import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"tools"))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import split_polygons
bp=Path("reports/motherboard-pcb-integration-20261001/source26-digital-bias-returns-adopted-r73/motherboard-source26-WIP.kicad_pcb")
rp=Path("reports/motherboard-return-zoning-20261001/source26-r73-positive-literal-native-resource-review-r01.json")
op=Path("reports/motherboard-return-zoning-20261001/source26-r73-exact-integer-micro-review-r01.json")
if op.exists():raise ValueError("fresh evidence required")
def chain_twice_area(chain):
    pts=[(chain.CPoint(i).x,chain.CPoint(i).y)for i in range(chain.PointCount())]
    return sum(x*y2-y*x2 for(x,y),(x2,y2)in zip(pts,pts[1:]+pts[:1]))
def exact_twice_area(shape):
    return sum(abs(chain_twice_area(shape.COutline(i)))-sum(abs(chain_twice_area(shape.CHole(i,j)))for j in range(shape.HoleCount(i)))for i in range(shape.OutlineCount()))
b=pcbnew.LoadBoard(str(bp));report=json.loads(rp.read_text());net="/mc_power_watchdog_permission/LOGIC_GND"
# Bind by literal resource rows rather than a presumed return-name alias.
rows=[r for r in report["unanchored_components"]if r["filled_area_mm2"]<.000001]+report["derived_nonphysical_computation_artifacts"]
nets={r["net"]for r in rows};fills=collect_native_reference_fills(b,nets,[pcbnew.In1_Cu,pcbnew.In4_Cu]);pieces={k:list(split_polygons(v))for k,v in fills.items()}
out=[]
for row in rows:
    layer=b.GetLayerID(row["reference_layer"]);micro=pieces[row["net"],layer][row["filled_piece"]];bounds=micro.BBox();contacts=[]
    for z in b.Zones():
        if z.GetIsRuleArea()or z.GetNetname()!=row["net"]or not z.IsOnLayer(layer):continue
        for ix,actual in enumerate(split_polygons(z.GetFilledPolysList(layer))):
            if not bounds.Intersects(actual.BBox()):continue
            cut=pcbnew.SHAPE_POLY_SET();cut.Append(micro);cut.BooleanIntersection(actual)
            contacts.append(dict(zone_uuid=z.m_Uuid.AsString(),literal_filled_piece=ix,native_double_intersection_area_nm2=cut.Area(),exact_integer_intersection_twice_area_nm2=exact_twice_area(cut),exact_integer_literal_twice_area_nm2=exact_twice_area(actual)))
    out.append(dict(net=row["net"],layer=row["reference_layer"],piece=row["filled_piece"],native_double_area_nm2=micro.Area(),exact_integer_twice_area_nm2=exact_twice_area(micro),bounds_nm=[bounds.GetX(),bounds.GetY(),bounds.GetRight(),bounds.GetBottom()],contours=[[(micro.COutline(i).CPoint(j).x,micro.COutline(i).CPoint(j).y)for j in range(micro.COutline(i).PointCount())]for i in range(micro.OutlineCount())],literal_intersections=contacts))
    print(row["reference_layer"],row["filled_piece"],micro.Area(),exact_twice_area(micro),[(r["native_double_intersection_area_nm2"],r["exact_integer_intersection_twice_area_nm2"])for r in contacts],flush=True)
write(op,dict(board_sha256=sha(bp),resource_report_sha256=sha(rp),rows=out,arithmetic="Unbounded Python integer shoelace; absolute outer contours minus absolute holes; no area tolerance",read_only=True,route_coverage_authorization=False))
