"""Host controls for source conservation and independent receipt rejection."""
import json
from pathlib import Path
import tempfile
import unittest

import compose_recovery as compose

HERE = Path(__file__).resolve().parent

def item(number, width=0.2, via=False, layers='F.Cu" "B.Cu', mode=''):
    uid = f'00000000-0000-0000-0000-{number:012d}'
    if via:
        text = f'\t(via{mode}\n\t\t(at 1 1)\n\t\t(size 0.6)\n\t\t(drill 0.3)\n\t\t(layers "{layers}")\n'
    else:
        text = f'\t(segment\n\t\t(start 1 1)\n\t\t(end 2 1)\n\t\t(width {width})\n\t\t(layer "F.Cu")\n'
    return (text + f'\t\t(net "TEST")\n\t\t(uuid "{uid}")\n\t)\n').encode()

def board(*items, setup='0'):
    return b'(kicad_pcb\n' + f'\t(setup\n\t\t(pad_to_mask_clearance {setup})\n\t)\n'.encode() + b''.join(items) + b')\n'

class PureAddControls(unittest.TestCase):
    def test_divergent_target_conserved_and_explicit(self):
        baseline = board(item(1), item(2))
        target = board(item(2), item(3))
        donor = board(item(1), item(2), item(4))
        result, receipt = compose.pure_add(target, baseline, donor)
        self.assertEqual(result, board(item(2), item(3), item(4)))
        self.assertEqual(len(receipt['diverged_old_copper']['missing']), 1)
        self.assertTrue(receipt['all_target_chunks_retained_exact'])

    def test_changed_target_copper_is_retained_and_recorded(self):
        result, receipt = compose.pure_add(board(item(1, .4)), board(item(1)), board(item(1), item(2)))
        self.assertEqual(result, board(item(1, .4), item(2)))
        self.assertEqual(len(receipt['diverged_old_copper']['changed']), 1)

    def test_donor_cannot_remove_or_change_baseline(self):
        for donor in (board(item(2)), board(item(1, .4), item(2))):
            with self.subTest(donor=donor), self.assertRaises(ValueError):
                compose.pure_add(board(item(1)), board(item(1)), donor)

    def test_physical_setup_difference_rejected(self):
        with self.assertRaises(ValueError):
            compose.pure_add(board(item(1), setup='1'), board(item(1)), board(item(1), item(2)))
        with self.assertRaises(ValueError):
            compose.pure_add(board(item(1)), board(item(1)), board(item(1), item(2), setup='1'))

    def test_uuid_collision_rejected(self):
        with self.assertRaises(ValueError):
            compose.pure_add(board(item(1), item(2)), board(item(1)), board(item(1), item(2)))

    def test_only_ordinary_through_via_additions(self):
        result, _ = compose.pure_add(board(item(1)), board(item(1)), board(item(1), item(2, via=True)))
        self.assertEqual(result, board(item(1), item(2, via=True)))
        for new in (item(2, via=True, mode=' micro'), item(2, via=True, layers='F.Cu" "In1.Cu')):
            with self.subTest(new=new), self.assertRaises(ValueError):
                compose.pure_add(board(item(1)), board(item(1)), board(item(1), new))

class AuthenticConstructionControls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt_path = HERE / 'construction-r1.json'
        if not cls.receipt_path.exists():
            cls.receipt_path = HERE / 'construction.json'
        cls.candidate = HERE / 'c03-recovery-in3-fag-dfm.kicad_pcb'
        if not cls.receipt_path.exists() or not cls.candidate.exists():
            raise RuntimeError('Real construction must exist before authentic host controls')
        cls.receipt = json.loads(cls.receipt_path.read_text())

    def validate_mutation(self, mutation):
        with tempfile.TemporaryDirectory(dir=HERE, prefix='control-') as folder:
            folder = Path(folder)
            self.assertEqual(folder.resolve().parent, HERE.resolve())
            receipt = json.loads(json.dumps(self.receipt))
            mutation(receipt)
            path = folder / 'receipt.json'
            path.write_text(json.dumps(receipt))
            with self.assertRaises(ValueError):
                compose.validate_construction(path, self.candidate)

    def test_authentic_reconstruction_read_only(self):
        before = compose.sha(self.candidate.read_bytes())
        result = compose.validate_construction(self.receipt_path, self.candidate)
        self.assertTrue(result['ok'])
        self.assertEqual(compose.sha(self.candidate.read_bytes()), before)

    def test_candidate_byte_tamper_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE, prefix='control-') as folder:
            folder = Path(folder)
            self.assertEqual(folder.resolve().parent, HERE.resolve())
            candidate = folder / 'candidate.kicad_pcb'
            candidate.write_bytes(self.candidate.read_bytes() + b'\n')
            with self.assertRaises(ValueError):
                compose.validate_construction(self.receipt_path, candidate)

    def test_frozen_source_hash_tamper_rejected(self):
        self.validate_mutation(lambda r: r['native_sources']['in3_donor'].update(sha256='0' * 64))

    def test_missing_original_source_binding_rejected(self):
        self.validate_mutation(lambda r: r['origins'].pop('fag_donor'))

    def test_missing_tool_binding_rejected(self):
        self.validate_mutation(lambda r: r['tools'].pop('dfm_contract_v2.py'))

    def test_incomplete_project_binding_rejected(self):
        self.validate_mutation(lambda r: r['project_bindings']['fag'].pop('sch.net'))

    def test_native_proof_hash_tamper_rejected(self):
        self.validate_mutation(lambda r: r['recovery_proof']['drc'].update(sha256='0' * 64))

    def test_recorded_recipe_tamper_rejected(self):
        self.validate_mutation(lambda r: r['stages']['in3'].update(all_target_chunks_retained_exact=False))

if __name__ == '__main__':
    unittest.main(verbosity=2)
