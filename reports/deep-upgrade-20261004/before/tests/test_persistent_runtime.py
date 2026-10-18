"""Persistent policy/filesystem fault tests; adapter is an explicit host double."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
import io
import json

from controller_config.model import ConfigurationError
from controller_config.persistent_runtime import PersistentRuntimeService, _sealed, _write
from controller_config.service import read_json
from controller_config.runtime import RuntimeConfigurationService, compiled_guard_error
from test_runtime_configuration import Adapter, PRE_MARGIN_CAPABILITIES


# Verbatim content of the archived pre-margin evidence
# cnc1/evidence/persistent/final-authority.json and final-witness.json, written
# by the LinuxCNC actual-RTL persistent run before the pulse-rate margin
# (review of R2-15). Kept inline so the check survives regeneration of that
# evidence; the seals below are the original sha256 values.
PRE_MARGIN_AUTHORITY = {
    "committed": {"capabilities": PRE_MARGIN_CAPABILITIES, "generation": 2,
                  "machine_id": "29ec6d59-6e25-4986-95a2-92cc10cfdc1d",
                  "profile_sha256": "fefe247b45c5c4a6ade69970a64b765fd89e7d0146a3f73607cf690b70d5f626",
                  "scales": [300.0, 200.0, 200.0, 200.0, 200.0, 200.0], "schema": "cnc1-persistent-scales/1",
                  "sha256": "3ae9fef3186240d3efcc4d8ead98d9090308ea24d1ec05d2220bd5b5e8848acb"},
    "pending": None, "schema": "cnc1-scale-journal/1",
    "sha256": "a623106e6325ad054c7a1a7ca0e90324d41e536de3fede1d0a9f79a1b318595d"}
PRE_MARGIN_WITNESS = {
    "generation": 2, "machine_id": "29ec6d59-6e25-4986-95a2-92cc10cfdc1d",
    "profile_sha256": "fefe247b45c5c4a6ade69970a64b765fd89e7d0146a3f73607cf690b70d5f626",
    "record_sha256": "3ae9fef3186240d3efcc4d8ead98d9090308ea24d1ec05d2220bd5b5e8848acb",
    "schema": "cnc1-generation-witness/1",
    "sha256": "a9dd6ddde778abebfc37485aab60a9ab63d36445fb7e0f67909c4f0e67ee06f2"}


class PersistentAdapter(Adapter):
    """Host double of the compiled persistent gate (cnc1/src/cnc1.c).

    Like cnc1_configure op 4 and the HAL load path, it records the stage
    revision whenever the gate is staged; like cnc1_persistence_commit it refuses
    op 5 with result code 5 unless a stopped op-2 scale commit advanced the
    revision since that stage. The scale values and hash are not compared here,
    exactly as in the driver (record equality is service-side).
    """
    def __init__(self):
        super().__init__()
        self.value.update(persistence_required=True, persistence_pending=True,
                          persistence_generation=0, persistence_hash='0'*64,
                          config_locked=True, machine_id='29ec6d59-6e25-4986-95a2-92cc10cfdc1d',
                          profile_sha256='a'*64)
        # hal_cnc1.c stages the gate at load when persistence is required.
        self.stage_revision = self.value['revision']
        self.refused = []

    def transaction(self, op, state, scales=None, persistent=None, *, deadline=None):
        if op == 4:
            self.operations.append(op)
            self.value.update(config_locked=True, persistence_pending=True)
            self.stage_revision = self.value['revision']
        elif op == 5:
            if not self.value['revision'] > self.stage_revision:
                self.refused.append(op)
                raise compiled_guard_error(5, 5)
            self.operations.append(op)
            self.value.update(persistence_pending=False, persistence_generation=persistent['generation'], persistence_hash=persistent['sha256'])
        elif op == 3 and self.value['persistence_pending']:
            self.refused.append(op)
            raise compiled_guard_error(3, 5)
        else:
            super().transaction(op, state, scales, deadline=deadline)


class Interrupted(Exception):
    pass


class PersistentRuntimeTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.adapter = PersistentAdapter()
        self.now = 1_000_000_000
        self.service = PersistentRuntimeService(self.adapter,self.temp.name,clock=lambda:self.now)

    def reject(self, code, function, *args):
        with self.assertRaises(ConfigurationError) as caught:
            function(*args)
        self.assertEqual(caught.exception.code,code)

    def initialize(self):
        return self.service.initialize([250,200,200,200,200,200])

    def restart(self):
        self.adapter = PersistentAdapter()
        self.adapter.value['instance'][2] += 1
        self.service = PersistentRuntimeService(self.adapter,self.temp.name,clock=lambda:self.now)

    def test_new_machine_init_is_explicit_and_unhomed(self):
        self.reject('PERSISTENCE_MISSING',self.service.status)
        result = self.initialize()
        self.assertEqual(result['generation'],1)
        self.assertEqual(result['runtime']['scales'][0],250)
        self.assertFalse(any(result['runtime']['homed']))
        self.assertFalse(result['runtime']['enabled'])
        self.assertEqual(self.adapter.operations,[4,2,5,3])

    def test_separate_instance_reconciles_saved_scale(self):
        self.initialize(); self.restart()
        self.assertTrue(self.adapter.value['config_locked'])
        self.assertEqual(self.adapter.value['scales'][0],200)
        result=self.service.reconcile()
        self.assertEqual(result['runtime']['scales'][0],250)
        self.assertFalse(result['runtime']['enabled'])

    def test_init_cannot_overwrite(self):
        self.initialize(); self.restart()
        self.reject('PERSISTENCE_EXISTS',self.initialize)

    def test_public_volatile_apply_and_recovery_cannot_bypass(self):
        self.reject('PERSISTENT_AUTHORITY_REQUIRED',RuntimeConfigurationService(self.adapter).recover_inhibit)
        self.initialize()
        core=RuntimeConfigurationService(self.adapter,clock=lambda:self.now)
        plan=core.preview([300,200,200,200,200,200])
        self.reject('PERSISTENT_AUTHORITY_REQUIRED',core.apply,plan)

    def test_durable_change_and_reversal_advance_generation(self):
        self.initialize()
        self.service.apply(self.service.preview([300,200,200,200,200,200]))
        result=self.service.apply(self.service.preview([250,200,200,200,200,200]))
        self.assertEqual(result['generation'],3)
        self.assertEqual(result['runtime']['scales'][0],250)

    def test_init_interruption_each_phase_reconciles(self):
        for phase in ('journal_durable','witness_durable','runtime_activated','committed_durable','gate_committed','released'):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                adapter=PersistentAdapter()
                def checkpoint(current):
                    if current==phase: raise Interrupted(phase)
                service=PersistentRuntimeService(adapter,directory,checkpoint=checkpoint)
                with self.assertRaises(Interrupted): service.initialize([250,200,200,200,200,200])
                if phase!='released': self.assertTrue(adapter.value['config_locked'])
                restarted=PersistentRuntimeService(PersistentAdapter(),directory)
                self.assertEqual(restarted.recover()['runtime']['scales'][0],250)

    def test_apply_interruption_each_phase_reconciles(self):
        for phase in ('journal_durable','witness_durable','runtime_activated','committed_durable','gate_committed','released'):
            with self.subTest(phase=phase), tempfile.TemporaryDirectory() as directory:
                adapter=PersistentAdapter(); service=PersistentRuntimeService(adapter,directory)
                service.initialize([200]*6)
                plan=service.preview([250,200,200,200,200,200])
                def checkpoint(current):
                    if current==phase: raise Interrupted(phase)
                service.checkpoint=checkpoint
                with self.assertRaises(Interrupted): service.apply(plan)
                restarted=PersistentRuntimeService(PersistentAdapter(),directory)
                result=restarted.recover()
                self.assertEqual(result['runtime']['scales'][0],250)
                self.assertEqual(result['generation'],2)

    def test_interrupted_same_instance_recovers_after_gate_ack(self):
        self.initialize()
        def checkpoint(phase):
            if phase=='gate_committed': raise Interrupted()
        self.service.checkpoint=checkpoint
        with self.assertRaises(Interrupted):self.service.apply(self.service.preview([300,200,200,200,200,200]))
        self.assertTrue(self.adapter.value['config_locked'])
        self.service.checkpoint=lambda phase:None
        self.assertEqual(self.service.recover()['runtime']['scales'][0],300)

    def test_corrupt_journal_remains_inhibited(self):
        self.initialize(); self.restart()
        self.service.journal.write_text('{broken')
        self.reject('INVALID_JSON',self.service.reconcile)
        self.assertTrue(self.adapter.value['config_locked'])

    def test_valid_older_authority_conflicts_with_witness(self):
        self.initialize(); old=self.service.journal.read_bytes()
        self.service.apply(self.service.preview([300,200,200,200,200,200]))
        self.service.journal.write_bytes(old); self.restart()
        self.reject('PERSISTENCE_CONFLICT',self.service.reconcile)

    def test_same_generation_different_record_hash_conflicts(self):
        self.initialize(); self.restart()
        journal=read_json(self.service.journal); record=journal['committed']; record.pop('sha256');record['scales'][0]=300
        journal.pop('sha256');journal['committed']=_sealed(record);_write(self.service.journal,_sealed(journal))
        self.reject('PERSISTENCE_CONFLICT',self.service.reconcile)

    def test_foreign_machine_profile_caps_refused(self):
        self.initialize()
        original=self.service.journal.read_bytes()
        for key,value in (('machine_id','393e2a66-b026-4543-943e-8bff02e70fa1'),('profile_sha256','b'*64),('capabilities',{})):
            with self.subTest(key=key):
                self.service.journal.write_bytes(original); self.restart()
                journal=read_json(self.service.journal); record=journal['committed'];record.pop('sha256');record[key]=value
                journal.pop('sha256');journal['committed']=_sealed(record);_write(self.service.journal,_sealed(journal))
                self.reject('PERSISTENCE_IDENTITY',self.service.reconcile)

    def test_pulse_rate_margin_guards_init_and_saved_authority(self):
        # 19500 steps/mm x 10 mm/s passed the former ceiling-only check but
        # exceeds the 193312.5 steps/s limit that keeps the driver's margin.
        self.reject('PULSE_RATE_LIMIT',self.service.initialize,[19500,200,200,200,200,200])
        self.assertFalse(self.service.journal.exists())
        self.assertEqual(self.adapter.operations,[])
        self.service.initialize([19331.25,200,200,200,200,200])
        self.restart()
        journal=read_json(self.service.journal); record=journal['committed'];record.pop('sha256');record['scales'][0]=19500
        journal.pop('sha256');journal['committed']=_sealed(record);_write(self.service.journal,_sealed(journal))
        self.reject('PULSE_RATE_LIMIT',self.service.reconcile)
        self.assertTrue(self.adapter.value['config_locked'])
        self.assertEqual(self.adapter.value['scales'][0],200)

    def test_authority_saved_before_pulse_margin_still_activates(self):
        # Adding the servo period for the pulse-rate margin must not change the
        # persisted capabilities identity: a record written by the pre-margin
        # adapter is reloaded, validated and activated unchanged.
        committed = PRE_MARGIN_AUTHORITY['committed']
        self.assertEqual(_sealed({k: v for k, v in committed.items() if k != 'sha256'}), committed)
        self.assertEqual(_sealed({k: v for k, v in PRE_MARGIN_AUTHORITY.items() if k != 'sha256'}), PRE_MARGIN_AUTHORITY)
        self.assertEqual(_sealed({k: v for k, v in PRE_MARGIN_WITNESS.items() if k != 'sha256'}), PRE_MARGIN_WITNESS)
        _write(self.service.journal, deepcopy(PRE_MARGIN_AUTHORITY))
        _write(self.service.witness, deepcopy(PRE_MARGIN_WITNESS))
        self.adapter.value.update(capabilities=deepcopy(PRE_MARGIN_CAPABILITIES), servo_period_ns=1_000_000,
                                  machine_id=committed['machine_id'], profile_sha256=committed['profile_sha256'])
        state = self.adapter.snapshot()
        self.assertEqual({k: v for k, v in committed.items() if k != 'sha256'},
                         PersistentRuntimeService._validate_record(deepcopy(committed), state))
        journal_before = self.service.journal.read_bytes()
        self.service.reconcile()
        self.assertEqual(self.adapter.value['scales'], committed['scales'])
        self.assertEqual(self.adapter.value['persistence_generation'], 2)
        self.assertEqual(self.adapter.value['persistence_hash'], committed['sha256'])
        self.assertFalse(self.adapter.value['config_locked'])
        self.assertEqual(read_json(self.service.journal)['committed'], committed)
        self.assertEqual(journal_before, self.service.journal.read_bytes())
        # The period is still enforced from the snapshot, not from the record.
        self.adapter.value['servo_period_ns'] = None
        self.reject('CAPABILITIES_UNAVAILABLE', PersistentRuntimeService._validate_record, deepcopy(committed), self.adapter.snapshot())

    def refuse_ack(self, persistent):
        with self.assertRaises(ConfigurationError) as caught:
            self.adapter.transaction(5, self.adapter.snapshot(), persistent=persistent)
        self.assertEqual('COMPILED_GUARD_REJECTED', caught.exception.code)
        # Same refusal text/code as LinuxCNCRTLAdapter; persistent_integration.py
        # checks this suffix against the compiled driver.
        self.assertTrue(str(caught.exception).endswith('code 5'), str(caught.exception))
        self.assertTrue(self.adapter.value['persistence_pending'])
        self.assertTrue(self.adapter.value['config_locked'])
        self.assertEqual(0, self.adapter.value['persistence_generation'])
        self.reject('COMPILED_GUARD_REJECTED', self.adapter.transaction, 3, self.adapter.snapshot())
        self.assertTrue(self.adapter.value['config_locked'])

    def test_double_refuses_acknowledgement_without_commit_since_stage(self):
        arbitrary = {'generation': 1, 'sha256': '0' * 63 + '1'}
        # Staged at load: no op 2 has happened yet.
        self.refuse_ack(arbitrary)
        # Explicit op 4 then op 5, still without op 2.
        self.adapter.transaction(4, self.adapter.snapshot())
        self.assertEqual(0, self.adapter.stage_revision)
        self.refuse_ack(arbitrary)
        self.assertEqual([4], self.adapter.operations)
        self.assertEqual([5, 3, 5, 3], self.adapter.refused)
        # Compiled limit case: an explicit op 2 of the unchanged default scales
        # followed by op 5 with an arbitrary hash is accepted; the driver checks
        # only that a commit followed the stage, not the values.
        self.adapter.transaction(2, self.adapter.snapshot(), [200.] * 6)
        self.adapter.transaction(5, self.adapter.snapshot(), persistent=arbitrary)
        self.assertFalse(self.adapter.value['persistence_pending'])
        self.assertEqual(arbitrary['sha256'], self.adapter.value['persistence_hash'])
        # A new stage records the new revision and needs another commit.
        self.adapter.transaction(4, self.adapter.snapshot())
        self.assertEqual(1, self.adapter.stage_revision)
        with self.assertRaises(ConfigurationError) as caught:
            self.adapter.transaction(5, self.adapter.snapshot(), persistent={'generation': 2, 'sha256': 'b' * 64})
        self.assertTrue(str(caught.exception).endswith('code 5'))
        self.assertTrue(self.adapter.value['persistence_pending'])
        self.adapter.transaction(2, self.adapter.snapshot(), [200.] * 6)
        self.adapter.transaction(5, self.adapter.snapshot(), persistent={'generation': 2, 'sha256': 'b' * 64})
        self.adapter.transaction(3, self.adapter.snapshot())
        self.assertFalse(self.adapter.value['config_locked'])

    def observe_attempts(self, adapter):
        attempts = []
        original = adapter.transaction
        def observed(op, state, scales=None, persistent=None, *, deadline=None):
            attempts.append(op)
            return original(op, state, scales, persistent, deadline=deadline)
        adapter.transaction = observed
        return attempts

    def assert_ack_follows_commit(self, attempts):
        staged_commit = True  # nothing staged yet in this observation
        for op in attempts:
            if op == 4:
                staged_commit = False
            elif op == 2:
                staged_commit = True
            elif op == 5:
                self.assertTrue(staged_commit, attempts)

    def test_service_never_attempts_acknowledgement_without_scale_commit(self):
        # Normal init, change, restart/reconcile and interrupted recovery paths:
        # every op 5 the service attempts follows an op 2 after the latest op 4,
        # and the compiled-rule double never has to refuse one.
        attempts = self.observe_attempts(self.adapter)
        self.initialize()
        self.service.apply(self.service.preview([300,200,200,200,200,200]))
        self.restart()
        restart_attempts = self.observe_attempts(self.adapter)
        self.service.reconcile()
        for phase in ('journal_durable','witness_durable','runtime_activated','committed_durable','gate_committed'):
            with self.subTest(phase=phase):
                def checkpoint(current, phase=phase):
                    if current == phase: raise Interrupted(phase)
                self.service.checkpoint = checkpoint
                with self.assertRaises(Interrupted):
                    self.service.apply(self.service.preview([250 if self.adapter.value['scales'][0] != 250 else 300,200,200,200,200,200]))
                self.service.checkpoint = lambda current: None
                self.service.recover()
        for sequence in (attempts, restart_attempts):
            self.assertIn(5, sequence)
            self.assert_ack_follows_commit(sequence)
        self.assertNotIn(5, self.adapter.refused)

    def test_failed_scale_commit_never_reaches_acknowledgement(self):
        # op 2 refused by the compiled guard, or op 2 not observed as a new
        # revision (COMMIT_UNCERTAIN): the service stops before op 5 and the
        # persistent-pending inhibit stays held.
        for failure in ('guard', 'uncertain'):
            with self.subTest(failure=failure), tempfile.TemporaryDirectory() as directory:
                adapter = PersistentAdapter()
                base = PersistentAdapter.transaction
                def failing(op, state, scales=None, persistent=None, *, deadline=None, adapter=adapter, failure=failure):
                    if op == 2:
                        if failure == 'guard':
                            raise compiled_guard_error(2, 5)
                        return None  # acknowledged but revision/scales unchanged
                    return base(adapter, op, state, scales, persistent, deadline=deadline)
                adapter.transaction = failing
                attempts = self.observe_attempts(adapter)
                service = PersistentRuntimeService(adapter, directory)
                self.assertRaises(ConfigurationError, service.initialize, [250,200,200,200,200,200])
                self.assertEqual([4, 2], attempts)
                self.assertTrue(adapter.value['persistence_pending'])
                self.assertTrue(adapter.value['config_locked'])
                self.assertEqual(0, adapter.value['persistence_generation'])

    def test_servo_period_bound_guards_saved_authority(self):
        # A discovered watchdog too short for the profile servo period refuses
        # the saved authority before any compiled transaction (driver would
        # latch CNC1_CONFIG); the inhibit stays held.
        self.initialize(); self.restart()
        self.adapter.value['watchdog_ticks'] = 20_000
        self.reject('SERVO_PERIOD_LIMIT', self.service.reconcile)
        self.assertEqual([], self.adapter.operations)
        self.assertTrue(self.adapter.value['config_locked'])
        self.assertTrue(self.adapter.value['persistence_pending'])
        self.adapter.value['watchdog_ticks'] = None
        self.reject('CAPABILITIES_UNAVAILABLE', self.service.reconcile)
        self.assertEqual([], self.adapter.operations)

    def test_missing_witness_for_committed_authority_refused(self):
        self.initialize(); self.service.witness.unlink(); self.restart()
        self.reject('PERSISTENCE_WITNESS_MISSING',self.service.reconcile)

    def test_stale_preview_cannot_replace_new_generation(self):
        self.initialize(); plan=self.service.preview([300,200,200,200,200,200])
        self.service.apply(plan)
        self.reject('PERSISTENCE_STALE',self.service.apply,plan)

    def test_expiry_during_journal_write_retains_pending_inhibit(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        def checkpoint(phase):
            if phase=='journal_durable':self.now+=60_000_000_001
        self.service.checkpoint=checkpoint
        self.reject('RUNTIME_EXPIRED',self.service.apply,plan)
        self.assertTrue(self.adapter.value['persistence_pending'])
        self.assertEqual(self.adapter.value['scales'][0],250)

    def test_epoch_change_during_fsync_refused(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        def checkpoint(phase):
            if phase=='journal_durable':self.adapter.value['epoch']+=1
        self.service.checkpoint=checkpoint
        self.reject('RUNTIME_STALE',self.service.apply,plan)
        self.assertTrue(self.adapter.value['config_locked'])

    def test_machine_enable_during_fsync_refused(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        def checkpoint(phase):
            if phase=='committed_durable':self.adapter.value['enabled']=True
        self.service.checkpoint=checkpoint
        self.reject('RUNTIME_UNSAFE',self.service.apply,plan)
        self.assertTrue(self.adapter.value['persistence_pending'])

    def test_changed_durable_readback_cannot_release(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        def checkpoint(phase):
            if phase=='committed_durable':self.service.witness.write_text('{}')
        self.service.checkpoint=checkpoint
        self.reject('PERSISTENCE_FORMAT',self.service.apply,plan)
        self.assertTrue(self.adapter.value['config_locked'])

    def test_live_generation_prevents_rollback_even_both_files_old(self):
        self.initialize();journal=self.service.journal.read_bytes();witness=self.service.witness.read_bytes()
        self.service.apply(self.service.preview([300,200,200,200,200,200]))
        self.service.journal.write_bytes(journal);self.service.witness.write_bytes(witness)
        self.reject('PERSISTENCE_ROLLBACK',self.service.reconcile)

    def test_modified_caller_plan_cannot_change_commit(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        def checkpoint(phase):
            if phase=='journal_durable':plan['runtime']['after'][0]=350
        self.service.checkpoint=checkpoint
        self.assertEqual(self.service.apply(plan)['runtime']['scales'][0],300)

    def test_expiry_during_final_disk_read_keeps_inhibit(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        original=self.service._read
        def slow_read(state):
            result=original(state)
            if not state['persistence_pending'] and state['config_locked']:
                self.now+=60_000_000_001
            return result
        self.service._read=slow_read
        self.reject('RUNTIME_EXPIRED',self.service.apply,plan)
        self.assertTrue(self.adapter.value['config_locked'])

    def test_epoch_change_during_final_disk_read_keeps_inhibit(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        original=self.service._read
        def changed_read(state):
            result=original(state)
            if not state['persistence_pending'] and state['config_locked']:
                self.adapter.value['epoch']+=1
            return result
        self.service._read=changed_read
        self.reject('RUNTIME_STALE',self.service.apply,plan)
        self.assertTrue(self.adapter.value['config_locked'])

    def test_exponent_overflow_corrupt_record_returns_structured_error(self):
        self.initialize();self.restart()
        text=self.service.journal.read_text()
        self.service.journal.write_text(text.replace('250.0','1e1000',1))
        self.reject('PERSISTENCE_FORMAT',self.service.reconcile)
        self.assertTrue(self.adapter.value['config_locked'])

    def test_new_directory_chain_syncs_parent_names_before_file_commit(self):
        root=Path(self.temp.name); target=root/'new'/'nested'/'record.json';calls=[]
        with patch('controller_config.persistent_runtime._sync_directory',side_effect=lambda p:calls.append(Path(p))):
            _write(target,{'test':True})
        self.assertEqual(calls,[root,root/'new',root/'new',root/'new'/'nested',root/'new'/'nested'])

    def test_directory_fsync_failure_keeps_pending_inhibit(self):
        self.service=PersistentRuntimeService(self.adapter,Path(self.temp.name)/'new')
        with patch('controller_config.persistent_runtime._sync_directory',side_effect=OSError('injected fsync failure')):
            self.reject('PERSISTENCE_IO',self.initialize)
        self.assertTrue(self.adapter.value['config_locked'])
        self.assertTrue(self.adapter.value['persistence_pending'])

    def test_activation_and_release_receive_original_deadline(self):
        self.initialize();plan=self.service.preview([300,200,200,200,200,200])
        received=[];original=self.adapter.transaction
        def observed(op,state,scales=None,persistent=None,*,deadline=None):
            received.append((op,deadline))
            return original(op,state,scales,persistent,deadline=deadline)
        self.adapter.transaction=observed
        self.service.apply(plan)
        self.assertEqual(received,[(op,plan['runtime']['expires_monotonic_ns']) for op in (4,2,5,3)])

    def test_cli_versioned_success_and_structured_failures(self):
        from controller_config.persistent_runtime import main
        self.initialize()
        for error,code in ((None,None),(ConfigurationError('PERSISTENCE_MISSING','no store'),'PERSISTENCE_MISSING'),(OSError('unavailable directory'),'IO_ERROR')):
            with self.subTest(code=code),patch('controller_config.persistent_runtime.LinuxCNCRTLAdapter',return_value=self.adapter,side_effect=error),redirect_stdout(io.StringIO()) as output:
                result=main(['--directory',self.temp.name,'status'])
            value=json.loads(output.getvalue())
            self.assertEqual(value['schema_version'],1)
            self.assertEqual(result,2 if error else 0)
            self.assertEqual(value['ok'],not bool(error))
            if error:self.assertEqual(value['error']['code'],code)


if __name__=='__main__':unittest.main()
