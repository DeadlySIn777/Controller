"""Read-only conservative configuration-space diagnostic, never route proof."""
from pathlib import Path
import sys,json
ROOT=Path.cwd();sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'reports/motherboard-ordinary-routing-20261001/isolated-native-geometry-deps-r01')]
import pcbnew,shapely
from shapely.geometry import Polygon,Point,box
from shapely.ops import unary_union
import hardware_route_selected_additive_r02 as e
R=ROOT/'reports/freerouting-evaluation-20261002';PRE=R/'ROOT103-visual-local-window-DSN-r06';OUT=R/'ROOT103-local-F-configuration-space-r01';OUT.mkdir(exist_ok=False)
t=e.parse((PRE/'selected.dsn').read_text());b=pcbnew.LoadBoard(str(PRE/'base.kicad_pcb'));m=e.read(PRE/'manifest.json')
window=box(300_000_000,120_000_000,330_000_000,150_000_000);margin=250_000
def parts(g):
 if isinstance(g,Polygon):return[g]
 if hasattr(g,'geoms'):return[p for c in g.geoms for p in parts(c)]
 return[]
def geom(poly):
 result=[]
 def points(chain):return[(chain.CPoint(i).x,chain.CPoint(i).y)for i in range(chain.PointCount())]
 for i in range(poly.OutlineCount()):result.append(Polygon(points(poly.COutline(i)),[points(poly.CHole(i,j))for j in range(poly.HoleCount(i))]))
 return unary_union(result)
obstacles=[]
for k in e.children(e.child(t,'structure'),'keepout'):
 raw=e.child(k,'polygon')
 if raw is None or e.value(raw[1])!='F.Cu':continue
 coords=lambda r:[(round(float(r[i])*1000),-round(float(r[i+1])*1000))for i in range(3,len(r),2)]
 g=Polygon(coords(raw),[coords(e.child(w,'polygon'))for w in e.children(k,'window')])
 if g.intersects(window):obstacles.append(g.buffer(margin+1000,quad_segs=32,join_style='round'))
fixed=unary_union(obstacles);pads={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()};rows=[]
for name,row in m['nets'].items():
 metal=[];identities=[]
 for p in b.GetPads():
  if p.GetNetname()==name or not p.IsOnLayer(pcbnew.F_Cu):continue
  bb=p.GetBoundingBox();region=box(bb.GetLeft()-margin,bb.GetTop()-margin,bb.GetRight()+margin,bb.GetBottom()+margin)
  if not region.intersects(window):continue
  poly=pcbnew.SHAPE_POLY_SET();p.TransformShapeToPolygon(poly,pcbnew.F_Cu,margin,1000,pcbnew.ERROR_OUTSIDE)
  g=geom(poly)
  if g.intersects(window):metal.append(g);identities.append(dict(kind='pad',uuid=str(p.m_Uuid),reference=p.GetParent().GetReference(),pin=p.GetNumber(),net=p.GetNetname()))
 for v in b.GetTracks():
  if v.GetNetname()==name or not v.IsOnLayer(pcbnew.F_Cu):continue
  bb=v.GetBoundingBox();region=box(bb.GetLeft()-margin,bb.GetTop()-margin,bb.GetRight()+margin,bb.GetBottom()+margin)
  if not region.intersects(window):continue
  poly=pcbnew.SHAPE_POLY_SET();v.TransformShapeToPolygon(poly,pcbnew.F_Cu,margin,1000,pcbnew.ERROR_OUTSIDE)
  g=geom(poly)
  if g.intersects(window):metal.append(g);identities.append(dict(kind='track_or_via',uuid=str(v.m_Uuid),net=v.GetNetname()))
 blocked=unary_union([fixed,*metal]);free=window.buffer(-margin).difference(blocked);pieces=parts(free);eps=[]
 for ref,pin in row['source_pins']:
  pad=pads[(ref,pin)];p=pad.GetPosition();point=Point(p.x,p.y);owners=[i for i,g in enumerate(pieces)if g.covers(point)]
  eps.append(dict(reference=ref,pin=pin,xy_mm=[p.x/1e6,p.y/1e6],free_components=owners,blocked_by_DSN_polygon_or_void=fixed.covers(point),blocked_by_native_foreign_metal=unary_union(metal).covers(point)))
 common=set(eps[0]['free_components'])
 for ep in eps[1:]:common.intersection_update(ep['free_components'])
 rows.append(dict(net=name,endpoints=eps,conservative_F_free_component_count=len(pieces),common_endpoint_components=sorted(common),common_component_bounds_mm=[[v/1e6 for v in pieces[i].bounds]for i in common],native_foreign_metal_count=len(metal),native_foreign_metal_identities=identities,actual_accepted_route=False))
e.write(OUT/'review.json',dict(passed=True,diagnostic_only=True,source_board_sha256=e.sha(PRE/'base.kicad_pcb'),selected_DSN_sha256=e.sha(PRE/'selected.dsn'),trace_width_mm=.20,clearance_mm=.15,configuration_space_radius_mm=.25,conservative_native_polygon_max_error_mm=.001,DSN_round_buffer_extra_mm=.001,raw_pad_center_coverage_not_an_escape_or_route_proof=True,rows=rows,no_source_or_board_writes=True))
print(json.dumps(rows,indent=2)[:6000])
