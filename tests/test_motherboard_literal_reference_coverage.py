import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
try:import pcbnew
except ImportError:pcbnew=None


@unittest.skipIf(pcbnew is None,'Native KiCad exact geometry is required')
class LiteralCoverageTests(unittest.TestCase):
    def fixture(self,shapes):
        from hardware_zone_motherboard_returns import rectangle
        from hardware_index_literal_reference_coverage import LiteralReferenceCoverage
        b=pcbnew.BOARD();layers=pcbnew.LSET()
        for l in[pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu]:layers.AddLayer(l)
        b.SetEnabledLayers(layers);b.SetCopperLayerCount(6)
        n=pcbnew.NETINFO_ITEM(b,'/OWN');b.Add(n)
        for shape in shapes:
            z=pcbnew.ZONE(b);z.SetNet(n);z.SetLayer(pcbnew.In1_Cu);z.Outline().Append(shape);z.SetFilledPolysList(pcbnew.In1_Cu,shape);z.SetIsFilled(True);b.Add(z)
        return b,LiteralReferenceCoverage(b,{'/OWN'},[pcbnew.In1_Cu],tile_mm=2)

    def rect(self,bounds):
        from hardware_zone_motherboard_returns import rectangle
        return rectangle(bounds)

    def test_complete_native_fill_passes_both_exact_guards(self):
        b,c=self.fixture([self.rect([0,0,10,10])]);s=self.rect([2,2,3,3])
        self.assertTrue(c.candidate_covered(s,'/OWN',pcbnew.In1_Cu));self.assertTrue(c.final_full_covered(s,'/OWN',pcbnew.In1_Cu))

    def test_literal_hole_is_preserved(self):
        shape=self.rect([0,0,10,10]);shape.BooleanSubtract(self.rect([2.4,2.4,2.6,2.6]))
        b,c=self.fixture([shape]);self.assertFalse(c.candidate_covered(self.rect([2,2,3,3]),'/OWN',pcbnew.In1_Cu))

    def test_one_nanometre_true_slot_is_not_tolerated(self):
        b,c=self.fixture([self.rect([0,0,2.499999,5]),self.rect([2.5,0,5,5])])
        self.assertFalse(c.candidate_covered(self.rect([2,2,3,3]),'/OWN',pcbnew.In1_Cu))

    def test_foreign_or_missing_reference_cannot_pass(self):
        b,c=self.fixture([self.rect([0,0,10,10])]);s=self.rect([2,2,3,3])
        self.assertFalse(c.candidate_covered(s,'/FOREIGN',pcbnew.In1_Cu));self.assertFalse(c.candidate_covered(s,'/OWN',pcbnew.In4_Cu))

    def test_exact_adjacent_pieces_union_without_phantom_gap(self):
        b,c=self.fixture([self.rect([0,0,2.5,5]),self.rect([2.5,0,5,5])]);s=self.rect([2,2,3,3])
        self.assertTrue(c.candidate_covered(s,'/OWN',pcbnew.In1_Cu));self.assertTrue(c.final_full_covered(s,'/OWN',pcbnew.In1_Cu))

    def test_spanned_via_without_real_source_and_annulus_is_rejected(self):
        b,c=self.fixture([self.rect([0,0,10,10])]);v=pcbnew.PCB_VIA(b);v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(2),pcbnew.FromMM(2)));v.SetNet(b.FindNet('/OWN'));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(v)
        self.assertFalse(c.final_ground_stitch(v,[pcbnew.In1_Cu],{}))

    def test_actual_flashed_source_connected_ground_stitch_passes(self):
        b,c=self.fixture([self.rect([0,0,10,10])]);f=pcbnew.FOOTPRINT(b);f.SetReference('J1');b.Add(f)
        p=pcbnew.PAD(f);p.SetNumber('1');p.SetNet(b.FindNet('/OWN'));p.SetAttribute(pcbnew.PAD_ATTRIB_PTH);p.SetSize(pcbnew.VECTOR2I(pcbnew.FromMM(1),pcbnew.FromMM(1)));p.SetDrillSize(pcbnew.VECTOR2I(pcbnew.FromMM(.5),pcbnew.FromMM(.5)));p.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(1),pcbnew.FromMM(1)));p.SetLayerSet(pcbnew.LSET.AllCuMask());f.Add(p)
        v=pcbnew.PCB_VIA(b);v.SetPosition(pcbnew.VECTOR2I(pcbnew.FromMM(2),pcbnew.FromMM(2)));v.SetNet(b.FindNet('/OWN'));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetRemoveUnconnected(False);b.Add(v)
        source={p.m_Uuid.AsString():dict(net='/OWN',native_nc=False)}
        self.assertTrue(c.final_ground_stitch(v,[pcbnew.In1_Cu],source))
        self.assertFalse(c.final_ground_stitch(v,[pcbnew.In1_Cu],{p.m_Uuid.AsString():dict(net='/WRONG',native_nc=False)}))
        self.assertFalse(c.final_ground_stitch(v,[pcbnew.In1_Cu],{p.m_Uuid.AsString():dict(net='/OWN',native_nc=True)}))
        self.assertFalse(c.final_ground_stitch(v,[pcbnew.In1_Cu,pcbnew.In4_Cu],source))


if __name__=='__main__':unittest.main()
