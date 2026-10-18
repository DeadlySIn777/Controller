"""Native physical return-transfer geometry and domain negative controls."""
from pathlib import Path
import sys,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
try:
    import pcbnew
    import hardware_stitch_owned_return_planes as h
    from hardware_zone_motherboard_returns import rectangle,add_zone
    from hardware_route_owned_bypass_loops import Geometry
except ModuleNotFoundError:pcbnew=None


@unittest.skipUnless(pcbnew,'Requires actual KiCad runtime')
class ReturnTransfers(unittest.TestCase):
    def board(self):
        b=pcbnew.BOARD();b.SetCopperLayerCount(6)
        for n in ['/LOGIC_GND','/motherboard_do/FIELD_B_0V','/CHASSIS','FOREIGN']:
            b.Add(pcbnew.NETINFO_ITEM(b,n))
        return b

    def test_full_both_side_same_return_overlap_selects_real_native_location(self):
        b=self.board();p=rectangle([10,10,12,12]);q=rectangle([10.5,10.5,12.5,12.5])
        selected=h.choose_transfer('/LOGIC_GND',p,[(3,q)],Geometry(b))
        self.assertIsNotNone(selected);self.assertEqual(selected[1],3)
        disk=h.circle(tuple(h.xy(selected[0])),pcbnew.FromMM(.26))
        self.assertTrue(h.covered(disk,p));self.assertTrue(h.covered(disk,q))

    def test_no_opposite_physically_anchored_piece_cannot_create_source(self):
        self.assertIsNone(h.choose_transfer('/LOGIC_GND',rectangle([10,10,12,12]),[],Geometry(self.board())))

    def test_touching_fills_without_full_native_annulus_are_rejected(self):
        p=rectangle([10,10,12,12]);q=rectangle([11.8,10,14,12])
        self.assertIsNone(h.choose_transfer('/LOGIC_GND',p,[(0,q)],Geometry(self.board())))

    def test_all_layer_foreign_pad_blocks_the_transfer(self):
        b=self.board();f=pcbnew.FOOTPRINT(b);f.SetReference('FOREIGN_FIXTURE');b.Add(f)
        p=pcbnew.PAD(f);p.SetNumber('1');p.SetNet(b.FindNet('FOREIGN'));p.SetPosition(h.xy((11,11)));p.SetSize(h.xy((3,3)));p.SetAttribute(pcbnew.PAD_ATTRIB_SMD)
        ls=pcbnew.LSET();ls.AddLayer(pcbnew.B_Cu);p.SetLayerSet(ls);f.Add(p)
        shape=rectangle([10.5,10.5,11.5,11.5])
        self.assertIsNone(h.choose_transfer('/LOGIC_GND',shape,[(0,shape)],Geometry(b)))

    def test_functional_isolation_via_barrier_blocks_transfer(self):
        b=self.board();z=pcbnew.ZONE(b);z.SetIsRuleArea(True);z.SetDoNotAllowVias(True);z.Outline().Append(rectangle([10,10,12,12]));ls=pcbnew.LSET()
        for layer in [pcbnew.F_Cu,pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu,pcbnew.B_Cu]:ls.AddLayer(layer)
        z.SetLayerSet(ls);b.Add(z);shape=rectangle([10.5,10.5,11.5,11.5])
        self.assertIsNone(h.choose_transfer('/LOGIC_GND',shape,[(0,shape)],Geometry(b)))

    def test_raw_isow_or_floating_or_chassis_net_is_forbidden(self):
        b=self.board();shape=rectangle([10,10,12,12])
        for net in ['/motherboard_comms/RS485_ISO_RETURN_RAW','/CHASSIS','SUB_ISLAND_12','DRY_CONTACT']:
            with self.assertRaises(ValueError):h.choose_transfer(net,shape,[(0,shape)],Geometry(b))

    def test_filled_resource_inventory_preserves_actual_layer_and_ground(self):
        b=self.board();shape=rectangle([10,10,12,12])
        for net,layer in [('/LOGIC_GND',pcbnew.In1_Cu),('/motherboard_do/FIELD_B_0V',pcbnew.In4_Cu),('/CHASSIS',pcbnew.In1_Cu)]:
            z=add_zone(b,net,shape,layer,10,'EXPLICIT_NATIVE_REFERENCE_FIXTURE');z.SetFilledPolysList(layer,shape)
        resources=h.filled_resources(b)
        self.assertEqual(set(resources),{('/LOGIC_GND',pcbnew.In1_Cu),('/motherboard_do/FIELD_B_0V',pcbnew.In4_Cu)})
        # Resource topology is reviewed repeatedly while actual anchors
        # propagate. A one-shot generator would lose islands on the next pass.
        self.assertEqual(len(resources['/LOGIC_GND',pcbnew.In1_Cu]),1)
        self.assertEqual(len(list(resources['/LOGIC_GND',pcbnew.In1_Cu])),1)
        self.assertEqual(len(list(resources['/LOGIC_GND',pcbnew.In1_Cu])),1)


if __name__=='__main__':unittest.main()
