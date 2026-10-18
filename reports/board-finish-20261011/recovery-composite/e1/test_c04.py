"""Host controls only: no pcbnew, native runner launch, or source input mutations."""
import copy
import hashlib
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

import compose_c04 as c
import measure_c04 as m


class AccountingControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        paths = {'manifest': c.E1 / 'e1-final-r06-manifest.json',
                 'donor_receipt': c.E1 / 'e1-final-donor/receipt.json',
                 'jobs': c.E1 / 'e1-final-frozen/jobs.json',
                 'checkpoint': c.E1 / 'e1-final-frozen/checkpoint.json',
                 'routes': c.E1 / 'e1-final-frozen/routes.json',
                 'full_donor': c.E1 / 'e1-final-donor/r06-e1-ordinary-donor.kicad_pcb',
                 'subset_donor': c.E1 / 'e1-four-net-subset/r06-e1-four-net-donor.kicad_pcb',
                 'subset_receipt': c.E1 / 'e1-four-net-subset/receipt.json'}
        cls.data = {role: path.read_bytes() for role, path in paths.items()}

    def altered_checkpoint(self, change):
        data = self.data.copy()
        checkpoint = json.loads(data['checkpoint'])
        change(checkpoint)
        data['checkpoint'] = json.dumps(checkpoint).encode()
        routes = json.loads(data['routes'])
        routes['tracks'], routes['failures'] = checkpoint['tracks'], checkpoint['failures']
        data['routes'] = json.dumps(routes).encode()
        manifest = json.loads(data['manifest'])
        manifest['source_hashes']['checkpoint'] = c.base.sha(data['checkpoint'])
        data['manifest'] = json.dumps(manifest).encode()
        return data

    def test_selected_six_jobs_explicit_global_nine_visible(self):
        result = c.verify_accounting(self.data)
        self.assertEqual(result['checkpoint_processed_original_jobs'], 2147)
        self.assertEqual(result['explicit_original_outcomes'], 2138)
        self.assertEqual(len(result['unrepresented_original_jobs_withheld']), 9)
        groups = result['selected_whole_nets'].values()
        self.assertEqual(sum(len(group['source_jobs']) for group in groups), 6)
        self.assertEqual(sum(len(group['successes']) for group in groups), 5)
        self.assertEqual(sum(len(group['failures']) for group in groups), 1)
        self.assertTrue(result['selected_original_jobs_fully_accounted'])
        self.assertEqual(result['potential_new_joins'], 4)

    def test_selected_failed_job_cannot_disappear(self):
        job = json.loads(self.data['jobs'])[1678]
        data = self.altered_checkpoint(lambda cp: cp.update(failures=[failure for failure in cp['failures'] if failure['job'] != job]))
        with self.assertRaisesRegex(ValueError, 'unrepresented original job'):
            c.verify_accounting(data)

    def test_auxiliary_without_main_is_not_success(self):
        def change(cp):
            for item in cp['tracks']:
                if item.get('job_index') == 874:
                    item['kind'] = 'padstub'
        with self.assertRaisesRegex(ValueError, 'auxiliary item'):
            c.verify_accounting(self.altered_checkpoint(change))

    def test_zero_based_index_refused(self):
        def change(cp):
            next(item for item in cp['tracks'] if item.get('job_index') == 176)['job_index'] = 0
        with self.assertRaisesRegex(ValueError, 'indexed route provenance'):
            c.verify_accounting(self.altered_checkpoint(change))

    def test_selected_ground_pour_claim_refused(self):
        def change(cp):
            next(item for item in cp['tracks'] if item.get('job_index') == 874)['crosses_ground_pour'] = True
        with self.assertRaisesRegex(ValueError, 'ground-pour crossing'):
            c.verify_accounting(self.altered_checkpoint(change))

    def test_extra_failed_successful_job_refused(self):
        job = json.loads(self.data['jobs'])[175]
        def change(cp):
            cp['failures'].append({'job': job, 'reason': 'injected'})
        with self.assertRaisesRegex(ValueError, 'cannot be attributed'):
            c.verify_accounting(self.altered_checkpoint(change))

    def test_checkpoint_source_digest_required(self):
        data = self.data.copy()
        manifest = json.loads(data['manifest'])
        manifest['source_hashes']['checkpoint'] = '0' * 64
        data['manifest'] = json.dumps(manifest).encode()
        with self.assertRaisesRegex(ValueError, 'identities or completeness'):
            c.verify_accounting(data)

    def test_subset_native_uuid_ledger_required(self):
        accounting = c.verify_accounting(self.data)
        accounting['selected_whole_nets']['/motherboard_status/OBS34_K']['native_uuids'].pop()
        r06 = c.base.verify_file(json.loads(c.BASE_RECEIPT.read_text())['native_sources']['r06'])
        with self.assertRaisesRegex(ValueError, 'UUIDs differ'):
            c.exact_subset(r06, self.data, accounting)


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

    def test_actual_bytes_and_binary_receipt_pass(self):
        reads = m.ReadSet()
        m.verify_inputs(self.out, self.inputs, self.expected, reads)
        reads.verify()

    def test_json_equivalent_bytes_change_refused(self):
        path = self.out / 'inputs.json'
        path.write_bytes(path.read_bytes() + b'\n')
        with self.assertRaisesRegex(ValueError, 'bytes changed'):
            m.verify_inputs(self.out, self.inputs, self.expected, m.ReadSet())

    def test_in_memory_manifest_mismatch_refused(self):
        altered = copy.deepcopy(self.inputs)
        altered['before_sha256'] = 'different'
        with self.assertRaisesRegex(ValueError, 'disagrees with run inputs'):
            m.verify_inputs(self.out, altered, self.expected, m.ReadSet())

    def test_native_binary_change_refused(self):
        self.binaries['pcbnew_extension'].write_bytes(b'changed')
        with self.assertRaisesRegex(ValueError, 'binary identity changed'):
            m.verify_inputs(self.out, self.inputs, self.expected, m.ReadSet())


class ReconstructionControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = c.HERE / 'construction.json'
        cls.candidate = c.HERE / 'c04-four-net-e1-dfm.kicad_pcb'

    def test_authentic_exact_reconstruction(self):
        result = c.validate_construction(self.receipt, self.candidate)
        self.assertTrue(result['ok'])
        self.assertEqual(result['e1_items'], 201)

    def test_recipe_source_binding_missing_refused(self):
        receipt = json.loads(self.receipt.read_text())
        receipt['original_source_bindings'].pop(next(iter(receipt['original_source_bindings'])))
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'construction.json'
            path.write_text(json.dumps(receipt))
            with self.assertRaisesRegex(ValueError, 'Original E1 extraction identities differ'):
                c.validate_construction(path, self.candidate)

    def test_candidate_text_tamper_refused(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / 'board.kicad_pcb'
            path.write_bytes(self.candidate.read_bytes() + b'\n')
            with self.assertRaisesRegex(ValueError, 'candidate bytes differ'):
                c.validate_construction(self.receipt, path)


if __name__ == '__main__':
    unittest.main(verbosity=2)
