"""Exact-source scope tampering plus real native critical own-return controls."""
from pathlib import Path
import copy,json,sys,tempfile,unittest,xml.etree.ElementTree as E
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT/'tests'))
try:
 import pcbnew
 import hardware_route_critical_digital_additive as h
 R=ROOT/h.SOURCE_REVIEW;G=ROOT/h.GEOMETRY_REVIEW
 from test_motherboard_return_corridors import fixture
except ModuleNotFoundError:pcbnew=None

@unittest.skipUnless(pcbnew,'Actual KiCad native runtime required')
class ExactCriticalScope(unittest.TestCase):
 def setUp(self):
  self.r=json.loads(R.read_text());self.g=json.loads(G.read_text())
  parts=json.loads((ROOT/'hardware/motherboard/design.json').read_text())['components']
  self.nodes={n.get('name'):sorted((p.get('ref'),p.get('pin'))for p in n.findall('node')if p.get('ref')in parts)for n in E.parse(ROOT/'hardware/motherboard/netlist.xml').findall('.//nets/net')}
  self.layers=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
 def check(self,n,row):h.check_row(n,row,self.r,self.g,set(self.nodes),self.layers,self.nodes)
 def test_all_152_exact_source_rows_pass_and_ordinary112_is_not_promoted(self):
  self.assertEqual(152,len(self.g['nets']))
  for n,row in self.g['nets'].items():self.check(n,row)
  ordinary=json.loads((ROOT/h.ORDINARY).read_text())['nets']
  self.assertFalse(set(self.g['nets'])&set(ordinary))
 def test_exact_source_and_geometry_tampering_rejected(self):
  name='/fpga_core/IOL1_L0_SCLK';base=self.g['nets'][name]
  mutations={'wrong_return':lambda x:x.update(return_net='/motherboard_do/FIELD_B_0V'),
   'deleted_pin':lambda x:x['source_pins'].pop(),
   'fieldless_endpoint':lambda x:next(p for p in x['source_endpoints']if p['reference'].startswith('U')).pop('actual_return_pins'),
   'wrong_input_MPN':lambda x:next(p for p in x['source_endpoints']if p['reference']=='U13003').update(mpn='SN74LVC125APWR'),
   'inner_signal_layer':lambda x:x.update(layers=['In2.Cu']),
   'wrong_width':lambda x:x.update(width_mm=.2),
   'loaded_timing_claim':lambda x:x.update(operating_profile_qualified=True),
   'factory_impedance_claim':lambda x:x.update(impedance_factory_qualified=True),
   'package_escape':lambda x:x.update(allow_unreferenced_escape=True),
   'isolation_shortcut':lambda x:x.update(allow_isolation_barrier_crossing=True),
   'oversize_stitch':lambda x:x.update(return_stitch_distance_mm=1.2)}
  for label,change in mutations.items():
   with self.subTest(label=label):
    row=copy.deepcopy(base);change(row)
    with self.assertRaises(ValueError):self.check(name,row)
 def test_ordinary_permission_cannot_enter_critical_executor(self):
  name='/mc_permission/OUT_PERMIT'
  self.assertIn(name,json.loads((ROOT/h.ORDINARY).read_text())['nets'])
  row=copy.deepcopy(self.r['nets'][name]);self.g['nets'][name]=row
  with self.assertRaisesRegex(ValueError,'ordinary112'):self.check(name,row)
 def test_power_and_precision_not_reviewed(self):
  for name in ['/IO_3V3','/motherboard_analog_input/AI_REFCAP','/LOGIC_GND']:
   with self.subTest(name=name),self.assertRaises(ValueError):self.check(name,{})

@unittest.skipUnless(pcbnew,'Actual KiCad native fill/DRC runtime required')
class NativeCriticalReturns(unittest.TestCase):
 def test_real_critical_via_route_has_actual_own_annuli(self):
  with tempfile.TemporaryDirectory()as d:
   b,added,rows,drc=fixture(d)
   rows['/DATA']['type']='critical_digital'
   r=h.fast.return_corridor_check(b,added,rows)
   self.assertTrue(r['passed']);self.assertEqual([],drc['violations']);self.assertEqual([],drc.get('ignored_checks',[]))
   self.assertTrue(r['actual_flashed_and_native_connected_reference_annuli_required'])
 def test_real_wrong_domain_critical_via_rejected(self):
  with tempfile.TemporaryDirectory()as d:
   b,added,rows,drc=fixture(d,'wrong_domain');rows['/DATA']['type']='critical_digital'
   with self.assertRaises(ValueError):h.fast.return_corridor_check(b,added,rows)
 def test_real_critical_span_without_reference_annulus_rejected(self):
  with tempfile.TemporaryDirectory()as d:
   b,added,rows,drc=fixture(d);rows['/DATA']['type']='critical_digital'
   for z in b.Zones():
    if z.IsOnLayer(pcbnew.In4_Cu):z.UnFill()
   b.BuildConnectivity()
   with self.assertRaises(ValueError):h.fast.return_corridor_check(b,added,rows)
 def test_exact_nonempty_native_union_preserves_old_filled_geometry(self):
  with tempfile.TemporaryDirectory()as d:
   b,added,rows,drc=fixture(d)
   old=h.fast.strict.ActualAnnulusReturnCheck(b,rows)
   new=h.fast.NativeCollectedAnnulusCheck(b,rows)
   for layer in [pcbnew.In1_Cu,pcbnew.In4_Cu]:
    a=old.reference('/LOGIC_GND',layer);c=new.reference('/LOGIC_GND',layer)
    self.assertEqual(a.Area(),c.Area());self.assertEqual(a.OutlineCount(),c.OutlineCount())
    for i in range(a.OutlineCount()):
     self.assertEqual([tuple(p)for p in a.COutline(i).CPoints()],[tuple(p)for p in c.COutline(i).CPoints()])
    delta=pcbnew.SHAPE_POLY_SET();delta.Append(a);delta.BooleanSubtract(c)
    self.assertEqual(0,delta.Area());self.assertEqual(0,delta.OutlineCount())
if __name__=='__main__':unittest.main()
