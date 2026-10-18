"""Independent GEOS intersection of literal native integer-coordinate contours."""
from pathlib import Path
import sys,json,hashlib
p=Path(__file__).parent
sys.path[:0]=[str(p/'isolated-native-geometry-deps-r01'),str(p),str(Path('tools').resolve())]
import pcbnew,shapely
from shapely.geometry import Polygon
from shapely.ops import unary_union
import check_io3_backbone_preservation_r02 as h
from hardware_collect_native_reference_fills import collect_native_reference_fills
def geos(poly):
 def ring(chain):return [(chain.CPoint(i).x,chain.CPoint(i).y)for i in range(chain.PointCount())]
 polys=[Polygon(ring(poly.COutline(i)),[ring(poly.CHole(i,j))for j in range(poly.HoleCount(i))])for i in range(poly.OutlineCount())]
 assert all(q.is_valid for q in polys), 'Do not silently repair invalid native contours'
 return unary_union(polys)
base=Path('reports/motherboard-pcb-integration-20261001/source26-C19042-local-bypass-r81/motherboard-bounded-merged-candidate.kicad_pcb')
out=p/'actual-source26-root81-OUT-PERMIT-r06'
paths=[base,out/'motherboard-OUT-PERMIT-common-In1-candidate.kicad_pcb']
boards=[pcbnew.LoadBoard(str(x))for x in paths]
fills=[collect_native_reference_fills(x,{'/IO_3V3'},[pcbnew.In2_Cu])['/IO_3V3',pcbnew.In2_Cu]for x in boards]
b,a=fills
er=h.duplicate(b);er.Deflate(pcbnew.FromMM(.501),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001))
opened=h.duplicate(er);opened.Inflate(pcbnew.FromMM(.501),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened.BooleanIntersection(b)
gb,ga,go=map(geos,[b,a,opened])
gn=gb.difference(go);removed=gb.difference(ga);hit=removed.intersection(gn)
literal=[]
for board in boards:
 pieces=[geos(z.GetFilledPolysList(pcbnew.In2_Cu))for z in board.Zones()if not z.GetIsRuleArea()and z.GetNetname()=='/IO_3V3'and z.HasFilledPolysForLayer(pcbnew.In2_Cu)and z.GetFilledPolysList(pcbnew.In2_Cu).OutlineCount()]
 literal.append(unary_union(pieces))
report=dict(input_sha256={str(x):h.sha(x)for x in paths},shapely_version=shapely.__version__,GEOS_version=shapely.geos_version_string,
 geometry_is_literal_native_integer_coordinates=True,no_native_contour_repair=True,no_geometry_area_exemption=True,
 union_before_difference_area_nm2=gb.symmetric_difference(literal[0]).area,union_after_difference_area_nm2=ga.symmetric_difference(literal[1]).area,
 exact_native_union_removed_area_mm2=removed.area/1e12,exact_cut_of_narrow_native_union_mm2=hit.area/1e12,
 exact_cut_wkt=hit.wkt,narrow_2nm_containment_escape_area_mm2=gn.difference(ga.buffer(2,quad_segs=32)).area/1e12,
 literal_raw_fill_narrow_cut_mm2=literal[0].difference(go).intersection(literal[0].difference(literal[1])).area/1e12,
 literal_raw_fill_narrow2nm_escape_mm2=literal[0].difference(go).difference(literal[1].buffer(2,quad_segs=32)).area/1e12)
(out/'independent-exact-native-geometry-r03.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
