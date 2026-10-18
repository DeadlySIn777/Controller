import sys,unittest,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
try:import pcbnew
except ImportError:pcbnew=None

@unittest.skipUnless(pcbnew,'Native KiCad Python required')
class ReferenceBridges(unittest.TestCase):
 def setUp(self):
  from hardware_bridge_owned_return_resources import ReferenceGuard,legal_path,compact_path
  from hardware_route_local_signals import GeometryIndex
  from hardware_zone_motherboard_returns import rectangle
  self.Guard=ReferenceGuard;self.route=legal_path;self.compact=compact_path;self.rect=rectangle
  self.g=ReferenceGuard.__new__(ReferenceGuard);self.g.indices={pcbnew.In1_Cu:GeometryIndex()};self.g.geometry=type('G',(),{'clear':lambda s,p,n,l,w:True})()
 def block(self,net,box):self.g.indices[pcbnew.In1_Cu].add((net,self.rect(box)),box)
 def test_same_owner_projection_is_permitted(self):
  self.block('/LOGIC_GND',[0,0,3,3]);self.assertTrue(self.g.clear([(1,1),(2,2)],'/LOGIC_GND',pcbnew.In1_Cu))
 def test_wrong_galvanic_projection_rejects(self):
  self.block('/motherboard_do/FIELD_B_0V',[0,0,3,3]);self.assertFalse(self.g.clear([(1,1),(2,2)],'/LOGIC_GND',pcbnew.In1_Cu))
 def test_floating_island_never_borrows_ground(self):
  self.block(None,[0,0,3,3]);self.assertFalse(self.g.clear([(1,1),(2,2)],'/LOGIC_GND',pcbnew.In1_Cu))
 def test_raw_converter_return_rejected(self):
  self.assertFalse(self.g.clear([(1,1),(2,2)],'/motherboard_comms/RS485_ISO_RETURN_RAW',pcbnew.In1_Cu))
 def test_native_copper_or_barrier_guard_cannot_be_overridden(self):
  self.g.geometry.clear=lambda p,n,l,w:False;self.assertFalse(self.g.clear([(1,1),(2,2)],'/LOGIC_GND',pcbnew.In1_Cu))
 def test_bounded_clear_path(self):
  p=self.route((1,1),(3,1),'/LOGIC_GND',pcbnew.In1_Cu,self.g,4);self.assertEqual(p,[(1,1),(3,1)])
 def test_detour_does_not_cross_foreign_component(self):
  self.block('/motherboard_do/FIELD_B_0V',[1.8,.7,2.2,1.3]);p=self.route((1,1),(3,1),'/LOGIC_GND',pcbnew.In1_Cu,self.g,8)
  self.assertIsNotNone(p);self.assertTrue(self.g.clear(p,'/LOGIC_GND',pcbnew.In1_Cu));self.assertGreater(sum(math.dist(s,e)for s,e in zip(p,p[1:])),2)
 def test_span_ceiling_prevents_unbounded_distribution(self):
  self.assertIsNone(self.route((1,1),(30,1),'/LOGIC_GND',pcbnew.In1_Cu,self.g,8))
 def test_collinear_compaction_keeps_real_endpoints(self):
  self.assertEqual(self.compact([(1,1),(2,1),(3,1),(3,2)]),[(1,1),(3,1),(3,2)])

if __name__=='__main__':unittest.main()
