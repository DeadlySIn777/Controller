"""Source allowlist and native additive/stitch regression with negative controls."""
import copy,json
from pathlib import Path
import sys,unittest
ROOT=Path(__file__).resolve().parents[1];sys.path.insert(0,str(ROOT/'tools'))
import hardware_route_selected_additive_r02 as h
from test_selected_additive_routing import pcb,donor,row
from hardware_build_ordinary_route_manifest import review,exact_review,native


class ReviewedOrdinaryRouting(unittest.TestCase):
 def fixture_manifest(self):
  r=row();r.update(signal_class='digital_fault_observation',return_domain='LOGIC',
   source_endpoints=[dict(reference=a,pin=b,function='exactPin',mpn='exactPart',actual_logic_return_pins=['2'])for a,b in r['source_pins']])
  return dict(schema_version=2,electrical_review='explicit native fixture',nets={'/SIGNAL':r})
 def check(self,m):
  return h.manifest_check(m,{'/SIGNAL','/LOGIC_GND','/IOL1_L0_SCLK','/SCLK_FIELD','/DOA_SDI_HOST'},
   ['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'],{'/SIGNAL':[('U1','1'),('R1','1')]})
 def test_actual_source_review_76_full_native_producer_and_returns(self):
  r=review(ROOT/'hardware/motherboard',ROOT/'reports/motherboard-integration-20260930/r24-2688-adoption.json')
  self.assertEqual(76,len(r['nets']));self.assertEqual(2688,r['source_physical_footprints'])
  self.assertEqual(set(exact_review()),set(r['nets']))
  _,nets,_=native(json.loads((ROOT/'hardware/motherboard/design.json').read_text()),ROOT/'hardware/motherboard/netlist.xml')
  self.assertEqual(76,len(h.manifest_check(r,set(nets),['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'],nets)))
  for n,row in r['nets'].items():
   self.assertEqual(sorted(map(tuple,row['source_pins'])),sorted((p['reference'],p['pin'])for p in row['source_endpoints']))
 def test_native_endpoint_metadata_required(self):
  m=self.fixture_manifest();m['nets']['/SIGNAL']['source_endpoints'].pop()
  with self.assertRaisesRegex(ValueError,'cover every'):self.check(m)
 def test_active_actual_return_pin_required(self):
  m=self.fixture_manifest();m['nets']['/SIGNAL']['source_endpoints'][0]['actual_logic_return_pins']=[]
  with self.assertRaisesRegex(ValueError,'actual source return'):self.check(m)
 def test_wrong_return_domain_not_a_name_alias(self):
  m=self.fixture_manifest();m['nets']['/SIGNAL']['return_domain']='FIELD_B'
  with self.assertRaisesRegex(ValueError,'return domain'):self.check(m)
 def test_missing_exact_MPN_rejected(self):
  m=self.fixture_manifest();m['nets']['/SIGNAL']['source_endpoints'][0]['mpn']=None
  with self.assertRaisesRegex(ValueError,'actual part/pin'):self.check(m)
 def test_explicit_SPI_and_IOL1_pin_names_rejected(self):
  for n in ['/IOL1_L0_SCLK','/SCLK_FIELD','/DOA_SDI_HOST']:
   m=self.fixture_manifest();m['nets']={n:m['nets']['/SIGNAL']}
   with self.assertRaises(ValueError):self.check(m)
 def test_exact_dependency_hashes(self):self.assertEqual(h.CHECKER_SHA256,h.checked_dependencies()['checker_sha256'])
 def test_v2_accepts_ordinary_explicit_fixture(self):self.assertEqual(['/SIGNAL'],list(self.check(self.fixture_manifest())))
 def test_old_deletion_cannot_erase_authoritative_copper(self):
  m,added=h.merge_tree(pcb(),donor(),{'/SIGNAL':row()})
  self.assertEqual(2,len(h.children(m,'segment')));self.assertEqual(['new1'],added)
 def test_retained_duplicate_land_and_paste_rejected_if_changed(self):
  d=donor();h.child(h.children(h.children(d,'footprint')[0],'pad')[1],'size')[1]='.9'
  with self.assertRaises(ValueError):h.merge_tree(pcb(),d,{'/SIGNAL':row()})
 def test_donor_cannot_add_ground_or_excluded_power(self):
  for n in ['/LOGIC_GND','/CORE_5V']:
   d=donor();h.child(h.children(d,'segment')[0],'net')[1]=h.q(n)
   with self.assertRaisesRegex(ValueError,'excluded-net'):h.merge_tree(pcb(),d,{'/SIGNAL':row()})
 def test_donor_cannot_move_old_route(self):
  d=donor();h.child(h.children(d,'segment')[0],'uuid')[1]=h.q('old1')
  with self.assertRaisesRegex(ValueError,'retained copper'):h.merge_tree(pcb(),d,{'/SIGNAL':row()})


if __name__=='__main__':unittest.main()
