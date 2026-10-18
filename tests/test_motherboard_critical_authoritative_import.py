"""Exact native placement/control proofs; no geometry tolerance waiver."""
from pathlib import Path
import copy,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
try:
 import pcbnew
 import hardware_route_critical_digital_wip_r05 as h
except ModuleNotFoundError:pcbnew=None
@unittest.skipUnless(pcbnew,'Actual KiCad native runtime required')
class AuthoritativeImport(unittest.TestCase):
 def test_actual_full_board_session_placement_and_one_coordinate_tamper(self):
  p=ROOT/'reports/motherboard-critical-routing-20261001/actual-AO0-source26-root56-r01'
  a=h.engine.parse((p/'prepared/native.dsn').read_text());b=h.engine.parse((p/'actual-router.ses').read_text())
  h.assert_native_placement(a,b);self.assertEqual(2688,len(h.placement_inventory(b)[1]))
  bad=copy.deepcopy(b);row=h.engine.children(h.engine.children(h.engine.child(bad,'placement'),'component')[0],'place')[0]
  row[2]=str(float(row[2])+1)
  with self.assertRaisesRegex(ValueError,'placement inventory'):h.assert_native_placement(a,bad)
 def test_actual_native_control_rejects_one_internal_unit_pose_or_land_change(self):
  with tempfile.TemporaryDirectory()as d:
   p=Path(d);b=pcbnew.BOARD();f=pcbnew.FOOTPRINT(b);f.SetReference('U1');f.SetPosition(pcbnew.VECTOR2I(10000000,10000000))
   q=pcbnew.PAD(f);q.SetNumber('1');q.SetAttribute(pcbnew.PAD_ATTRIB_SMD);q.SetShape(pcbnew.PAD_SHAPE_RECT)
   q.SetLayerSet(pcbnew.LSET.FrontMask());q.SetSize(pcbnew.VECTOR2I(1000000,1000000));q.SetPosition(f.GetPosition());f.Add(q);b.Add(f)
   pcbnew.SaveBoard(str(p/'control.kicad_pcb'),b);expected=h.engine.parse((p/'control.kicad_pcb').read_text())
   for change in ('pose','land'):
    native=pcbnew.LoadBoard(str(p/'control.kicad_pcb'));foot=next(iter(native.GetFootprints()))
    if change=='pose':foot.SetPosition(pcbnew.VECTOR2I(10000001,10000000))
    else:next(iter(foot.Pads())).SetSize(pcbnew.VECTOR2I(1000001,1000000))
    pcbnew.SaveBoard(str(p/(change+'.kicad_pcb')),native);bad=h.engine.parse((p/(change+'.kicad_pcb')).read_text())
    with self.assertRaisesRegex(ValueError,'beyond exact'):h.assert_control_matches(expected,bad)
 def test_all_donor_immutable_data_is_discarded_not_normalized_into_board(self):
  base=['kicad_pcb',['footprint','"original"',['property','"Reference"','"U1"'],['at','1.000001','2']],['zone',['uuid','"z"']]]
  donor=copy.deepcopy(base);donor[1][1]='"tampered"';donor.append(['segment',['width','.35']])
  restored=h.restore_immutable(base,donor)
  self.assertEqual(h.engine.immutable_objects(base),h.engine.immutable_objects(restored))
  self.assertEqual(1,len(h.engine.children(restored,'segment')))
if __name__=='__main__':unittest.main()
