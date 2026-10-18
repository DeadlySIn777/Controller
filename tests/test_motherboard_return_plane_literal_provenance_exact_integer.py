"""Native positive operand provenance; true small islands stay physical."""
import unittest
import sys
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
try:
    import pcbnew
except ImportError:
    pcbnew=None


@unittest.skipIf(pcbnew is None,'Native KiCad geometry is required')
class ActualLiteralNativeCopperExactInteger(unittest.TestCase):
    def rectangle(self,x,y,w,h):
        from hardware_zone_motherboard_returns import rectangle
        return rectangle([x,y,x+w,y+h])

    def test_real_small_floating_island_remains_physical(self):
        from hardware_validate_motherboard_return_planes_r06 import positive_literal_contact
        actual=self.rectangle(1,1,.001,.001)
        self.assertIsNotNone(positive_literal_contact(actual,[({'zone_uuid':'actual-small'},actual)]))

    def test_synthetic_empty_space_never_gets_provenance(self):
        from hardware_validate_motherboard_return_planes_r06 import positive_literal_contact
        self.assertIsNone(positive_literal_contact(self.rectangle(2,2,.001,.001),[({'zone_uuid':'native'},self.rectangle(0,0,1,1))]))

    def test_only_boundary_touch_is_not_positive_copper_area(self):
        from hardware_validate_motherboard_return_planes_r06 import positive_literal_contact
        self.assertIsNone(positive_literal_contact(self.rectangle(1,0,1,1),[({'zone_uuid':'native'},self.rectangle(0,0,1,1))]))

    def test_positive_partial_overlap_records_literal_operand(self):
        from hardware_validate_motherboard_return_planes_r06 import positive_literal_contact
        witness=positive_literal_contact(self.rectangle(.5,.5,1,1),[({'zone_uuid':'actual'},self.rectangle(0,0,1,1))])
        self.assertEqual(witness['zone_uuid'],'actual')
        self.assertGreater(witness['actual_intersection_area_nm2'],0)

    def test_real_small_unanchored_resource_is_not_promoted(self):
        from hardware_validate_motherboard_return_planes_r06 import add_literal_provenance
        b=pcbnew.BOARD();layers=pcbnew.LSET();layers.AddLayer(pcbnew.F_Cu);layers.AddLayer(pcbnew.In1_Cu);layers.AddLayer(pcbnew.In2_Cu);layers.AddLayer(pcbnew.In3_Cu);layers.AddLayer(pcbnew.In4_Cu);layers.AddLayer(pcbnew.B_Cu);b.SetEnabledLayers(layers);b.SetCopperLayerCount(6)
        net=pcbnew.NETINFO_ITEM(b,'/LOGIC_GND');b.Add(net);z=pcbnew.ZONE(b);z.SetNet(net);z.SetLayer(pcbnew.In1_Cu)
        shape=self.rectangle(0,0,.01,.01)
        z.SetFilledPolysList(pcbnew.In1_Cu,shape);b.Add(z)
        original=dict(filled_components=[dict(net='/LOGIC_GND',reference_layer='In1.Cu',filled_piece=0,filled_area_mm2=.0001,passed=False)],unanchored_components=[],passed=False)
        review=add_literal_provenance(b,original)
        self.assertFalse(review['passed']);self.assertEqual(len(review['unanchored_components']),1);self.assertEqual(len(review['derived_nonphysical_computation_artifacts']),0)

    def test_real_native_15_square_nanometre_sliver_has_provenance(self):
        from hardware_validate_motherboard_return_planes_r06 import positive_literal_contact,exact_twice_area
        actual=pcbnew.SHAPE_POLY_SET();actual.NewOutline()
        for x,y in [(4277109,13584619),(4277112,13584628),(4277111,13584631),(4277107,13584613)]:actual.Append(x,y)
        self.assertEqual(exact_twice_area(actual),30)
        witness=positive_literal_contact(actual,[({'zone_uuid':'actual-literal-sliver'},actual)])
        self.assertGreater(witness['actual_intersection_twice_area_nm2'],0);self.assertLessEqual(witness['actual_intersection_twice_area_nm2'],30)

    def test_actual_native_slender_collision_false_does_not_hide_metal(self):
        from hardware_validate_motherboard_return_planes_r06 import positive_literal_contact,exact_twice_area
        actual=pcbnew.SHAPE_POLY_SET();actual.NewOutline()
        for x,y in [(345858111,183866218),(345865271,183867353),(345858101,183866217)]:actual.Append(x,y)
        self.assertEqual(exact_twice_area(actual),4190)
        self.assertFalse(actual.Collide(actual))
        witness=positive_literal_contact(actual,[({'zone_uuid':'actual-long-sliver'},actual)])
        self.assertEqual(witness['actual_intersection_twice_area_nm2'],4190)

    def test_exact_hole_subtraction_and_translated_area(self):
        from hardware_validate_motherboard_return_planes_r06 import exact_twice_area
        shape=pcbnew.SHAPE_POLY_SET();shape.NewOutline()
        for x,y in [(400000000,300000000),(400000100,300000000),(400000100,300000100),(400000000,300000100)]:shape.Append(x,y)
        shape.NewHole(0)
        for x,y in [(400000020,300000020),(400000080,300000020),(400000080,300000080),(400000020,300000080)]:shape.Append(x,y,0,0)
        self.assertEqual(exact_twice_area(shape),2*(10000-3600))

if __name__=='__main__':unittest.main()

