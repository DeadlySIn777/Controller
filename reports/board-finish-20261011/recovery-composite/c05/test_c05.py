"""Host rejection controls against frozen c04/c05 bytes; no native calls."""
import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import compose_c05 as c
import measure_c05 as m


class RollbackControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = c.SOURCE.read_bytes()
        cls.previous = json.loads(c.SOURCE_RECEIPT.read_bytes())
        cls.r06_bytes = c.base.verify_file(cls.previous['base_bindings']['native_sources']['r06'])
        cls.recovery_bytes = c.base.verify_file(cls.previous['base_bindings']['native_sources']['recovery'])
        cls.inventories = {c.base.sha(data): c.base.inventory(data)
                           for data in [cls.source, cls.r06_bytes, cls.recovery_bytes]}
        cls.original_inventory = staticmethod(c.base.inventory)

    def setUp(self):
        # Parse the authentic native sources once. Altered bytes still use the real parser.
        def inventory(data):
            key = c.base.sha(data)
            return self.inventories[key] if key in self.inventories else self.original_inventory(data)
        self.binding = patch.object(c.base, 'inventory', inventory)
        self.binding.start()
        self.addCleanup(self.binding.stop)

    def changed(self):
        return copy.deepcopy(self.previous)

    def test_actual_complete_462_rollback_and_all_other_bytes_exact(self):
        result, changes = c.rollback(self.source, self.previous)
        self.assertEqual(result, (c.HERE / 'c05-fag-e1-rollback-dfm.kicad_pcb').read_bytes())
        before = self.inventories[c.base.sha(self.source)]
        after = self.original_inventory(result)
        owned = {item['uuid'] for item in changes['removed_complete_new_groups']}
        self.assertEqual(len(owned), 462)
        self.assertEqual(changes['removed_fag_items'], 261)
        self.assertEqual(changes['removed_e1_items'], 201)
        self.assertEqual(after[0], before[0])
        self.assertEqual(after[2], before[2])
        self.assertEqual(after[1], [chunk for chunk in before[1]
                                  if c.base.pcbtext.chunk_uuid(chunk) not in owned])
        self.assertEqual(after[4], {uid: chunk for uid, chunk in before[4].items()
                                   if uid not in owned})
        protected = set(self.inventories[c.base.sha(self.r06_bytes)][4]) | set(
            self.inventories[c.base.sha(self.recovery_bytes)][4])
        self.assertFalse(owned & protected)

    def test_incomplete_fag_group_refused(self):
        previous = self.changed()
        previous['base_bindings']['stages']['fag']['additions'].pop()
        with self.assertRaisesRegex(ValueError, 'ownership groups differ'):
            c.rollback(self.source, previous)

    def test_incomplete_e1_group_refused(self):
        previous = self.changed()
        previous['stages']['e1']['additions'].pop()
        with self.assertRaisesRegex(ValueError, 'ownership groups differ'):
            c.rollback(self.source, previous)

    def test_duplicate_owned_uuid_refused(self):
        previous = self.changed()
        additions = previous['base_bindings']['stages']['fag']['additions']
        additions[1] = copy.deepcopy(additions[0])
        with self.assertRaisesRegex(ValueError, 'ownership groups differ'):
            c.rollback(self.source, previous)

    def test_unapproved_e1_net_refused(self):
        previous = self.changed()
        previous['stages']['e1_native_subset_items'][0]['net'] = '/unapproved/net'
        with self.assertRaisesRegex(ValueError, 'four-net E1 ownership differs'):
            c.rollback(self.source, previous)

    def test_owned_geometry_digest_change_refused(self):
        previous = self.changed()
        previous['base_bindings']['stages']['fag']['additions'][0]['sha256'] = '0' * 64
        with self.assertRaisesRegex(ValueError, 'protected or changed copper'):
            c.rollback(self.source, previous)

    def test_retained_r06_copper_cannot_be_relabelled_donor_owned(self):
        self.inject_protected(self.inventories[c.base.sha(self.r06_bytes)][4])

    def test_retained_recovery_copper_cannot_be_relabelled_donor_owned(self):
        r06 = self.inventories[c.base.sha(self.r06_bytes)][4]
        recovery = self.inventories[c.base.sha(self.recovery_bytes)][4]
        self.inject_protected({uid: chunk for uid, chunk in recovery.items() if uid not in r06})

    def inject_protected(self, protected):
        actual = self.inventories[c.base.sha(self.source)][4]
        uid, chunk = next((uid, chunk) for uid, chunk in protected.items()
                          if uid in actual and c.base.pcbtext.chunk_kind(chunk) == 'segment')
        previous = self.changed()
        item = previous['base_bindings']['stages']['fag']['additions'][0]
        item['uuid'], item['sha256'] = uid, c.base.sha(chunk)
        with self.assertRaisesRegex(ValueError, 'protected or changed copper'):
            c.rollback(self.source, previous)

    def test_e1_actual_net_cannot_be_swapped_in_ledger(self):
        previous = self.changed()
        items = previous['stages']['e1_native_subset_items']
        first = items[0]
        second = next(item for item in items if item['net'] != first['net'])
        first['net'], second['net'] = second['net'], first['net']
        with self.assertRaisesRegex(ValueError, 'protected or changed copper'):
            c.rollback(self.source, previous)

    def test_altered_source_bytes_refused_before_rollback(self):
        with self.assertRaisesRegex(ValueError, 'source identity differs'):
            c.rollback(self.source + b'\n', self.previous)


