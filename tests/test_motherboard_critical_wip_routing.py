"""Actual source-cluster preservation and complete native warning admission."""
from pathlib import Path
import copy,json,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
try:
 import pcbnew
 import hardware_route_critical_digital_wip_r03 as h
except ModuleNotFoundError:pcbnew=None
@unittest.skipUnless(pcbnew,'Actual KiCad native runtime required')
class CriticalWipGates(unittest.TestCase):
 def test_actual_joined_native_source_cluster_cannot_be_fragmented(self):
  with tempfile.TemporaryDirectory()as d:
   b=pcbnew.BOARD();net=pcbnew.NETINFO_ITEM(b,'/CRITICAL_SOURCE',1);b.Add(net)
   for ref,x in [('U1',10),('U2',20)]:
    f=pcbnew.FOOTPRINT(b);f.SetReference(ref);f.SetAttributes(pcbnew.FP_SMD)
    q=pcbnew.PAD(f);q.SetNumber('1');q.SetAttribute(pcbnew.PAD_ATTRIB_SMD);q.SetShape(pcbnew.PAD_SHAPE_RECT)
    q.SetLayerSet(pcbnew.LSET.FrontMask());q.SetNet(net);q.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1),pcbnew.FromMM(1)))
    q.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(x),pcbnew.FromMM(10)));f.Add(q);b.Add(f)
   t=pcbnew.PCB_TRACK(b);t.SetNet(net);t.SetLayer(pcbnew.F_Cu);t.SetWidth(pcbnew.FromMM(.35))
   t.SetStart(pcbnew.VECTOR2I(pcbnew.FromMM(10),pcbnew.FromMM(10)));t.SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(20),pcbnew.FromMM(10)));b.Add(t)
   p=Path(d)/'joined.kicad_pcb';pcbnew.SaveBoard(str(p),b);joined=pcbnew.LoadBoard(str(p))
   prior=h.source_clusters(joined);self.assertEqual([2],list(map(len,prior)))
   self.assertTrue(h.clusters_preserved(prior,pcbnew.LoadBoard(str(p)))['passed'])
   cut=pcbnew.LoadBoard(str(p));next(iter(cut.GetTracks())).SetEnd(pcbnew.VECTOR2I(pcbnew.FromMM(19),pcbnew.FromMM(10)))
   broken=Path(d)/'cut.kicad_pcb';pcbnew.SaveBoard(str(broken),cut);cut=pcbnew.LoadBoard(str(broken))
   self.assertEqual([1,1],list(map(len,h.source_clusters(cut))))
   with self.assertRaisesRegex(ValueError,'fragmented'):h.clusters_preserved(prior,cut)
 def native_warning_fixture(self):
  source=ROOT/'reports/motherboard-owned-bypass-routing-20261001/wip-r03-warning-fixture-preparation-r03'
  disposition=json.loads((source/'baseline-disposition.json').read_text())
  report=json.loads((ROOT/'reports/motherboard-owned-bypass-routing-20261001/wip-r03-native-warning-fixture-r02/routed-0.json').read_text())
  return report,disposition
 def test_actual_persisted_warning_stays_visible_and_only_exact_known_row_is_allowed(self):
  report,d=self.native_warning_fixture()
  known=h.wip.reviewed_wip_warnings(report,d,d['board_sha256'])
  self.assertEqual(1,len(report['violations']));self.assertEqual([],h.wip.new_route_defects(report,known))
  new=copy.deepcopy(report);new['violations'][0]['items'][0]['uuid']='additional-real-source-feed-identity'
  self.assertEqual(1,len(h.wip.new_route_defects(new,known)))
 def test_known_warning_can_close_but_error_or_ignored_check_cannot_be_admitted(self):
  report,d=self.native_warning_fixture();known=h.wip.reviewed_wip_warnings(report,d,d['board_sha256'])
  self.assertEqual([],h.wip.new_route_defects(dict(violations=[],ignored_checks=[]),known))
  new=copy.deepcopy(report);new['violations'][0]['severity']='error'
  self.assertEqual(1,len(h.wip.new_route_defects(new,known)))
  new=copy.deepcopy(report);new['ignored_checks']=[{'type':'via_dangling'}]
  with self.assertRaises(ValueError):h.wip.new_route_defects(new,known)
if __name__=='__main__':unittest.main()
