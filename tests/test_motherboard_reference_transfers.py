"""Actual native cross-reference transfer contacts; no drill-span-only credit."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
sys.path.insert(0,str(Path(__file__).resolve().parent))
import test_motherboard_return_plane_track_anchors as _a
pcbnew,h=_a.pcbnew,_a.h

@unittest.skipUnless(pcbnew,'Actual KiCad runtime required')
class ReferenceTransferContacts(unittest.TestCase):
 fixture=_a.ReturnAnchors.fixture
 track=_a.ReturnAnchors.track
 def via(self,b,net='/LOGIC_GND'):
  v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(net));v.SetPosition(pcbnew.VECTOR2I(11000000,2000000));v.SetWidth(500000);v.SetDrill(200000);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetRemoveUnconnected(False);b.Add(v);return v
 def test_actual_other_reference_track_and_both_annuli_anchor_original_piece(self):
  b,m=self.fixture(two_pieces=True);v=self.via(b);t=self.track(b,(2,2),(11,2),pcbnew.In4_Cu)
  result=h.validate(b,m)
  self.assertTrue(result['passed'])
  self.assertTrue(h.physical_reference_contact(v,pcbnew.In1_Cu,b.GetConnectivity()))
  self.assertTrue(h.physical_reference_contact(v,pcbnew.In4_Cu,b.GetConnectivity()))
  self.assertIn(m['pads'][0]['uuid'],{p.m_Uuid.AsString()for p in b.GetConnectivity().GetConnectedItems(v)})
 def test_unconnected_same_name_via_does_not_create_source(self):
  b,m=self.fixture(two_pieces=True);v=self.via(b)
  self.assertFalse(h.validate(b,m)['passed'])
  self.assertFalse(h.physical_reference_contact(v,pcbnew.In4_Cu,b.GetConnectivity()))
 def test_opposite_reference_track_without_the_physical_via_cannot_transfer(self):
  b,m=self.fixture(two_pieces=True);self.track(b,(2,2),(11,2),pcbnew.In4_Cu)
  self.assertFalse(h.validate(b,m)['passed'])
 def test_wrong_field_net_transfer_is_rejected(self):
  b,m=self.fixture(two_pieces=True);v=self.via(b,'/motherboard_do/FIELD_B_0V');self.track(b,(2,2),(11,2),pcbnew.In4_Cu)
  with self.assertRaises(ValueError):h.validate(b,m)

if __name__=='__main__':unittest.main()
