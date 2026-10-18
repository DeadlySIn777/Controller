"""Exact WIP admission and actual native receiving-reference regressions."""
from pathlib import Path
import copy,json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
try:
 import pcbnew
 import hardware_route_owned_bypass_loops_wip_r03 as h
except ModuleNotFoundError:pcbnew=None

@unittest.skipUnless(pcbnew,'KiCad native runtime is required')
class WipBypassGates(unittest.TestCase):
 def warning(self):
  return dict(type='via_dangling',severity='warning',description='Actual unfinished source feed',items=[dict(uuid='source-feed-via',description='Native receiving via',pos=dict(x=1.,y=2.))])
 def admission(self):
  row=self.warning();report=dict(violations=[row],ignored_checks=[])
  disposition=dict(board_sha256='actual-board',routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=[copy.deepcopy(row)])
  return report,disposition
 def test_exact_old_warning_retained_and_legitimate_closure_accepted(self):
  report,d=self.admission();known=h.reviewed_wip_warnings(report,d,'actual-board')
  self.assertEqual([],h.new_route_defects(report,known))
  self.assertEqual([],h.new_route_defects(dict(violations=[],ignored_checks=[]),known))
  self.assertEqual(1,len(report['violations']))
 def test_another_same_type_warning_is_a_real_new_defect(self):
  report,d=self.admission();known=h.reviewed_wip_warnings(report,d,'actual-board')
  added=copy.deepcopy(report['violations'][0]);added['items'][0]['uuid']='new-unconnected-via'
  report['violations'].append(added)
  self.assertEqual([added],h.new_route_defects(report,known))
 def test_stale_board_error_and_ignored_checks_rejected(self):
  report,d=self.admission()
  with self.assertRaisesRegex(ValueError,'disposition'):h.reviewed_wip_warnings(report,d,'other-board')
  report['violations'][0]['severity']='error'
  with self.assertRaisesRegex(ValueError,'errors'):h.reviewed_wip_warnings(report,d,'actual-board')
  report,d=self.admission();report['ignored_checks']=[dict(type='via_dangling')]
  with self.assertRaisesRegex(ValueError,'ignored'):h.reviewed_wip_warnings(report,d,'actual-board')
 def test_disposition_cannot_omit_a_real_native_warning(self):
  report,d=self.admission();d['known_unresolved_native_warnings']=[]
  with self.assertRaisesRegex(ValueError,'differs'):h.reviewed_wip_warnings(report,d,'actual-board')
 def actual_fixture(self):
  folder=ROOT/'reports/motherboard-owned-bypass-routing-20261001/native-final-proof-r02/top'
  b=pcbnew.LoadBoard(str(folder/'owned-bypass-loop-candidate.kicad_pcb'));b.BuildConnectivity()
  receipt=json.loads((folder/'receipt.json').read_text())
  manifest=json.loads((ROOT/'reports/motherboard-owned-bypass-routing-20261001/native-fixture-r08/top/owners.json').read_text())
  return b,receipt,manifest
 def test_actual_owned_reference_and_source_pad_anchors_pass(self):
  b,r,m=self.actual_fixture()
  self.assertEqual(2,len(h.actual_receiving_return_anchors(b,r,m)))
  checker=h.NativeCollectedAnnulusCheck(b,{})
  # Use the exact retained fixture's actual own return identity.
  pad=next(p for fp in b.GetFootprints()if fp.GetReference()==r['owned_loops'][0]['ref']for p in fp.Pads()if p.GetNumber()==m['capacitors'][0]['cap_return'])
  self.assertGreater(checker.reference(pad.GetNetname(),pcbnew.In1_Cu).Area(),0)
 def test_actual_missing_inner_annulus_remains_rejected(self):
  b,r,m=self.actual_fixture()
  for zone in b.Zones():
   if zone.IsOnLayer(pcbnew.In4_Cu):zone.UnFill()
  b.BuildConnectivity()
  with self.assertRaisesRegex(ValueError,'actual local flashed/native-connected'):
   h.actual_receiving_return_anchors(b,r,m)
 def test_persisted_native_unfinished_feed_is_visible_after_routing(self):
  folder=ROOT/'reports/motherboard-owned-bypass-routing-20261001/wip-r03-native-warning-fixture-r02'
  receipt=json.loads((folder/'receipt.json').read_text())
  native=json.loads((folder/'routed-0.json').read_text())
  self.assertEqual(1,len(native['violations']))
  self.assertEqual('via_dangling',native['violations'][0]['type'])
  self.assertEqual(native['violations'],receipt['known_unresolved_native_warnings_retained'])
  self.assertEqual([],receipt['new_route_DRC_defects'])
  self.assertFalse(receipt['complete_board_DRC_pass'])
  self.assertFalse(receipt['manufacturing_ready'])
  self.assertTrue(receipt['all_prior_native_source_pad_clusters_preserved'])
  self.assertEqual(1,sum(g['retained']for g in receipt['owned_loops']))

if __name__=='__main__':unittest.main()
