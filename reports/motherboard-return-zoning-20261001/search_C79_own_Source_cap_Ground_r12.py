from pathlib import Path
import sys,json,math
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import native,classify,positioned,sha,write
from hardware_route_logic_return import xy,mm,distance,segment_hits_box
from hardware_route_owned_bypass_loops import Geometry
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_route_selected_additive import corridor_polygon
from hardware_zone_motherboard_returns import functional_barrier
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-facing-health-C80-dedicated-feed-r08/motherboard-facing-health-C80-dedicated-feed-candidate.kicad_pcb');O=Path('reports/motherboard-return-zoning-20261001/ROOT101-C79-actual-own-Source-Ground-search-r12');assert not O.exists();O.mkdir();S=Path('hardware/motherboard')
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();parts={r:c for r,c in json.loads((S/'design.json').read_text())['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')};nodes,nc,fn=native(S/'netlist.xml');ds,bar,_,_=classify(parts,nodes,nc);mp=positioned(b,parts,nodes,nc,fn,ds,bar);assert not mp['errors'];guard=ReferenceGuard(b,mp);geom=Geometry(b);pads={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()};pad=pads['C11079','2'];ret=pad.GetNetname();assert ret=='/LOGIC_GND';pt=mm(pad.GetPosition());box=pcbnew.BOX2I(xy((336.,172.5)),xy((5.,4.5)));geom.keepouts=[q for q in geom.keepouts if q.Outline().BBox().Intersects(box)];geom.holes=[q for q in geom.holes if box.Contains(xy(q[0]))];rows=[];failed={}
def legal(shape,l):
 bb=shape.BBox();bounds=[pcbnew.ToMM(x)for x in(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())]
 for other,project in guard.indices[l].candidates(tuple(bounds[:2]),tuple(bounds[2:]),.3):
  if other==ret:continue
  hit=pcbnew.SHAPE_POLY_SET(shape);hit.BooleanIntersection(project)
  if hit.OutlineCount():return False
 for br in mp['barriers']:
  hit=pcbnew.SHAPE_POLY_SET(shape);hit.BooleanIntersection(functional_barrier(br))
  if hit.OutlineCount():return False
 return True
def registered_ground_via(point,net):
 if not .75<point[0]<459.25 or not .75<point[1]<339.25:return False
 for p,box in geom.pads.candidates(point,point,.51):
  if p.GetAttribute()==pcbnew.PAD_ATTRIB_SMD and p.GetNetname()==net:
   for layer in(pcbnew.F_Cu,pcbnew.B_Cu):
    if p.IsOnLayer(layer)and p.GetEffectiveShape(layer).Collide(pcbnew.SHAPE_CIRCLE(xy(point),pcbnew.FromMM(.25)),0):return False
  elif segment_hits_box(point,point,box,.40):return False
 for zone in geom.keepouts:
  if zone.GetDoNotAllowVias():
   hit=corridor_polygon(tuple(xy(point)),tuple(xy(point)),pcbnew.FromMM(.25));hit.BooleanIntersection(zone.Outline())
   if hit.OutlineCount():return False
 for index in geom.tracks.values():
  for name,start,end,width in index.candidates(point,point,.51):
   if name!=net and distance(point,start,end)<.25+width/2+.205-1e-6:return False
 return not any(math.dist(point,q)<.1+d/2+.25-1e-6 for q,d in geom.holes)
points=[(round(336.4+i*.05,6),round(172.2+j*.05,6))for i in range(75)for j in range(67)]
for q in points:
 if math.dist(pt,q)>2 or not registered_ground_via(q,ret):failed['native_via']=failed.get('native_via',0)+1;continue
 path=[pt,q]
 if not geom.clear(path,ret,pcbnew.B_Cu,.25):failed['native_cap_escape']=failed.get('native_cap_escape',0)+1;continue
 shape=corridor_polygon(tuple(xy(q)),tuple(xy(q)),pcbnew.FromMM(.35))
 if not all(legal(shape,l)for l in(pcbnew.In1_Cu,pcbnew.In4_Cu)):failed['actual_foreign_Source_annulus']=failed.get('actual_foreign_Source_annulus',0)+1;continue
 rows.append(dict(Ground_mm=q,cap_return_mm=pt,short_cap_branch_mm=path,distance_mm=math.dist(pt,q),both_actual_Source_domain_annulus_screens_passed=True))
rows.sort(key=lambda r:r['distance_mm']);write(O/'search.json',dict(passed=bool(rows),board_sha256=sha(B),actual_C79_Source_return='C11079.2',return_net=ret,candidates=rows,failed_counts=failed));print(json.dumps(dict(candidates=rows[:10],count=len(rows),failed=failed)),flush=True)


