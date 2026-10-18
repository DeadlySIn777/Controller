"""Disconnected native fixtures prove names alone cannot anchor a plane."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
try:
    import pcbnew
    import hardware_validate_motherboard_return_planes_r02 as h
    from hardware_zone_motherboard_returns import rectangle,add_zone
except ModuleNotFoundError:
    pcbnew=None
    h=None


@unittest.skipUnless(pcbnew,'Requires actual KiCad pcbnew runtime')
class ReturnAnchors(unittest.TestCase):
    def fixture(self,through=True,pad_net='/LOGIC_GND',two_pieces=False):
        b=pcbnew.BOARD();b.SetCopperLayerCount(6)
        for name in ['/LOGIC_GND','/motherboard_do/FIELD_B_0V']:
            b.Add(pcbnew.NETINFO_ITEM(b,name))
        fp=pcbnew.FOOTPRINT(b);fp.SetReference('TEST_SOURCE');b.Add(fp)
        p=pcbnew.PAD(fp);p.SetNumber('1');p.SetPosition(pcbnew.VECTOR2I(2000000,2000000))
        p.SetSize(pcbnew.VECTOR2I(1000000,1000000));p.SetNet(b.FindNet(pad_net))
        if through:
            p.SetAttribute(pcbnew.PAD_ATTRIB_PTH);p.SetLayerSet(pcbnew.LSET.AllCuMask());p.SetDrillSize(pcbnew.VECTOR2I(300000,300000))
        else:
            p.SetAttribute(pcbnew.PAD_ATTRIB_SMD);layerset=pcbnew.LSET();layerset.AddLayer(pcbnew.F_Cu);p.SetLayerSet(layerset)
        fp.Add(p)
        z=add_zone(b,'/LOGIC_GND',rectangle([1,1,4,4]),pcbnew.In1_Cu,10,'DISCONNECTED_NATIVE_FIXTURE')
        #Native filled polygons are the checker's input. This explicit fixture
        #supplies native polygon objects; no manufactured board is implied.
        z.SetFilledPolysList(pcbnew.In1_Cu,rectangle([1,1,4,4]))
        z.SetIsFilled(True)
        if two_pieces:
            zz=add_zone(b,'/LOGIC_GND',rectangle([10,1,13,4]),pcbnew.In1_Cu,10,'UNANCHORED_FIXTURE')
            zz.SetFilledPolysList(pcbnew.In1_Cu,rectangle([10,1,13,4]))
            zz.SetIsFilled(True)
        layers=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']if through else['F.Cu']
        mapping=dict(pads=[dict(uuid=p.m_Uuid.AsString(),reference='TEST_SOURCE',pin='1',net=pad_net,
            domain='LOGIC'if pad_net=='/LOGIC_GND'else'FIELD_B',position_mm=[2,2],copper_layers=layers)])
        return b,mapping

    def test_actual_numbered_through_source_pad_anchors_own_fill(self):
        b,m=self.fixture();r=h.validate(b,m);self.assertTrue(r['passed'])
        self.assertEqual(len(r['filled_components'][0]['actual_numbered_through_pad_anchors']),1)

    def test_same_named_unconnected_SMD_pad_does_not_anchor_inner_plane(self):
        b,m=self.fixture(through=False);self.assertFalse(h.validate(b,m)['passed'])

    def test_other_field_return_cannot_anchor_logic_reference(self):
        b,m=self.fixture(pad_net='/motherboard_do/FIELD_B_0V');self.assertFalse(h.validate(b,m)['passed'])

    def test_one_anchored_piece_cannot_credit_disconnected_same_name_piece(self):
        b,m=self.fixture(two_pieces=True);r=h.validate(b,m)
        self.assertFalse(r['passed']);self.assertEqual(len(r['unanchored_components']),1)

    def test_actual_source_pad_net_mismatch_is_rejected(self):
        b,m=self.fixture();m['pads'][0]['net']='/motherboard_do/FIELD_B_0V'
        with self.assertRaises(ValueError):h.validate(b,m)

    def test_stale_source_pad_position_cannot_credit_the_wrong_reference_region(self):
        b,m=self.fixture();m['pads'][0]['position_mm']=[12,2]
        with self.assertRaises(ValueError):h.validate(b,m)

    def test_stale_source_pad_side_cannot_credit_a_front_contact_as_through(self):
        b,m=self.fixture(through=False);m['pads'][0]['copper_layers']=['F.Cu','In1.Cu']
        with self.assertRaises(ValueError):h.validate(b,m)

    def test_unfilled_polygon_does_not_invent_a_native_connected_annulus(self):
        b,m=self.fixture()
        for z in b.Zones():z.SetIsFilled(False)
        self.assertFalse(h.validate(b,m)['passed'])

    def test_spanned_drill_with_removed_inner_annulus_is_not_contact(self):
        b,m=self.fixture();v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet('/LOGIC_GND'));v.SetPosition(pcbnew.VECTOR2I(2800000,2800000));v.SetWidth(500000);v.SetDrill(200000);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetRemoveUnconnected(True);b.Add(v)
        b.BuildConnectivity()
        self.assertTrue(v.IsOnLayer(pcbnew.In4_Cu))
        self.assertFalse(v.FlashLayer(pcbnew.In4_Cu))
        self.assertFalse(h.physical_reference_contact(v,pcbnew.In4_Cu,b.GetConnectivity()))

    def track(self,b,start,end,layer=None,net='/LOGIC_GND'):
        if layer is None:layer=pcbnew.In1_Cu
        t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(layer)
        t.SetStart(pcbnew.VECTOR2I(*(pcbnew.FromMM(v)for v in start)))
        t.SetEnd(pcbnew.VECTOR2I(*(pcbnew.FromMM(v)for v in end)));t.SetWidth(pcbnew.FromMM(.5));b.Add(t);return t

    def test_real_source_connected_inner_track_anchors_the_other_piece(self):
        b,m=self.fixture(two_pieces=True);self.track(b,(2,2),(11,2));r=h.validate(b,m)
        self.assertTrue(r['passed']);other=next(x for x in r['filled_components']if not x['actual_numbered_through_pad_anchors'])
        self.assertTrue(other['actual_source_connected_inner_return_track_anchors'])

    def test_disconnected_same_name_inner_track_is_not_a_source_anchor(self):
        b,m=self.fixture(two_pieces=True);self.track(b,(10.5,2),(11.5,2));r=h.validate(b,m);self.assertFalse(r['passed'])

    def test_wrong_layer_track_cannot_anchor_adjacent_piece(self):
        b,m=self.fixture(two_pieces=True);self.track(b,(2,2),(11,2),pcbnew.In4_Cu);self.assertFalse(h.validate(b,m)['passed'])

    def test_other_domain_track_cannot_anchor_return(self):
        b,m=self.fixture(two_pieces=True);self.track(b,(2,2),(11,2),net='/motherboard_do/FIELD_B_0V')
        with self.assertRaisesRegex(ValueError,'reassigned actual copper nets'):h.validate(b,m)


if __name__=='__main__':unittest.main()
