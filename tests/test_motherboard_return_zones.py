"""Native plane serialization and bounded geometry search regressions."""
from pathlib import Path
import sys,tempfile,unittest
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
try:
    import pcbnew
    import hardware_zone_motherboard_returns as h
except ModuleNotFoundError:
    pcbnew=None


@unittest.skipUnless(pcbnew,'Requires the actual KiCad pcbnew runtime')
class ReturnZones(unittest.TestCase):
    def test_native_disconnected_zones_survive_save_reload(self):
        b=pcbnew.BOARD();b.SetCopperLayerCount(6)
        net=pcbnew.NETINFO_ITEM(b,'/FIELD_B_0V');b.Add(net)
        poly=h.rectangle([1,1,4,4]);poly.Append(h.rectangle([10,10,13,13]))
        pieces=list(h.split_polygons(poly));self.assertEqual(len(pieces),2)
        for i,piece in enumerate(pieces):h.add_zone(b,'/FIELD_B_0V',piece,pcbnew.In1_Cu,10,f'OWN_FIELD_{i}')
        with tempfile.TemporaryDirectory()as folder:
            path=Path(folder)/'actual-zones.kicad_pcb';pcbnew.SaveBoard(str(path),b)
            fresh=pcbnew.LoadBoard(str(path));self.assertEqual(len(fresh.Zones()),2)
            coverage=[z.Outline() for z in fresh.Zones()]
            self.assertTrue(any(p.Contains(pcbnew.VECTOR2I(pcbnew.FromMM(2),pcbnew.FromMM(2)))for p in coverage))
            self.assertTrue(any(p.Contains(pcbnew.VECTOR2I(pcbnew.FromMM(11),pcbnew.FromMM(11)))for p in coverage))

    def test_separate_functional_domains_keep_explicit_band(self):
        row=dict(side_domains=[['LOGIC'],['FIELD_B']],package_axis=[1,0],cross_axis=[0,1],polygon_mm=[[-2,-3],[2,-3],[2,3],[-2,3]])
        band=h.functional_barrier(row)
        self.assertAlmostEqual(band.Area()/1e12,3.6)
        self.assertTrue(band.Contains(pcbnew.VECTOR2I(0,0)))
        self.assertFalse(band.Contains(pcbnew.VECTOR2I(pcbnew.FromMM(.31),0)))

    def test_same_reference_does_not_invent_kilovolt_board_gap(self):
        row=dict(side_domains=[['LOGIC'],['LOGIC']],package_axis=[1,0],cross_axis=[0,1],polygon_mm=[[-2,-3],[2,-3],[2,3],[-2,3]])
        self.assertEqual(h.functional_barrier(row).OutlineCount(),0)

    def test_true_blocked_components_are_not_reported_connected(self):
        width,height=7,5;blocked=bytearray(width*height)
        for y in range(height):blocked[y*width+3]=1
        labels,count=h.connected_grid_labels(blocked,width,height)
        self.assertEqual(count,2)
        self.assertNotEqual(labels[1],labels[5])
        self.assertIsNone(h.grid_path((1,1),(5,1),blocked,width,height))

    def test_search_budget_does_not_return_unproved_partial_path(self):
        self.assertIsNone(h.grid_path((0,0),(9,9),bytearray(100),10,10,maximum_visited=0))

    def test_own_corridor_avoids_foreign_blocked_cell(self):
        blocked=bytearray(25);blocked[2*5+2]=1
        path=h.grid_path((0,2),(4,2),blocked,5,5)
        self.assertEqual(path[0],(0,2));self.assertEqual(path[-1],(4,2));self.assertNotIn((2,2),path)

    def test_fragment_entry_cannot_borrow_an_adjacent_outline(self):
        poly=h.rectangle([1,1,2,2]);poly.Append(h.rectangle([2.5,1,3.5,2]))
        width,height=10,8;blocked=bytearray(width*height)
        for y in range(height):
            for x in range(width):
                if x<=4:blocked[y*width+x]=1
        self.assertIsNone(h.outline_point(poly,0,blocked,width,height))
        self.assertIsNotNone(h.outline_point(poly,1,blocked,width,height))

    def test_blocked_start_or_goal_cannot_return_a_partial_corridor(self):
        start=bytearray(25);start[0]=1
        goal=bytearray(25);goal[-1]=1
        self.assertIsNone(h.grid_path((0,0),(4,4),start,5,5))
        self.assertIsNone(h.grid_path((0,0),(4,4),goal,5,5))
        self.assertIsNone(h.grid_path((-1,0),(4,4),bytearray(25),5,5))

    def test_geometric_fragments_never_earn_continuous_reference_claim(self):
        self.assertFalse(h.spanning_complete([dict(failed_outlines=[],resulting_outline_count=2)]))
        self.assertFalse(h.spanning_complete([dict(failed_outlines=[{'outline':0}],resulting_outline_count=1)]))
        self.assertTrue(h.spanning_complete([dict(failed_outlines=[],resulting_outline_count=1)]))

    def test_backside_pad_never_seeds_top_adjacent_reference(self):
        pad=dict(copper_layers=['B.Cu'])
        self.assertFalse(h.pad_supports_reference(pad,'In1.Cu'))
        self.assertTrue(h.pad_supports_reference(pad,'In4.Cu'))
        self.assertTrue(h.pad_supports_reference(dict(copper_layers=['F.Cu']),'In1.Cu'))
        self.assertFalse(h.pad_supports_reference(dict(copper_layers=['F.Cu']),'In4.Cu'))

    def test_numbered_through_land_seeds_both_actual_adjacent_references(self):
        pad=dict(copper_layers=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu'])
        self.assertTrue(h.pad_supports_reference(pad,'In1.Cu'))
        self.assertTrue(h.pad_supports_reference(pad,'In4.Cu'))
        with self.assertRaises(ValueError):h.pad_supports_reference(pad,'In2.Cu')

    def test_fragment_entry_prefers_real_shared_free_region(self):
        poly=h.rectangle([1,1,4,3]);width,height=12,10;grid=bytearray(width*height)
        labels=[1]*(width*height)
        #Both entries are inside this polygon, but the first corner's free
        #component is tiny. It cannot justify an unproved global corridor.
        for y in range(height):
            for x in range(width):
                if x>=6:labels[y*width+x]=2
        x,y=h.outline_point(poly,0,grid,width,height,labels=labels,label_sizes={1:5,2:50})
        self.assertEqual(labels[y*width+x],2)

    def test_native_polygon_hole_survives_serialization(self):
        b=pcbnew.BOARD();b.SetCopperLayerCount(6);b.Add(pcbnew.NETINFO_ITEM(b,'/GROUND'))
        p=h.rectangle([0,0,10,10]);p.BooleanSubtract(h.rectangle([2,2,4,4]))
        h.add_zone(b,'/GROUND',p,pcbnew.In1_Cu,10,'BOUNDED_NATIVE_HOLE')
        with tempfile.TemporaryDirectory()as folder:
            path=Path(folder)/'hole.kicad_pcb';pcbnew.SaveBoard(str(path),b)
            fresh=pcbnew.LoadBoard(str(path));q=list(fresh.Zones())[0].Outline()
            self.assertEqual(q.HoleCount(0),1);self.assertAlmostEqual(q.Area()/1e12,96.)

    def test_exact_five_legacy_zone_correction_keeps_all_native_rules(self):
        b=pcbnew.LoadBoard(str(h.LEGACY_SOURCE));before={z.m_Uuid.AsString():(z.GetNetname(),z.GetLayer(),z.GetLocalClearance(),z.GetAssignedPriority(),z.GetPadConnection(),z.GetIslandRemovalMode())for z in b.Zones()}
        empty=pcbnew.SHAPE_POLY_SET()
        sides={layer:dict(regions={'/motherboard_do/FIELD_B_0V':h.rectangle([90,40,95,45])},barriers=empty,ungrounded=empty)for layer in ['In1.Cu','In4.Cu']}
        ledger,new=h.reconcile_legacy_zone_outlines(b,sides)
        self.assertEqual({r['uuid']for r in ledger},set(h.LEGACY_ZONES))
        for z in b.Zones():
            if z.m_Uuid.AsString()in before:
                self.assertEqual((z.GetNetname(),z.GetLayer(),z.GetLocalClearance(),z.GetAssignedPriority(),z.GetPadConnection(),z.GetIslandRemovalMode()),before[z.m_Uuid.AsString()])
                self.assertFalse(z.Outline().Contains(pcbnew.VECTOR2I(92000000,42000000)))
        self.assertTrue(all(r['changed_keys']==['polygon']for r in ledger))

    def test_changed_original_zone_net_cannot_receive_legacy_exception(self):
        b=pcbnew.LoadBoard(str(h.LEGACY_SOURCE));z=list(b.Zones())[0];z.SetNet(b.FindNet('/IO_3V3'))
        with self.assertRaises(ValueError):h.reconcile_legacy_zone_outlines(b,{})

    def test_unreviewed_old_outline_change_is_rejected(self):
        b=pcbnew.LoadBoard(str(h.LEGACY_SOURCE));z=list(b.Zones())[0]
        z.Outline().RemoveAllContours();z.Outline().Append(h.rectangle([1,1,5,5]))
        with self.assertRaises(ValueError):h.reconcile_legacy_zone_outlines(b,{})

    def test_power_plane_retains_empty_space_return_corridor_overlap(self):
        b=pcbnew.LoadBoard(str(h.LEGACY_SOURCE));empty=pcbnew.SHAPE_POLY_SET()
        side=dict(regions={'/motherboard_do/FIELD_B_0V':h.rectangle([90,40,110,45])},
            physical_regions={'/motherboard_do/FIELD_B_0V':h.rectangle([90,40,95,45])},
            barriers=empty,ungrounded=empty)
        h.reconcile_legacy_zone_outlines(b,{'In1.Cu':side,'In4.Cu':side})
        actual={z.m_Uuid.AsString():z for z in b.Zones()}
        physical=pcbnew.VECTOR2I(pcbnew.FromMM(92),pcbnew.FromMM(42))
        corridor=pcbnew.VECTOR2I(pcbnew.FromMM(105),pcbnew.FromMM(42))
        for uid,(net,layer)in h.LEGACY_ZONES.items():
            self.assertFalse(actual[uid].Outline().Contains(physical))
            self.assertEqual(actual[uid].Outline().Contains(corridor),net in ['/IO_3V3','/CORE_1V2'])

    def test_power_plane_never_bypasses_actual_all_layer_isolation_barrier(self):
        b=pcbnew.LoadBoard(str(h.LEGACY_SOURCE));empty=pcbnew.SHAPE_POLY_SET()
        side=dict(regions={},physical_regions={},barriers=h.rectangle([90,40,95,45]),ungrounded=empty)
        h.reconcile_legacy_zone_outlines(b,{'In1.Cu':side,'In4.Cu':side})
        for z in b.Zones():
            self.assertFalse(z.Outline().Contains(pcbnew.VECTOR2I(pcbnew.FromMM(92),pcbnew.FromMM(42))))

    def test_actual_front_field_metal_reserves_own_top_reference_between_pads(self):
        b=pcbnew.BOARD();b.SetCopperLayerCount(6);net='/motherboard_do/FIELD_B_0V';b.Add(pcbnew.NETINFO_ITEM(b,net))
        z=h.add_zone(b,net,h.rectangle([10,10,15,15]),pcbnew.F_Cu,10,'SOURCE_OWNED_FIELD_FIXTURE')
        z.SetFilledPolysList(pcbnew.F_Cu,h.rectangle([10,10,15,15]))
        m=dict(pads=[dict(reference='TEST_SOURCE',pin='1',domain='FIELD_B',net=net,copper_layers=['F.Cu'],copper_aabb_mm=[11,11,13,13])],barriers=[])
        front,_,_=h.build_side_polygons(m,b,'In1.Cu');back,_,_=h.build_side_polygons(m,b,'In4.Cu')
        p=pcbnew.VECTOR2I(pcbnew.FromMM(14.8),pcbnew.FromMM(14.8))
        self.assertTrue(front[net].Contains(p));self.assertNotIn(net,back)

    def test_actual_raw_ISOW_field_metal_never_creates_global_raw_return_pour(self):
        b=pcbnew.BOARD();b.SetCopperLayerCount(6);net='/motherboard_comms/RS485_ISO_RETURN_RAW';b.Add(pcbnew.NETINFO_ITEM(b,net))
        z=h.add_zone(b,net,h.rectangle([10,10,15,15]),pcbnew.F_Cu,10,'RAW_TEST_FIXTURE')
        z.SetFilledPolysList(pcbnew.F_Cu,h.rectangle([10,10,15,15]))
        m=dict(pads=[dict(reference='TEST_RAW',pin='1',domain='RS485',net=net,copper_layers=['F.Cu'],copper_aabb_mm=[11,11,13,13])],barriers=[])
        front,_,_=h.build_side_polygons(m,b,'In1.Cu');self.assertNotIn(net,front)


if __name__=='__main__':unittest.main()
