"""Literal five-source AO1 cell routing; original native guards decide adoption."""
from pathlib import Path
import sys,json,copy,math,heapq,shutil,time
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_prepare_dac_package_escape as neck
import hardware_route_owned_bypass_loops_wip_r03 as wip
import hardware_check_return_corridors_r04 as ret
from hardware_check_return_corridors import covered,circle
import hardware_route_critical_digital_wip_r05 as authority
import hardware_route_critical_digital_wip_r03 as clusters
from hardware_route_logic_return import identity,xy,mm,segment_distance,segment_hits_box
e=authority.engine
BASE=Path('reports/motherboard-return-zoning-20261001/source26-r61-AO1-DAC-return-r04/motherboard-AO1-DAC-return-candidate.kicad_pcb')
OUT=Path(sys.argv[1]);OUT.mkdir(exist_ok=False,parents=True)
review=json.loads(neck.critical.SOURCE_REVIEW.read_text());geom_review=json.loads(neck.critical.GEOMETRY_REVIEW.read_text())
b=pcbnew.LoadBoard(str(BASE));fps={f.GetReference():f for f in b.GetFootprints()}
old={t.m_Uuid.AsString():identity(t)for t in b.GetTracks()};source_before=clusters.source_clusters(b)
orig=e.parse(BASE.read_text());g=wip.Geometry(b);rows={};added=[];groups=[];failed=[]
check=ret.NativeCollectedAnnulusCheck(b,{})
fill=check.reference('/motherboard_analog_output/AO1_COM',b.GetLayerID('In1.Cu'))
def pad(ref,pin):return next(p for p in fps[ref].Pads()if p.GetNumber()==pin)
def conn(p,q):return q.m_Uuid.AsString()in{v.m_Uuid.AsString()for v in b.GetConnectivity().GetConnectedItems(p)}
def add(points,net,width):
 for s,z in zip(points,points[1:]):
  if math.dist(s,z)<1e-6:continue
  t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetLayer(pcbnew.F_Cu);t.SetStart(xy(s));t.SetEnd(xy(z));t.SetWidth(pcbnew.FromMM(width));b.Add(t);added.append(t);g.add(t)
def reference_segment(s,z,width):
 if '--geometry-only'in sys.argv:return True
 poly=e.corridor_polygon(tuple(xy(s)),tuple(xy(z)),pcbnew.FromMM(width/2+.4))
 return covered(poly,fill)
def clear_path(points,net,width):
 for s,z in zip(points,points[1:]):
  for p,box in g.pads.candidates(s,z,width/2+.25):
   if not p.IsOnLayer(pcbnew.F_Cu)or p.GetNetname()==net:continue
   if p.GetEffectiveShape(pcbnew.F_Cu).Collide(pcbnew.SEG(xy(s),xy(z)),pcbnew.FromMM(width/2+.2-1e-6)):return False
  for name,a,c,w in g.tracks[pcbnew.F_Cu].candidates(s,z,width/2+.5):
   if name!=net and segment_distance(s,z,a,c)<width/2+w/2+.2-1e-6:return False
  for zone in g.keepouts:
   if zone.IsOnLayer(pcbnew.F_Cu)and zone.GetDoNotAllowTracks():
    poly=e.corridor_polygon(tuple(xy(s)),tuple(xy(z)),pcbnew.FromMM(width/2));poly.BooleanIntersection(zone.Outline())
    if poly.Area():return False
  if not reference_segment(s,z,width):return False
 return True