class ReconstructionControls(unittest.TestCase):
    def setUp(self):
        self.receipt = c.HERE / 'construction.json'
        self.candidate = c.HERE / 'c05-fag-e1-rollback-dfm.kicad_pcb'

    def test_authentic_sealed_reconstruction(self):
        result = c.validate_construction(self.receipt, self.candidate)
        self.assertTrue(result['ok'])
        self.assertEqual(result['protected_copper_removed_or_changed'], 0)
        self.assertTrue(result['fresh_native_required'])

    def altered_receipt(self, change, message):
        receipt = json.loads(self.receipt.read_bytes())
        change(receipt)
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'construction.json'
            path.write_text(json.dumps(receipt), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, message):
                c.validate_construction(path, self.candidate)

    def test_constructor_digest_missing_refused(self):
        self.altered_receipt(lambda receipt: receipt['tools'].pop('compose_c05.py'),
                             'constructor identities differ')

    def test_c04_source_construction_digest_change_refused(self):
        self.altered_receipt(lambda receipt: receipt['source_construction'].update(sha256='0' * 64),
                             'source bindings differ')

    def test_candidate_bytes_change_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'board.kicad_pcb'
            path.write_bytes(self.candidate.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'candidate bytes differ'):
                c.validate_construction(self.receipt, path)


class RunManifestControls(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.out = Path(self.temp.name)
        self.binaries = {}
        for role in m.NATIVE_BINARIES:
            path = self.out / (role + '.test-binary')
            path.write_bytes(role.encode())
            self.binaries[role] = path
        self.binding = patch.object(m, 'NATIVE_BINARIES', self.binaries)
        self.binding.start()
        self.addCleanup(self.binding.stop)
        self.inputs = {'native_binaries': m.binary_identities(m.ReadSet()), 'before_sha256': 'baseline'}
        m.write(self.out / 'inputs.json', self.inputs)
        self.expected = m.digest((self.out / 'inputs.json').read_bytes())

    def test_actual_bytes_and_all_four_binary_receipt_pass(self):
        self.assertEqual(len(self.inputs['native_binaries']), 4)
        reads = m.ReadSet()
        m.verify_inputs(self.out, self.inputs, self.expected, reads)
        reads.verify()

    def test_json_equivalent_inputs_byte_change_refused(self):
        path = self.out / 'inputs.json'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'bytes changed'):
            m.verify_inputs(self.out, self.inputs, self.expected, m.ReadSet())

    def test_manifest_record_divergence_refused(self):
        altered = copy.deepcopy(self.inputs)
        altered['before_sha256'] = 'different'
        with self.assertRaisesRegex(ValueError, 'disagrees with run inputs'):
            m.verify_inputs(self.out, altered, self.expected, m.ReadSet())

    def test_each_native_binary_change_refused(self):
        for role, path in self.binaries.items():
            with self.subTest(binary_role=role):
                original = path.read_bytes()
                path.write_bytes(b'changed')
                with self.assertRaisesRegex(ValueError, 'binary identity changed'):
                    m.verify_inputs(self.out, self.inputs, self.expected, m.ReadSet())
                path.write_bytes(original)


if __name__ == '__main__':
    unittest.main(verbosity=2)
