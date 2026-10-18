"""Read-only literal Source pad/reference-void/DSN obstacle membership."""
from pathlib import Path
import sys,json,collections,hashlib
ROOT=Path.cwd();sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'reports/motherboard-ordinary-routing-20261001/isolated-native-geometry-deps-r01')]
import pcbnew,shapely
from shapely.geometry import Polygon,Point,LineString
from shapely.ops import unary_union
import hardware_route_selected_additive_r02 as e
R=ROOT/'reports/freerouting-evaluation-20261002'
PRE=R/'ROOT103-GPIO-config-visual-selected-DSN-r02'
OUT=R/'ROOT103-exact-endpoint-mask-review-r01';OUT.mkdir(exist_ok=False)
t=e.parse((PRE/'selected.dsn').read_text());native=e.parse((PRE/'native.dsn').read_text())
ks=e.children(e.child(t,'structure'),'keepout');native_count=len(e.children(e.child(native,'structure'),'keepout'))
prep=e.read(PRE/'prepare.json');selection=prep['selection'];filled=selection['actual_filled_copper_keepout_polygons_on_routable_layers']
boundaries=[];at=native_count+filled
for row in selection['actual_adjacent_reference_void_obstacles']:
 end=at+row['actual_reference_void_polygons'];boundaries.append((at,end,'actual_'+row['actual_reference_layer']+'_void',row['signal_layer']));at=end
def coords(raw):return[(float(raw[i])*1000,float(raw[i+1])*1000)for i in range(3,len(raw),2)]
def parts(g):
 if isinstance(g,Polygon):return[g]
 if hasattr(g,'geoms'):return[p for c in g.geoms for p in parts(c)]
 return[]
obs=[]
for i,k in enumerate(ks):
 raw=e.child(k,'polygon')
 if raw is None:continue
 g=Polygon(coords(raw),[coords(e.child(w,'polygon'))for w in e.children(k,'window')]);g=g if g.is_valid else unary_union(parts(shapely.make_valid(g,method='linework')))
 if g.is_empty:continue
 reason='native_package_rule_or_keepout' if i<native_count else 'actual_filled_foreign_or_power_copper' if i<native_count+filled else next(v[2]for v in boundaries if v[0]<=i<v[1])
 obs.append((i,e.value(raw[1]),g,reason))
b=pcbnew.LoadBoard(str(PRE/'base.kicad_pcb'));pads={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()}
m=e.read(PRE/'manifest.json');nets=['/motherboard_status/OBS8_INVERTED','/motherboard_status/OBS9_INVERTED','/motherboard_io_control/DOA_SLOT2'];rows=[]
for name in nets:
 for ref,pin in m['nets'][name]['source_pins']:
  p=pads[(ref,pin)];pt=p.GetPosition();f=p.GetParent();size=p.GetSize();xy=(pt.x,-pt.y)
  # A1.5mm straight outward ray is a diagnostic probe, not an accepted route.
  direction=-1 if pt.x<f.GetPosition().x else 1
  probe=LineString([xy,(xy[0]+direction*1_500_000,xy[1])]).buffer(250_000,cap_style='square',join_style='mitre')
  endpoint=dict(net=name,reference=ref,pin=pin,pad_uuid=str(p.m_Uuid),native_xy_mm=[pcbnew.ToMM(pt.x),pcbnew.ToMM(pt.y)],native_land_size_mm=[pcbnew.ToMM(size.x),pcbnew.ToMM(size.y)],DSN_xy_mm=[xy[0]/1e6,xy[1]/1e6],probed_F_escape_length_mm=1.5,trace_width_mm=.20,DSN_clearance_mm=.15,reference_guard_margin_mm=.10,DSN_effective_polygon_envelope_mm=.25,layers={})
  for layer in['F.Cu','In2.Cu','In3.Cu','B.Cu']:
   relevant=[(i,g,reason)for i,l,g,reason in obs if l==layer and g.bounds[0]<=probe.bounds[2]and g.bounds[2]>=probe.bounds[0]and g.bounds[1]<=probe.bounds[3]and g.bounds[3]>=probe.bounds[1]]
   hits=[dict(original_keepout_index=i,reason=reason,point_is_inside_or_on_boundary=g.covers(Point(xy)),distance_to_pad_center_mm=g.distance(Point(xy))/1e6,probe_overlap_mm2=g.intersection(probe).area/1e12,obstacle_bounds_mm=[v/1e6 for v in g.bounds])for i,g,reason in relevant if g.intersects(probe)]
   endpoint['layers'][layer]=hits
  rows.append(endpoint)
report=dict(passed=True,diagnostic_only=True,board_sha256=e.sha(PRE/'base.kicad_pcb'),selected_DSN_sha256=e.sha(PRE/'selected.dsn'),native_DSN_sha256=e.sha(PRE/'native.dsn'),native_keepout_count=native_count,filled_copper_count=filled,reference_void_index_ranges=boundaries,rows=rows,declared_candidates_are_existing_exact_Source_reviewed_nets=True,actual_route_or_reference_qualification=False,guards_unchanged=True)
e.write(OUT/'review.json',report)
print(json.dumps(dict(path=str(OUT/'review.json'),endpoints=[dict(net=r['net'],pin=[r['reference'],r['pin']],land=r['native_land_size_mm'],F_center_blockers=[v['reason']for v in r['layers']['F.Cu']if v['point_is_inside_or_on_boundary']],F_ray_blockers=[v['reason']for v in r['layers']['F.Cu']],In2_center_blockers=[v['reason']for v in r['layers']['In2.Cu']if v['point_is_inside_or_on_boundary']])for r in rows]),indent=2))
