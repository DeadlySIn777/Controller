"""Check exact native fracture recovery for the interchange obstacle contours."""
from pathlib import Path
import sys,json,collections
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'));sys.path.insert(0,str(ROOT/'reports/motherboard-ordinary-routing-20261001/isolated-native-geometry-deps-r01'))
import pcbnew,shapely
from shapely.geometry import Polygon
from shapely.validation import explain_validity
import hardware_route_selected_additive_r02 as e
PRE=ROOT/'reports/freerouting-evaluation-20261002/ROOT103-GPIO-config-visual-selected-DSN-r02'
OUT=ROOT/'reports/freerouting-evaluation-20261002/DSN-native-unfracture-inspection-r01';assert not OUT.exists();OUT.mkdir(parents=True)
tree=e.parse((PRE/'selected.dsn').read_text(encoding='utf8'))
def pts(p):return[(round(float(p[i])*1000),round(float(p[i+1])*1000))for i in range(3,len(p),2)]
def points(c):return[(c.CPoint(i).x,c.CPoint(i).y)for i in range(c.PointCount())]
records=[];counts=collections.Counter();normalized={}
for index,k in enumerate(e.children(e.child(tree,'structure'),'keepout')):
 p=e.child(k,'polygon')
 if p is None:continue
 outer=pts(p);holes=[pts(e.child(w,'polygon'))for w in e.children(k,'window')];g=Polygon(outer,holes)
 if g.is_valid and g.area:continue
 native=pcbnew.SHAPE_POLY_SET();native.NewOutline()
 for x,y in outer:native.Append(x,y)
 for h in holes:
  hi=native.NewHole(0)
  for x,y in h:native.Append(x,y,0,hi)
 after=pcbnew.SHAPE_POLY_SET(native);after.Unfracture()
 missing=pcbnew.SHAPE_POLY_SET(native);missing.BooleanSubtract(after)
 added=pcbnew.SHAPE_POLY_SET(after);added.BooleanSubtract(native)
 polys=[Polygon(points(after.COutline(i)),[points(after.CHole(i,h))for h in range(after.HoleCount(i))])for i in range(after.OutlineCount())]
 rec=dict(index=index,layer=e.value(p[1]),before_vertices=len(outer),before_reason=explain_validity(g),after_outer_polygons=after.OutlineCount(),after_holes=sum(after.HoleCount(i)for i in range(after.OutlineCount())),after_valid=all(p.is_valid and p.area>0 for p in polys),after_reasons=[explain_validity(v)for v in polys if not v.is_valid or not v.area],native_missing_polygon_count=missing.OutlineCount(),native_added_polygon_count=added.OutlineCount(),native_missing_area_IU2=missing.Area(),native_added_area_IU2=added.Area())
 counts[(rec['after_valid'],rec['native_missing_polygon_count'],rec['native_added_polygon_count'])]+=1;records.append(rec)
 normalized[str(index)]=dict(layer=e.value(p[1]),polygons=[dict(outer_IU=points(after.COutline(i)),holes_IU=[points(after.CHole(i,h))for h in range(after.HoleCount(i))])for i in range(after.OutlineCount())])
e.write(OUT/'inspection.json',dict(input_sha256={str(PRE/'selected.dsn'):e.sha(PRE/'selected.dsn')},native_unfracture_only_copy=True,counts=[dict(after_valid=a,missing=m,added=n,count=c)for(a,m,n),c in counts.items()],records=records,native_board_changed=False))
e.write(OUT/'normalized-invalid-contours.json',normalized)
print(json.dumps(dict(records=len(records),counts=[dict(after_valid=a,missing=m,added=n,count=c)for(a,m,n),c in counts.items()],failed=records[:3])))
