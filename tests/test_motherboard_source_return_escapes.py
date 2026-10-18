import math,sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
try:import pcbnew
except ImportError:pcbnew=None

@unittest.skipUnless(pcbnew,'Native KiCad Python required')
class SourceReturnEscapes(unittest.TestCase):
 def setUp(self):
  from hardware_escape_unanchored_source_returns import eligible,choose_escape
  from hardware_zone_motherboard_returns import rectangle
  self.eligible=eligible;self.choose=choose_escape;self.rect=rectangle
  self.b=pcbnew.BOARD();self.f=pcbnew.FOOTPRINT(self.b);self.f.SetReference('R14765');self.f.SetLayer(pcbnew.F_Cu);self.b.Add(self.f)
  self.p=pcbnew.PAD(self.f);self.p.SetNumber('2');self.p.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(10),pcbnew.FromMM(10)));self.p.SetAttribute(pcbnew.PAD_ATTRIB_SMD);self.p.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(.8),pcbnew.FromMM(.8)));self.p.SetLayerSet(pcbnew.LSET.FrontMask());self.f.Add(self.p)
  self.g=type('G',(),{'via':lambda s,p,n:True,'clear':lambda s,p,n,l,w:True})()
 def test_only_exact_reviewed_parts(self):
  self.assertTrue(self.eligible('R14765',{'components':{'R14765':{'mpn':'CRCW060310K0FKEA'}}}))
  self.assertFalse(self.eligible('Q10001',{'components':{'Q10001':{'mpn':'BAS16,215'}}}))
 def test_changed_mpn_is_rejected(self):
  self.assertFalse(self.eligible('R14765',{'components':{'R14765':{'mpn':'HIGH_CURRENT_SHUNT'}}}))
 def test_owned_full_annulus_escape(self):
  q=self.choose(self.p,'AI_AGND',self.rect([9,9,13,13]),self.g);self.assertIsNotNone(q);self.assertLessEqual(math.dist(q,(10,10)),3.01)
 def test_open_adjacent_reference_rejects(self):
  self.assertIsNone(self.choose(self.p,'AI_AGND',self.rect([20,20,21,21]),self.g))
 def test_narrow_fill_cannot_credit_via_centre(self):
  self.assertIsNone(self.choose(self.p,'AI_AGND',self.rect([10.5,9.99,13,10.01]),self.g))
 def test_foreign_pad_or_barrier_collision_rejects(self):
  self.g.via=lambda p,n:False;self.assertIsNone(self.choose(self.p,'AI_AGND',self.rect([9,9,13,13]),self.g))
 def test_wrong_source_side_rejects(self):
  self.f.SetLayer(pcbnew.In2_Cu);self.assertIsNone(self.choose(self.p,'AI_AGND',self.rect([9,9,13,13]),self.g))

if __name__=='__main__':unittest.main()
