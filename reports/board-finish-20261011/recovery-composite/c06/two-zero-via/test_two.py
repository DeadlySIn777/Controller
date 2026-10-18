"""Host controls against actual saved sources; no native jobs."""
import copy,hashlib,json,tempfile,unittest
from pathlib import Path
import compose_two as C
import measure_two as M

class Controls(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.receipt=json.loads((C.HERE/'construction.json').read_bytes())
        cls.candidate=(C.HERE/'r07-two-zero-via.kicad_pcb').read_bytes()
        cls.audit=json.loads((C.HERE/'audit.json').read_bytes())

    def changed_audit(self,directory,mutator):
        receipt=copy.deepcopy(self.receipt);audit=copy.deepcopy(self.audit);mutator(audit)
        path=Path(directory)/'audit.json';raw=json.dumps(audit).encode();path.write_bytes(raw)
        receipt['audit_path']=str(path);receipt['source_files_sha256'][str(path)]=C.sha(raw)
        return receipt

    def test_exact_replay(self):
        result,added=C.reconstruct(self.receipt)
        self.assertEqual(result,self.candidate);self.assertEqual(len(added),7)

    def test_modified_candidate_refused(self):
        with tempfile.TemporaryDirectory(dir=C.HERE) as d:
            candidate=Path(d)/'candidate.kicad_pcb'
            candidate.write_bytes(self.candidate.replace(b'(width 0.2)',b'(width 0.3)',1))
            with self.assertRaisesRegex(ValueError,'reconstructionfailed'):
                C.validate_construction(C.HERE/'construction.json',candidate)

    def test_unapproved_third_net_refused_even_rehashed_audit(self):
        with tempfile.TemporaryDirectory(dir=C.HERE) as d:
            receipt=self.changed_audit(d,lambda a:a['rows'][0].update(net='/LOGIC_GND'))
            with self.assertRaisesRegex(ValueError,'Wrongnetset'):C.reconstruct(receipt)

    def test_via_smuggling_refused_even_rehashed_audit(self):
        with tempfile.TemporaryDirectory(dir=C.HERE) as d:
            receipt=self.changed_audit(d,lambda a:a['rows'][0].update(new_vias=[{'x':1,'y':2}]))
            with self.assertRaisesRegex(ValueError,'Unauditedvia'):C.reconstruct(receipt)

    def test_other_layer_refused_even_rehashed_audit(self):
        with tempfile.TemporaryDirectory(dir=C.HERE) as d:
            def edit(a):a['rows'][0]['segments'][0]['layer']='In1.Cu'
            receipt=self.changed_audit(d,edit)
            with self.assertRaisesRegex(ValueError,'Onlyordinary'):C.reconstruct(receipt)

    def test_unanchored_reference_refused_even_rehashed_audit(self):
        with tempfile.TemporaryDirectory(dir=C.HERE) as d:
            def edit(a):a['rows'][0]['reference_source_connected_both_planes']['In4.Cu']=False
            receipt=self.changed_audit(d,edit)
            with self.assertRaisesRegex(ValueError,'Uncoveredreference'):C.reconstruct(receipt)

    def test_real_baseline_losses_remain_fatal_after_two_synthetic_joins(self):
        # Synthetic after-fixture changes only the two proposed pad groups in
        # saved native r07; this is a guard control, never native evidence.
        p0=Path('Z:/pcb-runs/claude-finish/integrate/measure/r07-ripup-signals-1/partitions.json')
        p6=Path('Z:/pcb-runs/claude-finish/integrate/measure/r06-stitch-plane-pads-2/partitions.json')
        before=json.loads(p0.read_bytes());r06=json.loads(p6.read_bytes());after=copy.deepcopy(before)
        for row in self.audit['rows']:
            net=row['net'];groups=after['nets'][net];selected=[set(g) for g in row['physical_pad_groups']]
            indices=[i for i,g in enumerate(groups) if set(g) in selected]
            self.assertEqual(len(indices),2)
            after['nets'][net]=[g for i,g in enumerate(groups) if i not in indices]+[sorted(set(groups[indices[0]])|set(groups[indices[1]]))]
        after['pad_island_joins']-=2;after['api_unconnected_count']-=2
        live=M.compare(before,after);old=M.compare(r06,after)
        self.assertEqual((live['completed'],live['lost'],live['verdict']),(2,0,'PASS'))
        self.assertEqual(old['lost'],15);self.assertEqual(old['verdict'],'FAIL')
        self.assertEqual(M.combined_verdict(live,old,0),'FAIL')

    def test_inputs_digest_mutation_refused_before_binary_calls(self):
        with tempfile.TemporaryDirectory(dir=C.HERE) as d:
            out=Path(d);inputs={'native_binaries':{}};raw=json.dumps(inputs).encode()
            (out/'inputs.json').write_bytes(raw+b' ')
            with self.assertRaisesRegex(ValueError,'inputs.json bytes changed'):
                M.verify_inputs(out,inputs,hashlib.sha256(raw).hexdigest(),M.ReadSet())

if __name__=='__main__':unittest.main(verbosity=2)
