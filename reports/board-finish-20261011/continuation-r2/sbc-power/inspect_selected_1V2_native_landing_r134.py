"""Read-only source/landing hole and selected filled contour diagnostic."""
from pathlib import Path
import pickle,json,sys
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent;sys.path.insert(0,str(H/'field-power'))
import ordinary_routes as O
qs=pickle.loads((H/'sbc-power/frozen-regional-source-exit-replay-r129/accepted-source-scope/new-feed-zones.pkl').read_bytes());q=qs[0]
ng=json.loads((H/'core1v2-native-diagnostic-r132/scoped-native-fill/geometry.json').read_bytes());nq=next(x for x in ng['zones'] if x['uuid']==q['uuid']);s=q['zone_outline_shape'];parts=[s] if s.geom_type=='Polygon' else list(s.geoms)
native=unary_union(O.polys(nq['fills'].get('In4.Cu',[])));fl=json.loads((H/'core1v2-native-diagnostic-r132/scoped-native-fill/actual-via-flashes.json').read_bytes())['vias']
for uid in ('f6ad6a15-3a41-4605-9ad5-72f4ba7d5d92','13ace114-2da3-479c-9c70-bee7d15da004'):
 v=next(x for x in ng['vias'] if x['uuid']==uid);p=Point(v['at']);a=p.buffer(v['w']/2,quad_segs=64).difference(p.buffer(v['drill']/2,quad_segs=64))
 holes=[Polygon(r) for part in parts for r in part.interiors if Polygon(r).covers(p)]
 print(json.dumps({'via':uid,'at':v['at'],'native_actual_flashes':fl[uid],'proposed_outline_contains_center':s.covers(p),'explicit_hole_count_at_center':len(holes),'explicit_hole_areas_mm2':[h.area for h in holes],'proposed_annular_overlap_mm2':s.intersection(a).area,'native_filled_annular_overlap_mm2':native.intersection(a).area,'native_new_fill_distance_to_center_mm':native.distance(p),'native_new_fill_area_mm2':native.area}))
