"""Mutations which could destroy retained copper or erase excluded circuits."""
import copy
from pathlib import Path
import sys
import unittest
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'))
from hardware_route_selected_additive import parse,child,children,q,manifest_check,transform_dsn,merge_tree,all_pad_pieces


def row():
 return dict(type='ordinary_logic',controlled_impedance=False,maximum_voltage_v=3.6,width_mm=.2,clearance_mm=.15,
             layers=['F.Cu'],reference_layers={'F.Cu':'In1.Cu'},return_net='/LOGIC_GND',
             reference_corridor_margin_mm=.2,source_pins=[['U1','1'],['R1','1']],allow_vias=False)


def pcb():
 return parse('(kicad_pcb (version 20241229) (generator pcbnew) (layers (0 "F.Cu" signal) (1 "In1.Cu" power) (31 "B.Cu" signal)) '
  '(footprint "part" (layer "F.Cu") (uuid "fp1") (at 5 5) (property "Reference" "U1") '
  '(pad "1" smd rect (at 0 0) (size 1 1) (layers "F.Cu") (net "/SIGNAL") (uuid "p1")) '
  '(pad "1" smd rect (at 1 0) (size 1 1) (layers "F.Cu") (net "/SIGNAL") (uuid "p2")) '
  '(pad "" smd rect (at 0 2) (size .2 .2) (layers "F.Paste") (uuid "paste1"))) '
  '(segment (start 1 1) (end 2 1) (width .2) (layer "F.Cu") (net "/OTHER") (uuid "old1")) '
  '(zone (net "/LOGIC_GND") (layer "In1.Cu") (uuid "z1") (polygon (pts (xy 0 0) (xy 10 0) (xy 10 10) (xy 0 10))) '
  '(filled_polygon (layer "In1.Cu") (pts (xy 0 0) (xy 10 0) (xy 10 10) (xy 0 10)))))')


def donor():
 d=pcb();d.remove(children(d,'segment')[0]) # Raw SES deletes old copper: base still authoritative.
 d.append(parse('(segment (start 5 5) (end 8 5) (width .2) (layer "F.Cu") (net "/SIGNAL") (uuid "new1"))'))
 return d


