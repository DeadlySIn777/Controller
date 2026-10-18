"""Finite actual F routing from ordinary112 with exact eligible native fills."""
from pathlib import Path
import sys,json,copy,math,shutil,heapq,time
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_ordinary_wip_r05 as o
import hardware_bind_ordinary_route_manifest_r03 as binder
import hardware_scope_anchored_reference_pieces as pieces
import hardware_route_critical_digital_wip_r05 as authority
import hardware_route_owned_bypass_loops_wip_r03 as w
from hardware_route_local_signals import paths
from hardware_route_logic_return import xy,mm,segment_distance
from hardware_check_return_corridors import covered
e=o.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-four-reference-closures-r71/motherboard-bounded-merged-candidate.kicad_pcb')
MAP=Path('reports/motherboard-domains-20261001/source26-r71-r01/domain-map.json')
FULL=BASE.parent/'actual-board-bound-reference-review.json'
OUT=Path(sys.argv[1]);OUT.mkdir(exist_ok=False,parents=True)
review=e.read(e.ROOT/o.SOURCE)
proof=pieces.qualify(FULL,MAP,BASE,{'/LOGIC_GND'},{'In1.Cu','In4.Cu'})
e.write(OUT/'piece-eligibility.json',proof)
m=binder.bind(BASE,OUT/'piece-eligibility.json',OUT/'manifest.json',set(review['nets']))
o.INPUT_BOARD=BASE;o.MAPPING=e.read(MAP)
b=pcbnew.LoadBoard(str(BASE));e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
checker=o.LiteralPieces(b,m['nets']);g=w.Geometry(b);fill=checker.reference('/LOGIC_GND',pcbnew.In1_Cu)
fullfill=fill;added=[];groups=[];blocked=[];already=[]

def clear(points,name,row):
 width=row['width_mm'];space=row['clearance_mm']
 for s,z in zip(points,points[1:]):
  seg=pcbnew.SEG(xy(s),xy(z))
  for p,box in g.pads.candidates(s,z,width/2+space+.1):
   if p.IsOnLayer(pcbnew.F_Cu) and p.GetNetname()!=name and p.GetEffectiveShape(pcbnew.F_Cu).Collide(seg,pcbnew.FromMM(width/2+space-1e-6)):return False
  for name2,a,c,width2 in g.tracks[pcbnew.F_Cu].candidates(s,z,width/2+.5):
   if name2!=name and segment_distance(s,z,a,c)<width/2+width2/2+space-1e-6:return False
  copper=e.corridor_polygon(tuple(xy(s)),tuple(xy(z)),pcbnew.FromMM(width/2))
  for zone in g.keepouts:
   if zone.IsOnLayer(pcbnew.F_Cu) and zone.GetDoNotAllowTracks():
    hit=pcbnew.SHAPE_POLY_SET();hit.Append(copper);hit.BooleanIntersection(zone.Outline())
    if hit.Area():return False
  projected=e.corridor_polygon(tuple(xy(s)),tuple(xy(z)),pcbnew.FromMM(width/2+row['reference_corridor_margin_mm']))
  if not covered(projected,fill):return False
 return True

def astar(start,end,name,row):
 step=.125;lo=(math.floor((min(start[0],end[0])-4)/step)*step,math.floor((min(start[1],end[1])-4)/step)*step)
 hi=(max(start[0],end[0])+4,max(start[1],end[1])+4)
 def point(q):return(lo[0]+q[0]*step,lo[1]+q[1]*step)
 def index(p):return(round((p[0]-lo[0])/step),round((p[1]-lo[1])/step))
 def nearby(p):
  ix,iy=index(p);out=[]
  for dx in range(-4,5):
   for dy in range(-4,5):
    q=(ix+dx,iy+dy);v=point(q)
    if math.dist(v,p)<.52 and clear([p,v],name,row):out.append(q)
  return out
 starts,ends=nearby(start),nearby(end)
 if not starts or not ends:return None,dict(reason='Actual SOURCE pad lacks native-clear own-reference .20mm handoff',start_choices=len(starts),end_choices=len(ends))
 heap=[];cost={};parent={};maxq=index(hi);endset=set(ends);cache={};explored=0;t0=time.monotonic()
 for q in starts:
  cost[q]=math.dist(point(q),start);parent[q]=None;heapq.heappush(heap,(cost[q]+math.dist(point(q),end),cost[q],q))
 while heap:
  _,c,q=heapq.heappop(heap)
  if c!=cost.get(q):continue
  explored+=1
  if q in endset:
   chain=[]
   while q is not None:chain.append(point(q));q=parent[q]
   raw=[start]+list(reversed(chain))+[end];raw=[v for i,v in enumerate(raw)if not i or math.dist(v,raw[i-1])>1e-6]
   simple=[raw[0]];i=0
   while i<len(raw)-1:
    j=len(raw)-1
    while j>i+1 and not clear([raw[i],raw[j]],name,row):j-=1
    simple.append(raw[j]);i=j
   if not clear(simple,name,row):raise ValueError('Final exact ordinary corridor screen failed')
   return simple,dict(explored=explored,grid_mm=step,path_mm=sum(math.dist(a,z)for a,z in zip(simple,simple[1:])))
  if explored>14000 or time.monotonic()-t0>75:return None,dict(reason='Finite native search budget exhausted',explored=explored)
  for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
   n=(q[0]+dx,q[1]+dy)
   if not 0<=n[0]<=maxq[0] or not 0<=n[1]<=maxq[1]:continue
   key=(q,n)if q<n else(n,q)
   if key not in cache:cache[key]=clear([point(q),point(n)],name,row)
   if not cache[key]:continue
   nc=c+step*math.hypot(dx,dy)
   if nc+1e-8<cost.get(n,float('inf')):cost[n]=nc;parent[n]=q;heapq.heappush(heap,(nc+math.dist(point(n),end),nc,n))
 return None,dict(reason='No bounded actual F path in eligible reference',explored=explored)

