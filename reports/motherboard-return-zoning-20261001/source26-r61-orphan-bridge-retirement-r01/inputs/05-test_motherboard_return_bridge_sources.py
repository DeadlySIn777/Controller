import unittest
try:
 import pcbnew
 from tools.hardware_validate_return_bridge_sources import review
except ImportError:pcbnew=None

@unittest.skipIf(pcbnew is None,'Native KiCad Python required')
class ActualReturnBridgeSource(unittest.TestCase):
 def setUp(self):
  self.b=pcbnew.BOARD();self.n=pcbnew.NETINFO_ITEM(self.b,'RETURN',1);self.b.Add(self.n)
  self.fp=pcbnew.FOOTPRINT(self.b);self.fp.SetReference('R1');self.b.Add(self.fp)
  layers=pcbnew.LSET();layers.AddLayer(pcbnew.F_Cu)
  self.p=pcbnew.PAD(self.fp);self.p.SetNumber('2');self.p.SetAttribute(pcbnew.PAD_ATTRIB_SMD);self.p.SetShape(pcbnew.PAD_SHAPE_RECT);self.p.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1),pcbnew.FromMM(1)));self.p.SetLayerSet(layers);self.p.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(10),pcbnew.FromMM(10)));self.p.SetNet(self.n);self.fp.Add(self.p)
  self.source=[dict(uuid=self.p.m_Uuid.AsString(),reference='R1',pin='2',net='RETURN',native_nc=False)]
 def track(self,s,e,layer=pcbnew.F_Cu if pcbnew else 0):
  t=pcbnew.PCB_TRACK(self.b);t.SetNet(self.n);t.SetLayer(layer);t.SetStart(pcbnew.VECTOR2I(*[pcbnew.FromMM(v)for v in s]));t.SetEnd(pcbnew.VECTOR2I(*[pcbnew.FromMM(v)for v in e]));t.SetWidth(pcbnew.FromMM(.2));self.b.Add(t);return t
 def group(self,*items):return [dict(net='RETURN',new_copper_UUIDs=[t.m_Uuid.AsString()for t in items])]
 def test_actual_numbered_source_reachability(self):
  t=self.track((10,10),(12,10));self.assertTrue(review(self.b,self.group(t),self.source)['passed'])
 def test_absent_predecessor_transfer_rejects_same_named_inner_bridge(self):
  t=self.track((10,10),(12,10),pcbnew.In1_Cu)
  with self.assertRaisesRegex(ValueError,'physically orphaned'):review(self.b,self.group(t),self.source)
 def test_one_good_conductor_does_not_hide_another_orphan(self):
  a=self.track((10,10),(12,10));q=self.track((20,20),(22,20))
  with self.assertRaisesRegex(ValueError,'physically orphaned'):review(self.b,self.group(a,q),self.source)
 def test_nc_pad_is_not_a_real_return_source(self):
  t=self.track((10,10),(12,10));self.source[0]['native_nc']=True
  with self.assertRaisesRegex(ValueError,'physically orphaned'):review(self.b,self.group(t),self.source)
 def test_stale_source_net_is_rejected(self):
  t=self.track((10,10),(12,10));self.source[0]['net']='OTHER'
  with self.assertRaisesRegex(ValueError,'identity/net'):review(self.b,self.group(t),self.source)
 def test_duplicate_group_cannot_recount_source(self):
  t=self.track((10,10),(12,10));g=self.group(t)
  with self.assertRaisesRegex(ValueError,'multiple groups'):review(self.b,g+g,self.source)

if __name__=='__main__':unittest.main()