class SelectedAdditiveRouting(unittest.TestCase):
 def manifest(self,r=None,name='/SIGNAL'):
  r=row() if r is None else r
  return dict(schema_version=1,electrical_review='explicit fixture review',nets={name:r})
 def check(self,m):return manifest_check(m,{'/SIGNAL','/LOGIC_GND','/HOST_SPI_MOSI','/CORE_5V','/AI_DATA'},['F.Cu','In1.Cu','In2.Cu','B.Cu'],{'/SIGNAL':[('U1','1'),('R1','1')]})
 def test_full_reviewed_manifest(self):self.assertEqual(['/SIGNAL'],list(self.check(self.manifest())))
 def test_excluded_host_spi(self):
  with self.assertRaises(ValueError):self.check(self.manifest(name='/HOST_SPI_MOSI'))
 def test_excluded_power(self):
  with self.assertRaises(ValueError):self.check(self.manifest(name='/CORE_5V'))
 def test_excluded_precision(self):
  with self.assertRaises(ValueError):self.check(self.manifest(name='/AI_DATA'))
 def test_no_same_layer_return(self):
  r=row();r['reference_layers']['F.Cu']='F.Cu'
  with self.assertRaises(ValueError):self.check(self.manifest(r))
 def test_no_nonadjacent_reference(self):
  r=row();r['reference_layers']['F.Cu']='In2.Cu'
  with self.assertRaises(ValueError):self.check(self.manifest(r))
 def test_incomplete_source_pin_manifest(self):
  r=row();r['source_pins'].pop()
  with self.assertRaises(ValueError):self.check(self.manifest(r))
 def test_no_unreviewed_reference_margin(self):
  r=row();r.pop('reference_corridor_margin_mm')
  with self.assertRaises(ValueError):self.check(self.manifest(r))
 def test_actual_duplicate_pad_pieces_and_paste_preserved(self):self.assertEqual(3,len(all_pad_pieces(pcb())))
 def test_donor_deletion_never_deletes_retained_copper(self):
  m,a=merge_tree(pcb(),donor(),{'/SIGNAL':row()});self.assertEqual(2,len(children(m,'segment')));self.assertEqual(['new1'],a)
 def test_changed_duplicate_piece_rejected(self):
  d=donor();child(children(children(d,'footprint')[0],'pad')[1],'size')[1]='.9'
  with self.assertRaises(ValueError):merge_tree(pcb(),d,{'/SIGNAL':row()})
 def test_paste_aperture_deletion_rejected(self):
  d=donor();f=children(d,'footprint')[0];f.remove(children(f,'pad')[-1])
  with self.assertRaises(ValueError):merge_tree(pcb(),d,{'/SIGNAL':row()})
 def test_retained_copper_reused_uuid_cannot_change(self):
  d=donor();child(children(d,'segment')[0],'uuid')[1]=q('old1')
  with self.assertRaises(ValueError):merge_tree(pcb(),d,{'/SIGNAL':row()})
 def test_unselected_new_copper_rejected(self):
  d=donor();child(children(d,'segment')[0],'net')[1]=q('/OTHER')
  with self.assertRaises(ValueError):merge_tree(pcb(),d,{'/SIGNAL':row()})
 def test_width_change_rejected(self):
  d=donor();child(children(d,'segment')[0],'width')[1]='.15'
  with self.assertRaises(ValueError):merge_tree(pcb(),d,{'/SIGNAL':row()})
 def test_unapproved_layer_rejected(self):
  d=donor();child(children(d,'segment')[0],'layer')[1]=q('B.Cu')
  with self.assertRaises(ValueError):merge_tree(pcb(),d,{'/SIGNAL':row()})
 def test_zone_definition_change_rejected(self):
  d=donor();child(children(d,'zone')[0],'net')[1]=q('/OTHER')
  with self.assertRaises(ValueError):merge_tree(pcb(),d,{'/SIGNAL':row()})
 def test_refilled_polygons_are_generated_only(self):
  d=donor();z=children(d,'zone')[0];z.remove(children(z,'filled_polygon')[0]);self.assertEqual(1,len(merge_tree(pcb(),d,{'/SIGNAL':row()})[1]))
 def test_selected_dsn_keeps_every_physical_pin_and_wire(self):
  d=parse('(pcb "x" (structure (via "actualVia")) (library (image "x" (pin "p" "1" 0 0))) (placement (component "x" (place U1 0 0 front 0))) '
          '(network (net "/SIGNAL" (pins U1-1 R1-1)) (net "/OTHER" (pins C1-1 C2-1)) (class "old" "/SIGNAL" "/OTHER")) '
          '(wiring (wire (path F.Cu 200 0 0 1 0) (net "/OTHER") (type route)) (via "actualVia" 1 1 (net "/OTHER"))))')
  n,r=transform_dsn(d,{'/SIGNAL':row()})
  self.assertEqual(child(d,'library'),child(n,'library'));self.assertEqual(child(d,'placement'),child(n,'placement'))
  self.assertEqual(1,len(children(child(n,'network'),'net')));self.assertEqual(2,r['old_wires_vias_protected'])
  for item in child(n,'wiring')[1:]:self.assertEqual(['type','protect'],child(item,'type'));self.assertIsNone(child(item,'net'))
 def test_no_fabricated_native_via(self):
  d=parse('(pcb "x" (structure) (network (net "/SIGNAL")))')
  with self.assertRaises(ValueError):transform_dsn(d,{'/SIGNAL':row()})
 def test_excluded_nominal_plane_cannot_recreate_power_net(self):
  d=parse('(pcb "x" (structure (via "nativeVia") (plane "/LOGIC_GND" (polygon In1.Cu 0 0 0 10 0 10 10 0 10))) (network (net "/SIGNAL")))')
  n,r=transform_dsn(d,{'/SIGNAL':row()});self.assertEqual([],children(child(n,'structure'),'plane'));self.assertEqual(1,r['excluded_nominal_planes_replaced_by_native_filled_copper_keepouts'])


if __name__=='__main__':unittest.main()