def peers(p):return{v.m_Uuid.AsString()for v in b.GetConnectivity().GetConnectedItems(p)}|{p.m_Uuid.AsString()}
def add(points,name,row):
 ids=[]
 for s,z in zip(points,points[1:]):
  if math.dist(s,z)<1e-6:continue
  t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(name));t.SetLayer(pcbnew.F_Cu);t.SetStart(xy(s));t.SetEnd(xy(z));t.SetWidth(pcbnew.FromMM(row['width_mm']));b.Add(t);added.append(t);g.add(t);ids.append(t.m_Uuid.AsString())
 return ids
padmap={}
for p in b.GetPads():
 if p.GetNetname()in m['nets']:padmap.setdefault(p.GetNetname(),[]).append(p)
jobs=[]
for name,row in m['nets'].items():
 ps=padmap[name]
 for i,p in enumerate(ps):
  for q in ps[i+1:]:
   dist=math.dist(mm(p.GetPosition()),mm(q.GetPosition()))
   if dist<=25 and p.IsOnLayer(pcbnew.F_Cu)and q.IsOnLayer(pcbnew.F_Cu):jobs.append((dist,name,p,q))
for _,name,p,q in sorted(jobs,key=lambda v:v[0]):
 b.BuildConnectivity()
 if q.m_Uuid.AsString()in peers(p):already.append(dict(net=name,pair=[p.m_Uuid.AsString(),q.m_Uuid.AsString()]));continue
 row=m['nets'][name];s,z=mm(p.GetPosition()),mm(q.GetPosition())
 fill=pcbnew.SHAPE_POLY_SET();fill.Append(fullfill)
 box=pcbnew.SHAPE_POLY_SET();box.NewOutline()
 bounds=(min(s[0],z[0])-4,min(s[1],z[1])-4,max(s[0],z[0])+4,max(s[1],z[1])+4)
 for x,y in((bounds[0],bounds[1]),(bounds[2],bounds[1]),(bounds[2],bounds[3]),(bounds[0],bounds[3])):box.Append(pcbnew.FromMM(x),pcbnew.FromMM(y))
 fill.BooleanIntersection(box);fill.Simplify()
 # This exact intersection only removes possible reference coverage. Final
 # segment/via proof uses the original complete eligible native fill union.
 path=next((pts for pts in paths(s,z)if clear(pts,name,row)),None);search=dict(method='finite literal direct paths')
 if path is None:path,search=astar(s,z,name,row)
 pair=[p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),q.GetParentFootprint().GetReference()+'.'+q.GetNumber()]
 if path is None:blocked.append(dict(net=name,source_pair=pair,span_mm=math.dist(s,z),search=search));print(json.dumps(dict(net=name,pair=pair,blocked=search)),flush=True);continue
 ids=add(path,name,row);groups.append(dict(net=name,source_pair=pair,source_pad_UUIDs=[p.m_Uuid.AsString(),q.m_Uuid.AsString()],points_mm=path,new_copper_UUIDs=ids,width_mm=row['width_mm'],clearance_mm=row['clearance_mm'],reference_corridor_margin_mm=row['reference_corridor_margin_mm'],search=search));print(json.dumps(dict(net=name,pair=pair,newCu=len(ids),search=search)),flush=True)
tree=e.parse(BASE.read_text());old=copy.deepcopy(tree)
for t in added:tree.append(['segment',['start',str(pcbnew.ToMM(t.GetStart().x)),str(pcbnew.ToMM(t.GetStart().y))],['end',str(pcbnew.ToMM(t.GetEnd().x)),str(pcbnew.ToMM(t.GetEnd().y))],['width',str(pcbnew.ToMM(t.GetWidth()))],['layer','"F.Cu"'],['net',e.q(t.GetNetname())],['uuid',e.q(t.m_Uuid.AsString())]])
if e.immutable_objects(old)!=e.immutable_objects(tree):raise ValueError('Authoritative source/lands/zone geometry changed')
dest=OUT/'motherboard-ordinary-local-candidate.kicad_pcb';dest.write_text(authority.dump_native_board(tree)+'\n',encoding='utf8')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
for f in BASE.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
e.write(OUT/'proposed-local-groups.json',dict(base_sha256=e.sha(BASE),manifest_sha256=e.sha(OUT/'manifest.json'),tool_sha256=e.sha(__file__),groups=groups,added_copper_UUIDs=[t.m_Uuid.AsString()for t in added],blocked=blocked,already_joined_pairs=already,maximum_considered_source_span_mm=25,exact_local_fill_clipping_margin_mm=4,local_clipping_only_removes_eligible_geometry=True,final_guard_uses_original_full_native_fill=True,only_exact_frozen112_source_nets=True,whole_board_reference_qualification=False,full_failed_reference_ledger=proof['complete_unanchored_components'],native_validation_pending=True,manufacturing_ready=False))
print(json.dumps(dict(actual_groups=len(groups),newCu=len(added),blocked=len(blocked))),flush=True)
