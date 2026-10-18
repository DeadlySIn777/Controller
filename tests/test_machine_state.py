"""Machine-state projection tests using explicitly disconnected setup fixtures."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from controller_config.machine_state import (DOMAINS, MAX_RECORDS, MachineStateError,
    build_machine_state, configuration_binding, example_machine_observation, machine_observation_schema)
from controller_config.service import canonical, digest
from controller_config.model import ConfigurationError
from controller_config.setup_service import SetupService, example_draft


class MachineStateTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        self.folder = Path(temporary.name)
        self.service = SetupService(self.folder / 'setup.json')
        self.service.initialize()
        draft = example_draft('sim-mill-3axis')
        draft['inputs'] = [{'resource': 'SIM.DI0', 'role': 'test switch',
                            'equipment_profile': 'sim-24v-switch-v1', 'voltage_v': 24}]
        draft['outputs'] = [{'resource': 'SIM.DO0', 'role': 'test lamp',
                             'equipment_profile': 'sim-smart-output-v1', 'voltage_v': 24, 'current_a': 0.1}]
        draft['encoders'] = [{'resource': 'SIM.ABZ0', 'role': 'test encoder',
                              'equipment_profile': 'sim-abz-5v-v1', 'counts_per_revolution': 4000}]
        self.service.save_draft(draft, 0)
        self.service.commit(self.service.preview(), 'machine-state-fixture')
        self.snapshot = self.service.status()

    def record(self, *, timestamp=1_000_000_000, sequence=1, source='test-sensor', changes=None):
        value = example_machine_observation(self.snapshot, timestamp_ns=timestamp, sequence=sequence)
        value['source'] = source
        value['data']['observations'] = [{'domain': 'motion', 'resource': 'SIM.M0', 'key': 'position',
            'value': 12.5, 'unit': 'mm', 'source': 'measured', 'valid': True, 'fresh': True,
            'age_ms': 10, 'max_age_ms': 100}]
        value['data']['observations'][0].update(changes or {})
        return value

    def lane(self, state, domain='motion', source='measured'):
        return state['domains'][domain]['facts'][0][source]

    def assert_no_facts(self, state):
        self.assertEqual(state['counts']['observed_domains'], 0)
        self.assertTrue(all(not d['facts'] for d in state['domains'].values()))

    def test_all_domains_unknown_without_observations_and_no_inferred_presence(self):
        state = build_machine_state(self.snapshot, [])
        self.assertEqual(tuple(state['domains']), DOMAINS)
        self.assertEqual(state['counts']['unknown_domains'], 8)
        self.assert_no_facts(state)
        self.assertEqual(state['declared_target']['motor_channels'], 12)
        self.assertEqual(state['declared_target']['abz_encoders'], 4)
        self.assertEqual(state['declared_target']['general_di'], 24)
        self.assertEqual(state['declared_target']['general_do'], 16)
        self.assertFalse(state['declared_target']['qualified'])
        self.assertEqual(set(state['service_topology']['commodity_modules'].values()), {'unknown'})
        self.assertEqual(state['service_topology']['soldered_regions']['fpga'], 'whole_motherboard_exchange')
        self.assertFalse(state['grants_authority'])
        self.assertEqual(state['machine_commands'], [])
        self.assertNotIn('health_score', json.dumps(state))

    def test_machine_definition_reuses_one_validated_configuration_wiring_and_calculations(self):
        state = build_machine_state(self.snapshot, [])
        definition = state['machine_definition']
        active = self.snapshot['active']
        self.assertEqual(definition['configuration'], active['draft'])
        self.assertEqual(definition['wiring'], active['wiring'])
        self.assertEqual(definition['calculations'], active['calculations'])
        self.assertEqual(definition['binding'], configuration_binding(self.snapshot))
        self.assertEqual(definition['definition_sha256'], digest({k: v for k, v in definition.items() if k != 'definition_sha256'}))
        self.assertFalse(definition['qualified'])

    def test_valid_measured_value_retains_producer_provenance_without_authority(self):
        record = self.record()
        state = build_machine_state(self.snapshot, [record], evaluation_timestamp_ns=1_020_000_000)
        measured = self.lane(state)
        self.assertEqual(measured['value'], 12.5)
        self.assertEqual(measured['evaluated_age_ms'], 30)
        self.assertEqual(measured['producer'], 'test-sensor')
        self.assertEqual(measured['raw_record_sha256'], digest(record))
        self.assertEqual(measured['raw_record_index'], 0)
        self.assertEqual(measured['raw_observation_index'], 0)
        self.assertEqual(state['counts']['observed_domains'], 1)
        self.assertFalse(state['physical_evidence'])

    def test_command_and_report_do_not_become_measured_values(self):
        record = example_machine_observation(self.snapshot)
        state = build_machine_state(self.snapshot, [record])
        self.assertEqual(state['domains']['motion']['status'], 'commanded_only')
        self.assertIsNone(self.lane(state))
        self.assertEqual(self.lane(state, source='commanded')['value'], 12.5)
        self.assertEqual(state['domains']['controller']['status'], 'reported_only')
        self.assertEqual(state['counts']['observed_domains'], 0)
        self.assertEqual(state['counts']['unknown_domains'], 8)
        self.assertEqual(sum(d['counts']['measured'] for d in state['domains'].values()), 0)

    def test_measured_commanded_reported_channels_remain_separate(self):
        record = self.record()
        for source, value in (('commanded', 99), ('reported', 40)):
            record['data']['observations'].append({**record['data']['observations'][0], 'source': source, 'value': value})
        state = build_machine_state(self.snapshot, [record])
        for source, value in (('measured', 12.5), ('commanded', 99), ('reported', 40)):
            self.assertEqual(self.lane(state, source=source)['value'], value)

    def test_freshness_exact_boundary_then_stale_and_producer_invalidity(self):
        record = self.record()
        at_limit = build_machine_state(self.snapshot, [record], evaluation_timestamp_ns=1_090_000_000)
        self.assertEqual(self.lane(at_limit)['status'], 'available')
        later = build_machine_state(self.snapshot, [record], evaluation_timestamp_ns=1_090_000_001)
        self.assertEqual(self.lane(later)['status'], 'unavailable')
        self.assertIsNone(self.lane(later)['value'])
        self.assertEqual(self.lane(later)['reason'], 'stale')
        for changes, reason in (({'valid': False, 'value': None}, 'invalid'), ({'fresh': False}, 'producer_marked_stale')):
            state = build_machine_state(self.snapshot, [self.record(changes=changes)])
            self.assertEqual(self.lane(state)['reason'], reason)
            self.assertEqual(state['domains']['motion']['status'], 'unknown')

    def test_latest_invalid_sample_does_not_fall_back_to_older_valid_fact(self):
        old = self.record()
        latest = self.record(timestamp=1_010_000_000, sequence=2, changes={'valid': False, 'value': None})
        state = build_machine_state(self.snapshot, [old, latest])
        self.assertIsNone(self.lane(state)['value'])
        self.assertEqual(self.lane(state)['raw_record_index'], 1)

    def test_default_time_is_frozen_supplied_timeline_and_future_record_is_rejected(self):
        record = self.record()
        state = build_machine_state(self.snapshot, [record])
        self.assertEqual(state['timeline']['evaluation_timestamp_ns'], record['timestamp_ns'])
        self.assertFalse(state['timeline']['live_freshness_claim'])
        self.assertEqual(self.lane(state)['evaluated_age_ms'], 10)
        earlier = build_machine_state(self.snapshot, [record], evaluation_timestamp_ns=0)
        self.assert_no_facts(earlier)
        self.assertEqual(earlier['rejected_records'][0]['code'], 'MACHINE_STATE_TIME')

    def test_every_binding_field_exact_type_value_and_no_extra_fields(self):
        mutations = [('store_id', 'foreign'), ('epoch', 'foreign'), ('revision', 0), ('revision', float(self.snapshot['revision'])),
                     ('generation', True), ('generation', 9), ('configuration_sha256', '0' * 64), ('extra', 'forbidden')]
        for key, value in mutations:
            record = self.record()
            record['data']['configuration_binding'][key] = value
            with self.subTest(key=key, value=value):
                state = build_machine_state(self.snapshot, [record])
                self.assert_no_facts(state)
                self.assertEqual(state['rejected_records'][0]['code'], 'MACHINE_STATE_BINDING')
        record = self.record()
        del record['data']['configuration_binding']['generation']
        self.assert_no_facts(build_machine_state(self.snapshot, [record]))

    def test_new_revision_invalidates_old_observations_even_if_active_configuration_unchanged(self):
        old = self.record()
        draft = deepcopy(self.snapshot['draft'])
        draft['machine_name'] += ' edited draft'
        self.service.save_draft(draft, self.snapshot['revision'])
        current = self.service.status()
        self.assertEqual(current['active'], self.snapshot['active'])
        state = build_machine_state(current, [old])
        self.assert_no_facts(state)
        self.assertEqual(state['rejected_records'][0]['code'], 'MACHINE_STATE_BINDING')

    def test_no_active_or_inconsistent_definition_never_accepts_facts(self):
        record = self.record()
        inactive = deepcopy(self.snapshot)
        inactive['active'] = None
        self.assertIsNone(configuration_binding(inactive))
        self.assert_no_facts(build_machine_state(inactive, [record]))
        variants = []
        for key in ('configuration_sha256', 'wiring', 'calculations'):
            snapshot = deepcopy(self.snapshot)
            snapshot['active'][key] = '0' * 64 if key == 'configuration_sha256' else []
            variants.append(snapshot)
        snapshot = deepcopy(self.snapshot)
        snapshot['active']['draft']['motors'][0]['microsteps'] = None
        variants.append(snapshot)
        for snapshot in variants:
            with self.subTest(active=snapshot['active']['configuration_sha256']):
                state = build_machine_state(snapshot, [record])
                self.assert_no_facts(state)
                self.assertIsNotNone(state['definition_error'])
                with self.assertRaises(ConfigurationError):
                    configuration_binding(snapshot)

    def test_unrecognized_legacy_faults_and_unbound_records_remain_information_only(self):
        legacy = self.record()
        legacy['kind'] = 'fault'
        legacy['data'] = {'temperature': 45, 'health': 'green', 'fault': 'authored fixture'}
        old_sample = self.record(sequence=2)
        old_sample['data'] = {'observations': [{'value': 99}]}
        state = build_machine_state(self.snapshot, [legacy, old_sample])
        self.assert_no_facts(state)
        self.assertEqual(state['counts']['unrecognized_records'], 2)

    def test_unknown_schema_extra_fields_bad_units_and_types_reject_complete_sample(self):
        for changes in ({'unit': 'in'}, {'unit': 'degC'}, {'value': True}, {'value': '12.5'}, {'valid': 1},
                        {'fresh': 'true'}, {'age_ms': -1}, {'max_age_ms': True}, {'source': 'derived'},
                        {'domain': 'health'}, {'extra': True}, {'resource': 'SIM.M11'}, {'key': 'arm'}):
            with self.subTest(changes=changes):
                state = build_machine_state(self.snapshot, [self.record(changes=changes)])
                self.assert_no_facts(state)
                self.assertEqual(state['counts']['rejected_records'], 1)
        for key, value in (('schema_version', True), ('extra', True)):
            record = self.record()
            record['data'][key] = value
            self.assert_no_facts(build_machine_state(self.snapshot, [record]))

    def test_configured_io_encoder_and_explicit_fixed_domain_types(self):
        examples = [('motion', 'SIM.ABZ0', 'count', 123, 'count'),
                    ('io', 'SIM.DI0', 'state', True, 'bool'), ('io', 'SIM.DO0', 'current', 0.1, 'A'),
                    ('spindle', 'SIM.SPINDLE', 'speed', 3000, 'rpm'),
                    ('safety', 'SIM.SAFETY', 'estop_active', True, 'bool'),
                    ('modules', 'SIM.COMPUTE', 'present', True, 'bool'),
                    ('temperatures', 'SIM.COMPUTE', 'temperature', 40, 'degC'),
                    ('network', 'SIM.NETWORK', 'rx_errors', 0, 'count')]
        record = self.record()
        base = record['data']['observations'][0]
        record['data']['observations'] = [{**base, 'domain': d, 'resource': r, 'key': k, 'value': v, 'unit': u} for d, r, k, v, u in examples]
        state = build_machine_state(self.snapshot, [record])
        self.assertEqual(state['counts']['accepted_records'], 1)
        self.assertEqual(state['counts']['observed_domains'], 7)
        self.assertFalse(state['physical_evidence'])
        # A supplied simulation presence fact never rewrites physical topology.
        self.assertEqual(state['service_topology']['commodity_modules']['compute'], 'unknown')

    def test_soldered_region_presence_and_commanded_sensor_values_are_not_valid_fields(self):
        for changes in ({'domain': 'modules', 'resource': 'SIM.FPGA', 'key': 'present', 'value': True, 'unit': 'bool'},
                        {'domain': 'temperatures', 'resource': 'SIM.COMPUTE', 'key': 'temperature', 'unit': 'degC', 'source': 'commanded'},
                        {'domain': 'io', 'resource': 'SIM.DI1', 'key': 'state', 'value': True, 'unit': 'bool'}):
            self.assert_no_facts(build_machine_state(self.snapshot, [self.record(changes=changes)]))

    def test_active_motor_units_are_exact_and_measurements_are_not_clamped_to_command_limits(self):
        draft = deepcopy(self.snapshot['draft'])
        draft['motors'][0]['unit'] = 'in'
        self.service.save_draft(draft, self.snapshot['revision'])
        self.service.commit(self.service.preview(), 'inch-definition')
        current = self.service.status()
        record = self.record(changes={'key': 'velocity', 'unit': 'in/s', 'value': 1000})
        record['data']['configuration_binding'] = configuration_binding(current)
        state = build_machine_state(current, [record])
        self.assertEqual(self.lane(state)['value'], 1000)
        self.assertGreater(self.lane(state)['value'], draft['motors'][0]['max_velocity_units_per_second'])
        self.assertFalse(state['grants_authority'])
        record['data']['observations'][0]['unit'] = 'mm/s'
        self.assert_no_facts(build_machine_state(current, [record]))

    def test_duplicate_field_rejects_record_and_envelope_retry_is_idempotent(self):
        record = self.record()
        state = build_machine_state(self.snapshot, [record, deepcopy(record)])
        self.assertEqual(state['counts']['accepted_records'], 1)
        self.assertEqual(state['counts']['duplicate_records'], 1)
        record['data']['observations'].append(deepcopy(record['data']['observations'][0]))
        state = build_machine_state(self.snapshot, [record])
        self.assert_no_facts(state)
        self.assertEqual(state['rejected_records'][0]['code'], 'MACHINE_STATE_DUPLICATE')

    def test_conflicting_source_sequence_rejects_both_and_same_time_producers_are_ambiguous(self):
        one, two = self.record(), self.record(changes={'value': 999})
        state = build_machine_state(self.snapshot, [one, two])
        self.assert_no_facts(state)
        self.assertEqual(state['counts']['rejected_records'], 2)
        two['source'] = 'other-producer'
        state = build_machine_state(self.snapshot, [one, two])
        self.assertEqual(self.lane(state)['reason'], 'conflicting_same_time_observations')
        self.assertIsNone(self.lane(state)['value'])

    def test_replayed_sequence_cannot_be_refreshed_with_a_newer_timestamp(self):
        newer_sequence = self.record(sequence=5, timestamp=1_000_000_000)
        replay = self.record(sequence=4, timestamp=1_010_000_000, changes={'value': 999})
        for rows in ([newer_sequence, replay], [replay, newer_sequence]):
            state = build_machine_state(self.snapshot, rows)
            self.assert_no_facts(state)
            self.assertEqual(state['counts']['rejected_records'], 2)
            self.assertEqual(state['source_consistency']['quarantined_sources'], ['test-sensor'])
            self.assertTrue(all(row['code'] == 'MACHINE_STATE_SEQUENCE' for row in state['rejected_records']))

    def test_conflicting_latest_source_identity_cannot_resurrect_older_fact(self):
        old = self.record(sequence=0, timestamp=990_000_000)
        latest = self.record(sequence=1)
        conflicting = self.record(sequence=1, changes={'value': 999})
        state = build_machine_state(self.snapshot, [old, latest, conflicting])
        self.assert_no_facts(state)
        self.assertEqual(state['counts']['rejected_records'], 3)

    def test_fresh_contradictory_producers_at_different_times_remain_unavailable(self):
        one = self.record(sequence=1)
        two = self.record(sequence=0, timestamp=1_020_000_000, changes={'value': 999})
        two['source'] = 'other-sensor'
        state = build_machine_state(self.snapshot, [one, two])
        fact = self.lane(state)
        self.assertEqual(fact['reason'], 'conflicting_fresh_producers')
        self.assertIsNone(fact['value'])
        self.assertEqual(fact['conflicting_record_count'], 2)
        self.assertEqual(set(fact['conflicting_record_indexes']), {0, 1})

    def test_sequence_valid_same_time_updates_from_one_producer_are_not_conflicts(self):
        old = self.record(sequence=1)
        newer = self.record(sequence=2, changes={'value': 999})
        state = build_machine_state(self.snapshot, [newer, old])
        self.assertEqual(self.lane(state)['value'], 999)
        self.assertIsNone(self.lane(state)['reason'])
        self.assertEqual(self.lane(state)['sequence'], 2)

    def test_agreeing_fresh_producers_with_different_age_metadata_are_not_conflicts(self):
        one = self.record(sequence=1)
        two = self.record(sequence=0, changes={'age_ms': 20, 'max_age_ms': 200})
        two['source'] = 'other-sensor'
        state = build_machine_state(self.snapshot, [one, two])
        self.assertEqual(self.lane(state)['value'], 12.5)
        self.assertIsNone(self.lane(state)['reason'])
        self.assertEqual(self.lane(state)['producer_count'], 2)

    def test_expired_disagreement_does_not_override_a_fresh_producer(self):
        old = self.record(sequence=1, timestamp=0, changes={'value': 999})
        current = self.record(sequence=0)
        current['source'] = 'current-sensor'
        state = build_machine_state(self.snapshot, [old, current])
        self.assertEqual(self.lane(state)['value'], 12.5)
        self.assertIsNone(self.lane(state)['reason'])

    def test_malformed_current_bound_sample_cannot_resurrect_older_valid_rows(self):
        old = self.record(sequence=1)
        malformed = self.record(sequence=2, timestamp=1_010_000_000, changes={'unit': 'in'})
        state = build_machine_state(self.snapshot, [old, malformed])
        self.assert_no_facts(state)
        self.assertEqual(state['counts']['rejected_records'], 2)
        self.assertEqual(state['source_consistency']['quarantined_source_count'], 1)
        malformed = self.record(sequence=2, timestamp=1_010_000_000)
        malformed['data']['observations'].append(deepcopy(malformed['data']['observations'][0]))
        self.assert_no_facts(build_machine_state(self.snapshot, [old, malformed]))

    def test_quarantined_producer_does_not_remove_independent_valid_facts(self):
        one, conflicting = self.record(), self.record(changes={'value': 999})
        independent = self.record(sequence=0)
        independent['source'] = 'independent-sensor'
        state = build_machine_state(self.snapshot, [one, conflicting, independent])
        self.assertEqual(self.lane(state)['value'], 12.5)
        self.assertEqual(state['counts']['accepted_records'], 1)
        self.assertEqual(state['counts']['rejected_records'], 2)

    def test_pure_projection_keeps_inputs_raw_provenance_and_setup_files_unchanged(self):
        record = self.record()
        before_snapshot, before_record = deepcopy(self.snapshot), deepcopy(record)
        before_file = (self.folder / 'setup.json').read_bytes()
        with patch('builtins.open', side_effect=AssertionError('projection must not open files')):
            state = build_machine_state(self.snapshot, [record])
        self.assertEqual(self.snapshot, before_snapshot)
        self.assertEqual(record, before_record)
        self.assertEqual((self.folder / 'setup.json').read_bytes(), before_file)
        self.assertEqual(state['provenance']['input_envelopes_sha256'], digest([record]))
        self.assertFalse(state['provenance']['raw_records_embedded'])
        state['machine_definition']['configuration']['machine_name'] = 'output mutation'
        self.assertEqual(self.snapshot, before_snapshot)

    def test_diagnostic_detail_bounds_keep_counts_without_duplicating_raw_report(self):
        records = []
        for index in range(1000):
            record = self.record(sequence=index, timestamp=index)
            record['kind'] = 'event'
            record['data'] = {'fixture': 'x' * 1000}
            records.append(record)
        state = build_machine_state(self.snapshot, records)
        self.assertEqual(state['counts']['unrecognized_records'], 1000)
        self.assertEqual(len(state['unrecognized_records']), 64)
        self.assertTrue(state['record_details_truncated'])
        self.assertLess(len(canonical(state)), 100000)
        self.assertEqual(state['provenance']['input_record_count'], 1000)

    def test_structural_input_and_timeline_bounds_reject_without_coercion(self):
        for records in ({}, [None] * (MAX_RECORDS + 1), [{'x': float('nan')}], [{'x': 10**1000}], [{'x': 'y' * 20000}]):
            with self.assertRaises(MachineStateError):
                build_machine_state(self.snapshot, records)
        for timestamp in (True, -1, 1.5, 2**63):
            with self.assertRaises(MachineStateError):
                build_machine_state(self.snapshot, [], evaluation_timestamp_ns=timestamp)
        record = self.record()
        record['simulation_only'] = False
        self.assert_no_facts(build_machine_state(self.snapshot, [record]))

    def test_schema_and_example_are_serializable_and_demo_has_no_measured_observations(self):
        schema = machine_observation_schema()
        json.dumps(schema, allow_nan=False)
        example = example_machine_observation(self.snapshot, timestamp_ns=1, sequence=2)
        self.assertEqual(example['data']['configuration_binding'], configuration_binding(self.snapshot))
        self.assertTrue(all(o['source'] != 'measured' for o in example['data']['observations']))
        self.assertFalse(schema['data_schema']['additionalProperties'])


if __name__ == '__main__':
    unittest.main()
