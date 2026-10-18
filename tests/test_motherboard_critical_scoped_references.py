"""Literal scope admission, immutable full evidence and witness negative controls."""
from pathlib import Path
import copy,json,sys,tempfile,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import hardware_scope_critical_reference_qualification as h
class ScopedReferences(unittest.TestCase):
 def setUp(self):
  self.tmp=tempfile.TemporaryDirectory();self.addCleanup(self.tmp.cleanup)
  self.root=Path(self.tmp.name);self.mapping=self.root/'map.json';self.full=self.root/'full.json'
  self.mapping.write_text(json.dumps(dict(pads=[dict(uuid='source-ground-pad')])))
  self.net='/motherboard_analog_output/AO0_COM'
  self.rows=[dict(net=self.net,reference_layer=layer,filled_piece=0,passed=True,
   actual_source_connected_through_stitch_anchors=[dict(uuid='native-via-'+layer,
    source_pad_anchors=[dict(reference='U14608',pin='4',pad_uuid='source-ground-pad')])])
   for layer in ['In1.Cu','In4.Cu']]
  self.report=dict(passed=False,board_sha256='actual-board-hash',source_map_sha256=h.sha(self.mapping),
   exact_source_pad_inventory_checked=1,filled_components=self.rows+[dict(net='/LOGIC_GND',reference_layer='In1.Cu',passed=False)],
   unanchored_components=[dict(net='/LOGIC_GND',reference_layer='In1.Cu',passed=False)])
  self.write()
  self.manifest=dict(board_sha256='actual-board-hash',nets={'/AO0_SPI':dict(return_net=self.net,
   reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'})})
 def write(self):self.full.write_text(json.dumps(self.report))
 def scoped(self):return h.qualify(self.full,self.mapping,[self.net])
 def test_unrelated_unanchored_component_does_not_become_global_pass(self):
  r=self.scoped();proof=h.check(r,self.manifest)
  self.assertFalse(r['whole_board_reference_qualification']);self.assertFalse(r['full_plane_review']['passed'])
  self.assertEqual(1,r['complete_native_unanchored_components_retained']);self.assertEqual([self.net],proof['scoped_return_nets'])
 def test_actual_past_native_unanchored_AO_piece_rejected(self):
  p=ROOT/'reports/motherboard-return-zoning-20261001/source25-r46-per-side-reference-r05'
  with self.assertRaisesRegex(ValueError,'unanchored'):
   h.qualify(p/'physical-reference-anchors.json',p/'inputs/domain-map.json',[self.net])
 def test_scope_cannot_be_expanded_to_another_return(self):
  r=self.scoped();m=copy.deepcopy(self.manifest);m['nets']['/AO0_SPI']['return_net']='/LOGIC_GND'
  with self.assertRaisesRegex(ValueError,'not actually qualified'):h.check(r,m)
 def test_missing_or_fabricated_anchor_witness_rejected(self):
  for anchors in ([],[dict(uuid='via',source_pad_anchors=[dict(reference='U1')])]):
   self.report['filled_components'][0]['actual_source_connected_through_stitch_anchors']=anchors;self.write()
   with self.assertRaisesRegex(ValueError,'anchor|witness'):self.scoped()
 def test_missing_reference_side_rejected(self):
  self.report['filled_components']=self.report['filled_components'][1:];self.write()
  with self.assertRaisesRegex(ValueError,'Both actual'):self.scoped()
 def test_full_report_and_map_changes_rejected(self):
  r=self.scoped();self.report['unanchored_components'].append(dict(net='/FIELD_B_0V'));self.write()
  with self.assertRaisesRegex(ValueError,'evidence changed'):h.check(r,self.manifest)
 def test_changed_board_rows_or_global_claim_rejected(self):
  for field,value in [('board_sha256','different'),('whole_board_reference_qualification',True),('filled_components',[])]:
   r=self.scoped();r[field]=value
   with self.assertRaises(ValueError):h.check(r,self.manifest)
if __name__=='__main__':unittest.main()
