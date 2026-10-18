from pathlib import Path
import sys,json,re
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_zone_motherboard_returns import rectangle
from hardware_validate_motherboard_return_planes_r06 import exact_twice_area
influence=Path('reports/motherboard-return-zoning-20261001/IO3-literal-tip-cleanup-independent-r07/exact-physical-cleanup-influence.json')
loss=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-IO3-tip-trial-r85/rejected-power-cut-location.json')
out=Path('reports/motherboard-return-zoning-20261001/ROOT85-crescent-qualified-cleanup-membership-r01.json')
if out.exists():raise ValueError('Fresh immutable membership proof required')
d=json.loads(influence.read_text());region=rectangle(d['nominal_rule_bounds_mm'])
def poly(text):
 p=pcbnew.SHAPE_POLY_SET();p.NewOutline()
 for x,y in re.findall(r'VECTOR2I\(\s*(-?\d+),\s*(-?\d+)\)',text):p.Append(int(x),int(y))
 return p
for r in d['exact_three_native_local_smoothing_contours']:region.BooleanAdd(poly(r['native_polygon']))
data=json.loads(loss.read_text());rows=data.get('rejected_native_power_cut_components',data.get('rows'))
if rows is None:raise ValueError('Exact root loss schema must be inspected')
result=[]
for r in rows:
 p=poly(r['native_polygon']);outside=pcbnew.SHAPE_POLY_SET();outside.Append(p);outside.BooleanSubtract(region)
 result.append(dict(exact_loss_twice_area_nm2=exact_twice_area(p),outside_exact_twice_area_nm2=exact_twice_area(outside),outside_native_polygon=outside.Format(False),inside_exact_qualified_union=outside.OutlineCount()==0 and exact_twice_area(outside)==0))
write(out,dict(read_only=True,input_sha256={str(p):sha(p)for p in(influence,loss,Path(__file__))},rows=result,all_inside_exact_union=all(r['inside_exact_qualified_union']for r in result),no_new_region_or_tolerance=True,composed_actual_Source44_feed22_topology_and_core_proof_still_required=True))
print(json.dumps(result,indent=2))
