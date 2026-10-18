"""Bounded zone-outline editing rejects electrical changes and stale reviews.

Run with KiCad Python. These use the actual native six-layer routing fixture;
they do not establish that the controller's final planes are connected.
"""
import copy,json,shutil,subprocess,sys,tempfile,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
try:
    import pcbnew
    from hardware_build_assembly import parse,dump,children,child
    from hardware_merge_bounded_pcb_delta import merge_reviewed_existing_zone_outlines,zone_definition,sha_text
except ModuleNotFoundError:pcbnew=None

ROOT=Path(__file__).resolve().parents[1]
FIXTURE=ROOT/'reports/motherboard-owned-bypass-routing-20261001/native-fixture-r08/top/fixture.kicad_pcb'

@unittest.skipUnless(pcbnew is not None,'Requires native KiCad Python')
class ReviewedZoneOutline(unittest.TestCase):
    def setUp(self):
        self.before=parse(FIXTURE.read_text());self.donor=copy.deepcopy(self.before);self.target=copy.deepcopy(self.before)
        self.old=children(self.before,'zone')[0];self.new=children(self.donor,'zone')[0]
        polygon=children(self.new,'polygon')[0]
        self.new.append(copy.deepcopy(polygon))
        points=child(self.new[-1],'pts')
        points[:]=parse('(pts (xy 18 13) (xy 19 13) (xy 19 14) (xy 18 14))')
        self.uid=child(self.old,'uuid')[1].strip('"')
        self.reviews=[dict(uuid=self.uid,before_definition_sha256=sha_text(zone_definition(self.old)),after_definition_sha256=sha_text(zone_definition(self.new)),electrical_outline_correction_reason='Fixture: exclude an actual reviewed foreign-domain envelope')]
    def run_merge(self):return merge_reviewed_existing_zone_outlines(self.before,self.donor,self.target,self.reviews)
    def refresh_review(self):self.reviews[0]['after_definition_sha256']=sha_text(zone_definition(self.new))
    def test_only_reviewed_outline_changes(self):
        original=copy.deepcopy(self.target);result=self.run_merge()
        self.assertEqual(len(result),1)
        original[original.index(children(original,'zone')[0])]=copy.deepcopy(self.new)
        self.assertEqual(dump(self.target),dump(original))
    def test_missing_review_rejected(self):
        self.reviews=[]
        with self.assertRaisesRegex(ValueError,'Unreviewed'):self.run_merge()
    def test_stale_review_rejected(self):
        self.reviews[0]['after_definition_sha256']='0'*64
        with self.assertRaisesRegex(ValueError,'definition differs'):self.run_merge()
    def test_net_change_rejected_even_with_fresh_hash(self):
        child(self.new,'net')[1]='999';self.refresh_review()
        with self.assertRaisesRegex(ValueError,'net/layers/clearance/pour rules'):self.run_merge()
    def test_layer_change_rejected_even_with_fresh_hash(self):
        layers=child(self.new,'layers') or child(self.new,'layer');layers[1]='"B.Cu"';self.refresh_review()
        with self.assertRaisesRegex(ValueError,'net/layers/clearance/pour rules'):self.run_merge()
    def test_clearance_change_rejected_even_with_fresh_hash(self):
        child(child(self.new,'connect_pads'),'clearance')[1]='0';self.refresh_review()
        with self.assertRaisesRegex(ValueError,'net/layers/clearance/pour rules'):self.run_merge()
    def test_deleted_plane_rejected(self):
        self.donor.remove(self.new)
        with self.assertRaisesRegex(ValueError,'deletes existing'):self.run_merge()
    def test_concurrent_outline_edit_rejected(self):
        children(self.target,'zone')[0].append(copy.deepcopy(self.new[-1]))
        with self.assertRaisesRegex(ValueError,'Concurrent'):self.run_merge()
    def test_duplicate_review_rejected(self):
        self.reviews.append(copy.deepcopy(self.reviews[0]))
        with self.assertRaisesRegex(ValueError,'Duplicate'):self.run_merge()
    def test_extra_review_rejected(self):
        self.reviews.append(dict(self.reviews[0],uuid='11111111-1111-1111-1111-111111111111'))
        with self.assertRaisesRegex(ValueError,'not the actual delta'):self.run_merge()
    def test_actual_native_merge_preserves_source_lands_copper_and_clusters(self):
        before=pcbnew.LoadBoard(str(FIXTURE));before.BuildConnectivity()
        def pad_clusters(board):
            conn=board.GetConnectivity()
            return {p.m_Uuid.AsString():tuple(sorted(i.m_Uuid.AsString() for i in conn.GetConnectedItems(p) if i.Type()==pcbnew.PCB_PAD_T)) for f in board.GetFootprints() for p in f.Pads() if p.GetNumber()}
        with tempfile.TemporaryDirectory(prefix='reviewed-plane-outline-') as folder:
            folder=Path(folder);donor=folder/'donor.kicad_pcb';donor.write_text(dump(self.donor)+'\n')
            scope=folder/'scope.json';scope.write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=[],reviewed_added_zone_UUIDs=[],reviewed_existing_zone_outline_deltas=self.reviews,reviewed_scope_reason='Native fixture existing-zone electrical exclusion review')))
            out=folder/'merged'
            run=subprocess.run([sys.executable,str(ROOT/'tools/hardware_merge_bounded_pcb_delta.py'),'--before',str(FIXTURE),'--donor',str(donor),'--target',str(FIXTURE),'--scope',str(scope),'--out',str(out)],capture_output=True,text=True)
            self.assertEqual(run.returncode,0,run.stdout+run.stderr)
            receipt=json.loads((out/'receipt.json').read_text());self.assertEqual(receipt['native_DRC_regular'],0)
            self.assertEqual(receipt['ignored_checks'],[]);self.assertEqual(len(receipt['reviewed_existing_zone_outline_deltas']),1)
            after=pcbnew.LoadBoard(str(out/'motherboard-bounded-merged-candidate.kicad_pcb'));after.BuildConnectivity()
            self.assertEqual(before.GetConnectivity().GetUnconnectedCount(False),after.GetConnectivity().GetUnconnectedCount(False))
            self.assertEqual(pad_clusters(before),pad_clusters(after))
            self.assertEqual(len(before.GetTracks()),len(after.GetTracks()))

if __name__=='__main__':unittest.main()
