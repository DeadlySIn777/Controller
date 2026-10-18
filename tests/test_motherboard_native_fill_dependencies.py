"""Frozen native geometry plus real copied-file dependency tamper controls."""
from pathlib import Path
import sys,tempfile,unittest
from unittest.mock import patch
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
try:
 import pcbnew
 import hardware_check_return_corridors_r04 as h
except ModuleNotFoundError:pcbnew=None
@unittest.skipUnless(pcbnew,'Actual KiCad runtime required')
class ExactNativeDependencyGuard(unittest.TestCase):
 def test_actual_all_frozen_native_dependencies_match(self):
  d=h.dependencies()
  self.assertEqual('ae44bbaf5ba31fb4bbe0f1bf7f532f5a07ef5f6546ca82523b760a27379c1aa7',d['original_geometric_checker_sha256'])
 def test_actual_changed_original_geometric_file_is_rejected(self):
  original=Path(h.strict.prior.__file__)
  with tempfile.TemporaryDirectory()as d:
   copy=Path(d)/original.name;copy.write_bytes(original.read_bytes()+b'\n# deliberate dependency tamper\n')
   with patch.object(h.strict.prior,'__file__',str(copy)):
    with self.assertRaisesRegex(ValueError,'original geometric'):h.dependencies()
 def test_actual_changed_nonempty_checker_file_is_rejected(self):
  original=Path(h.prior.__file__)
  with tempfile.TemporaryDirectory()as d:
   copy=Path(d)/original.name;copy.write_bytes(original.read_bytes()+b'\n# deliberate dependency tamper\n')
   with patch.object(h.prior,'__file__',str(copy)):
    with self.assertRaisesRegex(ValueError,'nonempty checker'):h.dependencies()
 def test_frozen_035_native_healthy_and_resource_negatives_remain_exact(self):
  base=ROOT/'reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/native-geometry-controls-r03'
  rows={'/DATA':dict(type='critical_digital',return_net='/LOGIC_GND',
   layers=['F.Cu','B.Cu'],reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},
   width_mm=.35,clearance_mm=.20,reference_corridor_margin_mm=.40,
   return_stitch_distance_mm=1.,allow_vias=True,via_diameter_mm=.6,via_drill_mm=.3)}
  for case in ['healthy','wrong_domain','missing_reference_annulus']:
   with self.subTest(case=case):
    b=pcbnew.LoadBoard(str(base/case/'prototype-route.kicad_pcb'))
    ids={t.m_Uuid.AsString()for t in b.GetTracks()if t.GetNetname()=='/DATA'}
    if case=='healthy':
     r=h.return_corridor_check(b,ids,rows);self.assertTrue(r['passed']);self.assertTrue(r['independent_original_geometric_dependency_guard'])
    else:
     with self.assertRaises(ValueError):h.return_corridor_check(b,ids,rows)
if __name__=='__main__':unittest.main()
