"""Physical native reference contacts for accepted receiving bypass loops."""
from pathlib import Path
import json,sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
try:
 import pcbnew
 import hardware_route_owned_bypass_loops_r02 as h
except ModuleNotFoundError:pcbnew=None

@unittest.skipUnless(pcbnew,'Actual KiCad native fixture runtime required')
class OwnedBypassAnnuli(unittest.TestCase):
 def fixture(self,case):
  folder=ROOT/'reports/motherboard-owned-bypass-routing-20261001/native-final-proof-r02'/case
  board=pcbnew.LoadBoard(str(folder/'owned-bypass-loop-candidate.kicad_pcb'));board.BuildConnectivity()
  receipt=json.loads((folder/'receipt.json').read_text())
  owners=json.loads((ROOT/'reports/motherboard-owned-bypass-routing-20261001/native-fixture-r08'/case/'owners.json').read_text())
  return board,receipt,owners
 def test_actual_front_and_back_receiving_anchors_pass(self):
  for case in ['top','bottom']:
   with self.subTest(case=case):
    b,r,m=self.fixture(case);proof=h.actual_receiving_return_anchors(b,r,m)
    self.assertEqual(2,len(proof))
    self.assertTrue(all(v['physical_reference_anchors']for v in proof))
    self.assertTrue(all(p['actual_flashed_and_native_connected_reference_annuli']for v in proof for p in v['physical_reference_anchors']))
 def test_drilled_span_without_one_actual_reference_contact_rejected(self):
  b,r,m=self.fixture('top')
  for zone in b.Zones():
   if zone.IsOnLayer(pcbnew.In4_Cu):zone.UnFill()
  b.BuildConnectivity()
  local=[v for v in b.GetTracks()if isinstance(v,pcbnew.PCB_VIA)]
  self.assertTrue(all(v.IsOnLayer(pcbnew.In4_Cu)for v in local))
  self.assertTrue(all(not b.GetConnectivity().IsConnectedOnLayer(v,pcbnew.In4_Cu)for v in local))
  with self.assertRaisesRegex(ValueError,'actual local flashed/native-connected'):
   h.actual_receiving_return_anchors(b,r,m)
 def test_no_owned_loop_can_credit_remote_ground_via(self):
  b,r,m=self.fixture('top')
  # Leave the real remote source pad/plane anchor intact, move only each
  # close receiving ground stitch away. Mere shared names are insufficient.
  close={p['uuid']for v in h.actual_receiving_return_anchors(b,r,m)for p in v['physical_reference_anchors']}
  for v in list(b.GetTracks()):
   if v.m_Uuid.AsString()in close:v.SetPosition(h.prior.xy((18,12)))
  b.BuildConnectivity()
  with self.assertRaisesRegex(ValueError,'actual local flashed/native-connected'):
   h.actual_receiving_return_anchors(b,r,m)

if __name__=='__main__':unittest.main()
