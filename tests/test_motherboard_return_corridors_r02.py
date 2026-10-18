"""Actual native six-layer fixtures for the stricter selected-router guard."""
from pathlib import Path
import sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
sys.path.insert(0,str(ROOT/'tests'))
try:
 import pcbnew
 import hardware_check_return_corridors_r02 as strict
 from test_motherboard_return_corridors import fixture
except ModuleNotFoundError:pcbnew=None

@unittest.skipUnless(pcbnew,'Actual KiCad native fixture runtime required')
class StrictReturnTests(unittest.TestCase):
 def test_actual_six_layer_filled_native_route_passes(self):
  with tempfile.TemporaryDirectory()as folder:
   b,added,rows,drc=fixture(folder);r=strict.return_corridor_check(b,added,rows)
   self.assertTrue(r['passed']);self.assertEqual([],drc['violations']);self.assertEqual([],drc.get('ignored_checks',[]))
   self.assertTrue(r['actual_flashed_and_native_connected_reference_annuli_required'])
   self.assertEqual(1,len(r['actual_signal_via_reference_audits']))
   self.assertEqual(['In1.Cu','In4.Cu'],r['actual_signal_via_reference_audits'][0]['return_stitches'][0]['actual_flashed_and_native_connected_reference_layers'])
 def test_original_physical_failure_modes_still_rejected(self):
  for kind in ['wrong_domain','wrong_reference','name_only','too_far','slot','large_hole','one_side_open']:
   with self.subTest(kind=kind),tempfile.TemporaryDirectory()as folder:
    b,added,rows,drc=fixture(folder,kind)
    with self.assertRaises(ValueError):strict.return_corridor_check(b,added,rows)
 def test_actual_drilled_span_without_connected_annulus_rejected(self):
  # An intentionally unfilled reference is a native resource failure, not a
  # name or through-layer declaration that can masquerade as an annulus.
  with tempfile.TemporaryDirectory()as folder:
   b,added,rows,drc=fixture(folder)
   for z in b.Zones():
    if z.IsOnLayer(pcbnew.In4_Cu):z.UnFill()
   b.BuildConnectivity()
   with self.assertRaises(ValueError):strict.return_corridor_check(b,added,rows)
 def test_wrong_declared_via_geometry_rejected(self):
  with tempfile.TemporaryDirectory()as folder:
   b,added,rows,drc=fixture(folder);rows['/DATA']['via_drill_mm']=.20
   with self.assertRaises(ValueError):strict.return_corridor_check(b,added,rows)

if __name__=='__main__':unittest.main()
