"""Cheap rejection controls for exact geometry/contact/source constructor."""
import copy
import json
import unittest
from types import SimpleNamespace
import construct as C
W,P=C.W,C.P
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree

def rec(key,layer,shape,kind='segment'):return {'key':key,'kind':kind,'layer':layer,'shape':shape}

class Controls(unittest.TestCase):
 @classmethod
 def setUpClass(cls):cls.packet=json.loads(C.AUDIT.read_bytes())
 def test_xy_crossing_different_layers_does_not_join(self):
  a=rec('F','F.Cu',LineString([(0,0),(2,0)]).buffer(.1));b=rec('I','In3.Cu',LineString([(1,-1),(1,1)]).buffer(.1))
  g=W.ContactGraph([a,b]);self.assertNotEqual(g.find(0),g.find(1))
 def test_width_overlap_connects_without_centreline_touch(self):
  a=rec('a','In3.Cu',LineString([(0,0),(2,0)]).buffer(.2));b=rec('b','In3.Cu',LineString([(1,.3),(1,1)]).buffer(.2))
  g=W.ContactGraph([a,b]);self.assertEqual(g.find(0),g.find(1))
 def test_plated_via_only_joins_actual_present_layers(self):
  records=[rec('v','F.Cu',Point(0,0).buffer(.3),'via'),rec('v','In1.Cu',Point(0,0).buffer(.3),'via'),rec('track','In3.Cu',Point(0,0).buffer(.2))]
  g=W.ContactGraph(records);self.assertEqual(g.find(0),g.find(1));self.assertNotEqual(g.find(0),g.find(2))
 def test_native_suppressed_annulus_is_excluded(self):
  v={'uuid':'v','net':P.NET,'kind':'via','shape':Point(0,0).buffer(.3)}
  model=SimpleNamespace(g={'copper_layers':['F.Cu','In1.Cu','In3.Cu','B.Cu']},records={l:[v] for l in('F.Cu','In1.Cu','In3.Cu','B.Cu')})
  rows=W.graph_records([],model,{'v':{'span':['F.Cu','B.Cu'],'flashed':['In1.Cu']}})
  self.assertEqual([r['layer'] for r in rows],['In1.Cu'])
 def test_unknown_native_via_layers_rejected(self):
  v={'uuid':'v','net':P.NET,'kind':'via','shape':Point(0,0).buffer(.3)}
  model=SimpleNamespace(g={'copper_layers':['F.Cu']},records={'F.Cu':[v]})
  with self.assertRaises(ValueError):W.graph_records([],model,{})
 def test_wrong_net_hole_contact_cannot_be_exempted(self):
  row={'uuid':'t','kind':'segment','a':[0,0],'b':[1,0],'width':.3}
  v={'uuid':'v','net':'/LOGIC_GND','x':1,'y':0,'d':.6,'drill':.3}
  self.assertFalse(P.hole_contact(row,{'uuid':'v'},{'v':v},{}))
 def test_near_uncontacted_same_net_hole_stays_protected(self):
  row={'uuid':'t','kind':'segment','a':[0,0],'b':[.4,0],'width':.3}
  v={'uuid':'v','net':P.NET,'x':1,'y':0,'d':.6,'drill':.3}
  self.assertFalse(P.hole_contact(row,{'uuid':'v'},{'v':v},{}))
 def test_new_copper_envelope_not_centreline_controls_hole_gap(self):
  hole={'kind':'hole','net':'/LOGIC_GND','uuid':'h','shape':Point(1,.51).buffer(.1)}
  model=SimpleNamespace(g={'copper_layers':['F.Cu'],'rule_areas':[],'footprints':[]},records={'F.Cu':[hole]},trees={'F.Cu':STRtree([hole['shape']])},hard={},outline=Point(1,0).buffer(10))
  row={'uuid':'t','kind':'segment','net':P.NET,'a':[0,0],'b':[2,0],'width':.3,'layer':'F.Cu'}
  a=P.audit_row(row,model,{}, {},set());self.assertEqual(len(a['failures']),1);self.assertAlmostEqual(a['failures'][0]['gap_mm'],.26)
 def test_failures_lost_graph_and_new_exception_rejected(self):
  variants=[]
  for field,value in(('failing_items',[{'uuid':'bad'}]),('new_copper_clearance_exceptions',True),('verdict','HOST_WHOLE_GROUP_WITHHELD')):
   p=copy.deepcopy(self.packet);p[field]=value;variants.append(p)
  p=copy.deepcopy(self.packet);p['layer_correct_physical_contact_closure']['lost_physical_relationship_components']=[1];variants.append(p)
  for p in variants:
   with self.subTest(field=list(p.keys())):
    with self.assertRaises(ValueError):C.require_packet(p)
 def test_wrong_native_layers_counts_and_target_identity_rejected(self):
  for field,value in(('suppressed_annulus_vias',0),('r07_sha256','0'*64),('new_vias',2)):
   p=copy.deepcopy(self.packet);p[field]=value
   with self.subTest(field=field):
    with self.assertRaises(ValueError):C.require_packet(p)
 def test_changed_geometry_rejected_by_encoder(self):
  via=copy.deepcopy(next(r for r in self.packet['replacements'] if r['kind']=='via'));via['drill']=.2
  with self.assertRaises(ValueError):C.encode(via,'00000000-0000-0000-0000-000000000001')
 def test_collision_and_old_chunk_preservation(self):
  r07=P.R.R07.read_bytes();inv=P.R.composition.inventory(r07);uid,ch=next(iter(inv[4].items()))
  with self.assertRaises(ValueError):C.pure_add(r07,[(uid,ch)])
 def test_actual_frozen_reconstruction_and_byte_accounting(self):
  r07=P.R.R07.read_bytes();donor=P.I.DONOR.read_bytes();four=W.TARGET.read_bytes()
  d,c,items,new,gap=C.reconstruct(self.packet,C.AUDIT_SHA,r07,donor,four)
  before=P.R.composition.inventory(four);after=P.R.composition.inventory(c)
  self.assertEqual(len(items),269);self.assertEqual(len(new),19);self.assertGreater(gap,.625)
  self.assertTrue(all(after[3][u]==ch for u,ch in before[3].items()))
  self.assertEqual(len(after[4])-len(before[4]),269)
  with self.assertRaises(ValueError):C.reconstruct(self.packet,C.AUDIT_SHA,r07+b' ',donor,four)

if __name__=='__main__':unittest.main(verbosity=2)