def route(start,end,net):
 step=.125;lo=(375,236);hi=(424,258)
 def point(q):return(lo[0]+q[0]*step,lo[1]+q[1]*step)
 def index(p):return(round((p[0]-lo[0])/step),round((p[1]-lo[1])/step))
 def nearby(p):
  ix,iy=index(p);out=[]
  for dx in range(-6,7):
   for dy in range(-6,7):
    q=(ix+dx,iy+dy);v=point(q)
    if math.dist(v,p)<.78 and clear_path([p,v],net,.35):out.append(q)
  return out
 starts=nearby(start);ends=nearby(end);endset=set(ends)
 if not starts or not ends:return None,dict(reason='no SOURCE-side .35mm handoff',starts=len(starts),ends=len(ends))
 h=lambda q:math.dist(point(q),end);heap=[];cost={};parent={};valid={};maxq=index(hi)
 for q in starts:cost[q]=math.dist(point(q),start);parent[q]=None;heapq.heappush(heap,(cost[q]+h(q),cost[q],q))
 explored=0;edge_cache={}
 while heap:
  _,c,q=heapq.heappop(heap)
  if c!=cost.get(q):continue
  explored+=1
  if q in endset:
   chain=[]
   while q is not None:chain.append(point(q));q=parent[q]
   points=[start]+list(reversed(chain))+[end];result=[points[0]]
   for p in points[1:]:
    if math.dist(result[-1],p)>1e-6:result.append(p)
   simple=[result[0]];i=0
   while i<len(result)-1:
    j=len(result)-1
    while j>i+1 and not clear_path([result[i],result[j]],net,.35):j-=1
    simple.append(result[j]);i=j
   return simple,dict(explored=explored,grid_mm=step,path_mm=sum(math.dist(s,z)for s,z in zip(simple,simple[1:])))
  for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
   n=(q[0]+dx,q[1]+dy)
   if not 0<=n[0]<=maxq[0]or not 0<=n[1]<=maxq[1]:continue
   key=(q,n)if q<n else(n,q)
   if key not in edge_cache:edge_cache[key]=clear_path([point(q),point(n)],net,.35)
   if not edge_cache[key]:continue
   nc=c+step*math.hypot(dx,dy)
   if nc+1e-8<cost.get(n,float('inf')):cost[n]=nc;parent[n]=q;heapq.heappush(heap,(nc+h(n),nc,n))
 return None,dict(reason='no physical own-reference F path',explored=explored,grid_mm=step)
recipes={}
for pin in neck.PINS:
 p=pad('U14626',pin);name=p.GetNetname();rows[name]=copy.deepcopy(geom_review['nets'][name]);recipe=neck.recipe(p,'U14626',review)
 if '--extended-necks'in sys.argv and pin in {'2','3','8'}:
  tip=recipe['points_mm'][-1];direction=neck.PINS[pin][0];recipe['points_mm'].append([tip[0]+direction*.15,tip[1]]);recipe['length_mm']+=.15
  recipe['extension_mm']=.15;recipe['maximum_total_mm']=1.20;recipe['parent_authorized_bounded_correction']=True
 recipes[pin]=recipe
 if not clear_path(recipe['points_mm'],name,.2):failed.append(dict(net=name,reason='actual reviewed .20 neck clearance/reference obstructed'));continue
 add(recipe['points_mm'],name,.2)
order=['6','8','7','3','2'] if '--clock-first'in sys.argv else ['3','2','7','8','6']
for pin in order:
 p=pad('U14626',pin);name=p.GetNetname();row=copy.deepcopy(geom_review['nets'][name]);rows[name]=row
 recipe=recipes[pin];points=recipe['points_mm']
 if any(x['net']==name for x in failed):continue
 handoff=points[-1];sources=[pad(ref,num)for ref,num in row['source_pins']if ref!='U14626'];work=[]
 # Real source endpoints are joined one at a time to the actual DAC handoff.
 for source in sorted(sources,key=lambda v:math.dist(mm(v.GetPosition()),handoff)):
  b.BuildConnectivity()
  if conn(p,source):continue
  source_xy=mm(source.GetPosition());path,screen=route(handoff,source_xy,name)
  if path is None:work.append(dict(reference=source.GetParentFootprint().GetReference(),pin=source.GetNumber(),failed=screen));continue
  add(path,name,.35);work.append(dict(reference=source.GetParentFootprint().GetReference(),pin=source.GetNumber(),points_mm=path,screen=screen))
 groups.append(dict(net=name,neck=recipe,trunks=work))
 print(json.dumps(dict(net=name,trunks=len(work),failures=sum('failed'in x for x in work))),flush=True)
tree=copy.deepcopy(orig)
for t in added:
 tree.append(['segment',['start',str(pcbnew.ToMM(t.GetStart().x)),str(pcbnew.ToMM(t.GetStart().y))],['end',str(pcbnew.ToMM(t.GetEnd().x)),str(pcbnew.ToMM(t.GetEnd().y))],['width',str(pcbnew.ToMM(t.GetWidth()))],['layer','"F.Cu"'],['net',e.q(t.GetNetname())],['uuid',e.q(t.m_Uuid.AsString())]])
if e.immutable_objects(orig)!=e.immutable_objects(tree):raise ValueError('Actual source/land/zone geometry changed')
dest=OUT/'motherboard-AO1-five-digital-candidate.kicad_pcb';dest.write_text(authority.dump_native_board(tree)+'\n',encoding='utf8')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
for f in BASE.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
e.write(OUT/'search-receipt.json',dict(board_sha256=e.sha(BASE),source_design_sha256=e.sha('hardware/motherboard/design.json'),groups=groups,failed=failed,added_copper_uuids=[t.m_Uuid.AsString()for t in added],manufacturing_ready=False,passed=False,native_validation_pending=True))
