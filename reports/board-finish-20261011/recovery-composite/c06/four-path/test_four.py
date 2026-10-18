"""Host rejection controls against actual frozen sources; no native jobs."""
import copy, hashlib, json, tempfile, unittest
from pathlib import Path
import compose_four as C
import measure_four as M


class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt = json.loads((C.HERE/'construction.json').read_bytes())
        cls.candidate = (C.HERE/'r07-four-path.kicad_pcb').read_bytes()
        cls.audit = json.loads((C.HERE/'audit.json').read_bytes())

    def changed_audit(self, directory, edit):
        receipt, audit = copy.deepcopy(self.receipt), copy.deepcopy(self.audit); edit(audit)
        path = Path(directory)/'audit.json'; raw = json.dumps(audit).encode(); path.write_bytes(raw)
        receipt['audit_path'] = str(path); receipt['source_files_sha256'][str(path)] = C.sha(raw)
        return receipt

    def test_exact_replay_and_frozen_two_retained(self):
        result, added = C.reconstruct(self.receipt)
        self.assertEqual(result, self.candidate); self.assertEqual(len(added), 18)
        old = C.T.inventory(C.TWO.R07.read_bytes()); after = C.T.inventory(result)
        two = C.T.inventory((C.TWO.HERE/'r07-two-zero-via.kicad_pcb').read_bytes())
        self.assertTrue(all(after[3].get(uid) == chunk for uid, chunk in old[3].items()))
        self.assertTrue(all(after[3].get(uid) == chunk for uid, chunk in two[3].items()))
        self.assertEqual(sum(item['kind'] == 'via' for item in added), 2)

    def test_retained_item_or_candidate_byte_edit_refused(self):
        with tempfile.TemporaryDirectory(dir=C.HERE) as d:
            path = Path(d)/'candidate.kicad_pcb'; path.write_bytes(self.candidate.replace(b'(width 0.2)', b'(width 0.3)', 1))
            with self.assertRaisesRegex(ValueError, 'reconstruction failed'):
                C.validate_construction(C.HERE/'construction.json', path)

    def test_unapproved_fifth_net_refused(self):
        with tempfile.TemporaryDirectory(dir=C.HERE) as d:
            receipt = self.changed_audit(d, lambda audit: audit['rows'][0].update(net='/LOGIC_GND'))
            with self.assertRaisesRegex(ValueError, 'net set'): C.reconstruct(receipt)

    def test_rehashed_path_geometry_edit_refused(self):
        with tempfile.TemporaryDirectory(dir=C.HERE) as d:
            def edit(audit): audit['rows'][2]['segments'][0]['points_mm'][1][0] += .1
            receipt = self.changed_audit(d, edit)
            with self.assertRaisesRegex(ValueError, 'frozen component audit'): C.reconstruct(receipt)

    def test_rehashed_via_size_edit_refused(self):
        with tempfile.TemporaryDirectory(dir=C.HERE) as d:
            def edit(audit): audit['rows'][3]['new_signal_vias'][0]['size_mm'] = .4
            receipt = self.changed_audit(d, edit)
            with self.assertRaisesRegex(ValueError, 'frozen component audit'): C.reconstruct(receipt)

    def test_rehashed_via_position_edit_refused(self):
        with tempfile.TemporaryDirectory(dir=C.HERE) as d:
            def edit(audit): audit['rows'][3]['new_signal_vias'][0]['point_mm'][0] += .1
            receipt = self.changed_audit(d, edit)
            with self.assertRaisesRegex(ValueError, 'frozen component audit'): C.reconstruct(receipt)

    def test_combined_reference_gap_refused(self):
        with tempfile.TemporaryDirectory(dir=C.HERE) as d:
            def edit(audit): audit['rows'][0]['reference_checks'][0]['source_connected_reference_both_planes']['In4.Cu'] = False
            receipt = self.changed_audit(d, edit)
            with self.assertRaisesRegex(ValueError, 'Uncovered source reference'): C.reconstruct(receipt)

    def test_return_source_disconnection_refused(self):
        with tempfile.TemporaryDirectory(dir=C.HERE) as d:
            def edit(audit): audit['rows'][3]['return_checks'][0]['source_connected_after_all_new_antipads']['In1.Cu'] = False
            receipt = self.changed_audit(d, edit)
            with self.assertRaisesRegex(ValueError, 'Unanchored existing return'): C.reconstruct(receipt)

    def test_source_input_hash_change_refused(self):
        receipt = copy.deepcopy(self.receipt)
        receipt['source_files_sha256'][str(C.TWO.R07.resolve())] = '0'*64
        with self.assertRaisesRegex(ValueError, 'Construction input changed'): C.reconstruct(receipt)

    def test_real_baseline_losses_remain_fatal_after_four_synthetic_joins(self):
        # A strict-guard control only: ignores possible refill changes, and
        # never substitutes for native candidate DRC or pad partitions.
        p7 = Path('Z:/pcb-runs/claude-finish/integrate/measure/r07-ripup-signals-1/partitions.json')
        p6 = Path('Z:/pcb-runs/claude-finish/integrate/measure/r06-stitch-plane-pads-2/partitions.json')
        before, r06 = json.loads(p7.read_bytes()), json.loads(p6.read_bytes()); after = copy.deepcopy(before)
        for row in self.audit['rows']:
            groups = after['nets'][row['net']]; selected = [set(group) for group in row['physical_pad_groups']]
            indices = [i for i, group in enumerate(groups) if set(group) in selected]
            self.assertEqual(len(indices), 2)
            after['nets'][row['net']] = [group for i, group in enumerate(groups) if i not in indices] + [sorted(set(groups[indices[0]]) | set(groups[indices[1]]))]
        after['pad_island_joins'] -= 4; after['api_unconnected_count'] -= 4
        live, old = M.compare(before, after), M.compare(r06, after)
        self.assertEqual((live['completed'], live['lost'], live['verdict']), (4, 0, 'PASS'))
        self.assertEqual(old['lost'], 14); self.assertEqual(old['verdict'], 'FAIL')
        self.assertEqual(M.combined_verdict(live, old, 0), 'FAIL')

    def test_live_losses_and_drc_remain_fatal(self):
        self.assertEqual(M.combined_verdict({'verdict': 'FAIL'}, {'verdict': 'PASS'}, 0), 'FAIL')
        self.assertEqual(M.combined_verdict({'verdict': 'PASS'}, {'verdict': 'PASS'}, 1), 'FAIL')

    def test_inputs_digest_mutation_refused_before_binary_calls(self):
        with tempfile.TemporaryDirectory(dir=C.HERE) as d:
            out = Path(d); inputs = {'native_binaries': {}}; raw = json.dumps(inputs).encode()
            (out/'inputs.json').write_bytes(raw+b' ')
            with self.assertRaisesRegex(ValueError, 'inputs.json bytes changed'):
                M.verify_inputs(out, inputs, hashlib.sha256(raw).hexdigest(), M.ReadSet())


if __name__ == '__main__': unittest.main(verbosity=2)
