"""Exercise actual KiCad base-proxy behavior rather than mocked via types."""
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
try:
 import pcbnew
 import hardware_route_owned_bypass_loops_wip_r04 as h
except ModuleNotFoundError:pcbnew=None

@unittest.skipUnless(pcbnew,'Actual KiCad runtime required')
class NativeViaLookup(unittest.TestCase):
 def fixture(self):
  p=ROOT/'reports/motherboard-owned-bypass-routing-20261001/native-final-proof-r02/top/owned-bypass-loop-candidate.kicad_pcb'
  b=pcbnew.LoadBoard(str(p));b.BuildConnectivity()
  pairs=[]
  for pad in b.GetPads():
   vias=h.connected_native_vias(b,pad)
   if vias:pairs.append((pad,vias))
  self.assertTrue(pairs)
  return b,pairs
 def test_actual_base_proxy_resolves_typed_physical_via(self):
  b,pairs=self.fixture();observed_proxy=False
  for pad,vias in pairs:
   raw={x.m_Uuid.AsString():x for x in b.GetConnectivity().GetConnectedItems(pad)}
   for v in vias:
    self.assertIsInstance(v,pcbnew.PCB_VIA)
    self.assertEqual(v.GetNetname(),pad.GetNetname())
    self.assertIn(v.m_Uuid.AsString(),raw)
    observed_proxy|=not isinstance(raw[v.m_Uuid.AsString()],pcbnew.PCB_VIA)
  self.assertTrue(observed_proxy,'Fixture must reproduce the actual KiCad SWIG lookup failure')
 def test_unconnected_same_net_via_cannot_be_credited(self):
  b,pairs=self.fixture();pad=pairs[0][0]
  v=pcbnew.PCB_VIA(b);v.SetNet(pad.GetNet());v.SetPosition(h.xy((100,100)))
  v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v);b.BuildConnectivity()
  self.assertNotIn(v.m_Uuid.AsString(),{x.m_Uuid.AsString()for x in h.connected_native_vias(b,pad)})
 def test_typed_lookup_does_not_waive_missing_annulus(self):
  b,pairs=self.fixture()
  for z in b.Zones():
   if z.IsOnLayer(pcbnew.In4_Cu):z.UnFill()
  b.BuildConnectivity()
  # Via membership still exists; native reference connectivity must still fail.
  vias=h.connected_native_vias(b,pairs[0][0]);self.assertTrue(vias)
  self.assertTrue(all(not b.GetConnectivity().IsConnectedOnLayer(v,pcbnew.In4_Cu)for v in vias))

if __name__=='__main__':unittest.main()
