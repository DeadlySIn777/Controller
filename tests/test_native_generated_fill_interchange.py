"""Derived-polygon stripping must preserve every source/rule object."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
try:
 from hardware_merge_bounded_pcb_delta import without_generated_fills,dump_board
except ModuleNotFoundError:
 without_generated_fills=None
from hardware_build_assembly import parse,children

@unittest.skipUnless(without_generated_fills,'Native KiCad Python required')
class DerivedFillInterchange(unittest.TestCase):
 def test_only_generated_polygons_removed(self):
  source='(kicad_pcb (zone (net 2)(polygon (pts(xy 1 2)(xy 3 4))) (filled_polygon(layer "F.Cu")(pts(xy 1 2)(xy 3 4)))) (segment(start 1 2)(end 3 4)(net 2)))'
  wanted=parse(source);zone=children(wanted,'zone')[0];zone.remove(children(zone,'filled_polygon')[0])
  self.assertEqual(parse(without_generated_fills(source)),wanted)
 def test_quoted_fill_like_text_preserved(self):
  source='(kicad_pcb (property "note" "literal (filled_polygon (x)) and \\\"quoted\\\"") (zone(filled_polygon(layer "F.Cu")(pts(xy 0 0)))))'
  result=without_generated_fills(source)
  self.assertIn('literal (filled_polygon (x))',result);self.assertEqual(len(children(parse(result),'property')),1)
 def test_atom_prefix_is_not_generated_fill(self):
  source='(kicad_pcb(filled_polygon_extra 3)(filled_polygonx 4))'
  self.assertEqual(without_generated_fills(source),source)
 def test_unbalanced_generated_polygon_rejected(self):
  with self.assertRaises(ValueError):without_generated_fills('(kicad_pcb(zone(filled_polygon(pts(xy 0 0))')
 def test_top_level_newlines_preserve_all_objects(self):
  source=parse('(kicad_pcb(version 1)(footprint "x"(property "Reference" "R1"))(zone(net 2)(polygon(pts(xy 0 0)))) )')
  text=dump_board(source);self.assertIn('\n',text);self.assertEqual(parse(text),source)

if __name__=='__main__':unittest.main()
