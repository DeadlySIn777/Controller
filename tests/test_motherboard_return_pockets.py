"""Native empty-pocket versus actual source-projection negative controls."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
try:
    import pcbnew
    import hardware_classify_unanchored_return_pockets as h
    from hardware_zone_motherboard_returns import add_zone,rectangle
except ModuleNotFoundError:pcbnew=None


@unittest.skipUnless(pcbnew,'Requires actual KiCad runtime')
class ReturnPockets(unittest.TestCase):
    def fixture(self,pad_net=None,pos=(2,2),signal=False):
        b=pcbnew.BOARD();b.SetCopperLayerCount(6)
        for n in ['/LOGIC_GND','/motherboard_do/FIELD_B_0V','SIGNAL']:b.Add(pcbnew.NETINFO_ITEM(b,n))
        z=add_zone(b,'/LOGIC_GND',rectangle([1,1,4,4]),pcbnew.In1_Cu,10,'EXPLICIT_UNANCHORED_NATIVE_FIXTURE');z.SetFilledPolysList(pcbnew.In1_Cu,rectangle([1,1,4,4]));rows=[]
        if pad_net:
            f=pcbnew.FOOTPRINT(b);f.SetReference('SOURCE_FIXTURE');b.Add(f);p=pcbnew.PAD(f);p.SetNumber('1');p.SetNet(b.FindNet(pad_net));p.SetSize(pcbnew.VECTOR2I(1000000,1000000));p.SetPosition(pcbnew.VECTOR2I(*(pcbnew.FromMM(x)for x in pos)));p.SetAttribute(pcbnew.PAD_ATTRIB_SMD);ls=pcbnew.LSET();ls.AddLayer(pcbnew.F_Cu);p.SetLayerSet(ls);f.Add(p)
            rows.append(dict(reference=f.GetReference(),pin='1',uuid=p.m_Uuid.AsString(),net=pad_net,domain='FIELD_B'if pad_net=='/motherboard_do/FIELD_B_0V'else'LOGIC',position_mm=list(pos),copper_layers=['F.Cu'],copper_aabb_mm=[pos[0]-.5,pos[1]-.5,pos[0]+.5,pos[1]+.5]))
        if signal:
            t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(pad_net));t.SetLayer(pcbnew.In2_Cu);t.SetWidth(pcbnew.FromMM(.2));t.SetStart(pcbnew.VECTOR2I(500000,2000000));t.SetEnd(pcbnew.VECTOR2I(4500000,2000000));b.Add(t)
        return b,dict(pads=rows)

    def test_truly_empty_unanchored_fill_is_not_a_source_requirement(self):
        b,m=self.fixture();r=h.classify(b,m);self.assertEqual(r['empty_count'],1);self.assertEqual(r['source_bearing_count'],0)

    def test_unanchored_actual_SMD_ground_requires_stitching(self):
        b,m=self.fixture('/LOGIC_GND');r=h.classify(b,m);self.assertEqual(r['source_bearing_count'],1);self.assertEqual(r['empty_count'],0)

    def test_other_field_domain_pad_cannot_create_logic_reference_need(self):
        b,m=self.fixture('/motherboard_do/FIELD_B_0V');self.assertEqual(h.classify(b,m)['empty_count'],1)

    def test_actual_owned_signal_projection_requires_real_reference(self):
        b,m=self.fixture('SIGNAL',pos=(25,25),signal=True);self.assertEqual(h.classify(b,m)['source_bearing_count'],1)

    def test_foreign_signal_geometry_cannot_create_logic_reference_need(self):
        b,m=self.fixture('/motherboard_do/FIELD_B_0V',pos=(25,25),signal=True);self.assertEqual(h.classify(b,m)['empty_count'],1)

    def test_source_adjacent_antipad_margin_preserves_required_reference(self):
        # Actual source land lies outside the fill, with a .3 mm antipad gap.
        # Centre-only classification would incorrectly delete this resource.
        b,m=self.fixture('SIGNAL',pos=(4.8,2))
        r=h.classify(b,m)
        self.assertEqual(r['source_bearing_count'],1)
        self.assertEqual(r['empty_count'],0)

    def test_remote_source_does_not_keep_an_empty_reference_pocket(self):
        b,m=self.fixture('SIGNAL',pos=(5.1,2))
        self.assertEqual(h.classify(b,m)['empty_count'],1)


if __name__=='__main__':unittest.main()
