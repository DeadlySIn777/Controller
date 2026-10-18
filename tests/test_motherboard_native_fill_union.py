"""Native exact-union equivalence, holes, layer/domain and no-fill negatives."""
import sys,unittest
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'tools'))
try:
    import pcbnew
    from hardware_collect_native_reference_fills import collect_native_reference_fills
    from hardware_zone_motherboard_returns import rectangle,duplicate,add_zone
except ModuleNotFoundError:pcbnew=None


@unittest.skipUnless(pcbnew,'Requires native KiCad geometry')
class NativeFillUnion(unittest.TestCase):
    def board(self):
        b=pcbnew.BOARD();b.SetCopperLayerCount(6)
        for n in ['LOGIC','FIELD']:b.Add(pcbnew.NETINFO_ITEM(b,n))
        return b

    def fill(self,b,shape,net='LOGIC',layer=None):
        layer=pcbnew.In1_Cu if layer is None else layer
        z=add_zone(b,net,shape,layer,10,'EXPLICIT_NATIVE_POLYGON_FIXTURE');z.SetFilledPolysList(layer,shape);z.SetIsFilled(True);return z

    def same_metal(self,actual,shapes):
        old=pcbnew.SHAPE_POLY_SET()
        for p in shapes:old.BooleanAdd(p)
        old.Simplify();extra=duplicate(actual);extra.BooleanSubtract(old);lost=duplicate(old);lost.BooleanSubtract(actual)
        self.assertEqual(extra.Area(),0);self.assertEqual(lost.Area(),0)
        self.assertEqual(actual.OutlineCount(),old.OutlineCount())

    def test_overlapping_same_return_is_exactly_the_old_native_union(self):
        b=self.board();shapes=[rectangle([1,1,4,4]),rectangle([3,1,6,4])]
        for p in shapes:self.fill(b,p)
        r=collect_native_reference_fills(b,{'LOGIC'},[pcbnew.In1_Cu]);self.same_metal(r['LOGIC',pcbnew.In1_Cu],shapes)

    def test_duplicate_native_same_return_does_not_cancel_metal(self):
        b=self.board();shape=rectangle([1,1,4,4]);self.fill(b,shape);self.fill(b,shape)
        r=collect_native_reference_fills(b,{'LOGIC'},[pcbnew.In1_Cu]);self.same_metal(r['LOGIC',pcbnew.In1_Cu],[shape,shape]);self.assertEqual(r['LOGIC',pcbnew.In1_Cu].Area()/1e12,9)

    def test_actual_hole_and_disconnected_interior_island_stay_exact(self):
        b=self.board();shape=rectangle([1,1,6,6]);shape.BooleanSubtract(rectangle([2,2,5,5]));island=rectangle([3,3,4,4]);self.fill(b,shape);self.fill(b,island)
        r=collect_native_reference_fills(b,{'LOGIC'},[pcbnew.In1_Cu]);self.same_metal(r['LOGIC',pcbnew.In1_Cu],[shape,island]);self.assertEqual(r['LOGIC',pcbnew.In1_Cu].OutlineCount(),2)

    def test_foreign_return_and_opposite_side_are_never_borrowed(self):
        b=self.board();shape=rectangle([1,1,4,4]);self.fill(b,shape,'FIELD');self.fill(b,shape,'LOGIC',pcbnew.In4_Cu)
        self.assertEqual(collect_native_reference_fills(b,{'LOGIC'},[pcbnew.In1_Cu]),{})

    def test_nonfilled_outline_cannot_invent_reference_metal(self):
        b=self.board();add_zone(b,'LOGIC',rectangle([1,1,4,4]),pcbnew.In1_Cu,10,'UNFILLED_NATIVE_FIXTURE')
        self.assertEqual(collect_native_reference_fills(b,{'LOGIC'},[pcbnew.In1_Cu]),{})

    def test_rule_area_never_becomes_return_copper(self):
        b=self.board();z=self.fill(b,rectangle([1,1,4,4]));z.SetIsRuleArea(True)
        self.assertEqual(collect_native_reference_fills(b,{'LOGIC'},[pcbnew.In1_Cu]),{})


if __name__=='__main__':unittest.main()
