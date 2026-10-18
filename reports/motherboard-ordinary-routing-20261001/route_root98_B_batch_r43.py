"""Bounded real B-only adjacent-In4-reference routing trial on the frozen ordinary112 scope.

Emit additive native copper only. No acceptance until native refill/DRC,
SOURCE clustering, full literal return-annulus checks and cut controls pass.
"""
from pathlib import Path
import sys,json,math,copy,shutil,itertools,time,heapq
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_zone_motherboard_returns as zoneutils
import hardware_route_ordinary_wip_r05 as ordinary
import hardware_bind_ordinary_route_manifest_r03 as binder
import hardware_scope_anchored_reference_pieces as pieces
import hardware_route_critical_digital_wip_r05 as authority
from hardware_route_owned_bypass_loops_wip_r03 import Geometry
from hardware_route_local_signals import paths
from hardware_route_logic_return import xy,mm,distance,segment_distance,segment_hits_box
from hardware_check_return_corridors import covered,circle,corridor_polygon
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
e=ordinary.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U19-merged-trial-r98/motherboard-bounded-merged-candidate.kicad_pcb')
MAP=Path('reports/motherboard-domains-20261001/source26-r98-r01/domain-map.json')
OUT=Path(sys.argv[1]);OUT.mkdir(parents=True,exist_ok=False)
frozen={str(p):e.sha(p)for p in(BASE,MAP,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'),Path(__file__))}
review=e.read(e.ROOT/ordinary.SOURCE)
proof=pieces.qualify(BASE.parent/'literal-reference-resources.json',MAP,BASE,{'/LOGIC_GND'},{'In1.Cu','In4.Cu'})
e.write(OUT/'piece-eligibility.json',proof)
m=binder.bind(BASE,OUT/'piece-eligibility.json',OUT/'manifest.json',set(review['nets']))
ordinary.INPUT_BOARD=BASE;ordinary.MAPPING=e.read(MAP)
ordinary.frozen_review_check(m,Path('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity()
e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
check=ordinary.LiteralPieces(b,m['nets']);geo=Geometry(b)
fills={l:check.reference('/LOGIC_GND',r)for l,r in((pcbnew.B_Cu,pcbnew.In4_Cu),)}
ps={p.m_Uuid.AsString():p for p in b.GetPads()}
existing_ground=[t for t in b.GetTracks()if t.Type()==pcbnew.PCB_VIA_T and t.GetNetname()=='/LOGIC_GND' and all(physical_reference_contact(t,l,b.GetConnectivity())for l in(pcbnew.In1_Cu,))]
full_fills=fills;added=[];groups=[];blocked=[]
# CORE_1V2 remains an absolute filled-copper obstacle. The bounded IO3
# hole/slot must separately pass exact post-refill topology/feed screening.
# No candidate is eligible from this search alone.
power_fills={l:pcbnew.SHAPE_POLY_SET()for l in(pcbnew.In3_Cu,)}
for z in b.Zones():
    if not z.GetIsRuleArea()and z.GetLayer()in power_fills:
        power_fills[z.GetLayer()].BooleanAdd(z.GetFilledPolysList(z.GetLayer()))
for poly in power_fills.values():poly.Simplify()


def clear(points,name,layer,width=.2,clearance=.20):
    for a,z in zip(points,points[1:]):
        seg=pcbnew.SEG(xy(a),xy(z))
        for p,_ in geo.pads.candidates(a,z,width/2+clearance+.1):
            if p.IsOnLayer(layer)and p.GetNetname()!=name and p.GetEffectiveShape(layer).Collide(seg,pcbnew.FromMM(width/2+clearance-1e-6)):return False
        for other,p,q,w in geo.tracks[layer].candidates(a,z,width/2+.5):
            if other!=name and segment_distance(a,z,p,q)<width/2+w/2+clearance-1e-6:return False
        cu=corridor_polygon(tuple(xy(a)),tuple(xy(z)),pcbnew.FromMM(width/2))
        for zone in geo.keepouts:
            if zone.IsOnLayer(layer)and zone.GetDoNotAllowTracks():
                hit=pcbnew.SHAPE_POLY_SET();hit.Append(cu);hit.BooleanIntersection(zone.Outline())
                if hit.OutlineCount():return False
        if layer in power_fills:
            hit=corridor_polygon(tuple(xy(a)),tuple(xy(z)),pcbnew.FromMM(width/2+clearance))
            hit.BooleanIntersection(power_fills[layer])
            if hit.OutlineCount():return False
        if not covered(corridor_polygon(tuple(xy(a)),tuple(xy(z)),pcbnew.FromMM(width/2+.10)),fills[layer]):return False
    return True

def via_clear(pt,name,diameter,drill):
    radius=diameter/2
    if not .8+radius<pt[0]<459.2-radius or not .8+radius<pt[1]<339.2-radius:return False
    for p,box in geo.pads.candidates(pt,pt,radius+.25):
        if segment_hits_box(pt,pt,box,radius+.20):return False
    for zone in geo.keepouts:
        if zone.GetDoNotAllowVias():
            hit=circle(tuple(xy(pt)),pcbnew.FromMM(radius));hit.BooleanIntersection(zone.Outline())
            if hit.OutlineCount():return False
    for power_poly in power_fills.values():
        hit=circle(tuple(xy(pt)),pcbnew.FromMM(radius+.205));hit.BooleanIntersection(power_poly)
        if hit.OutlineCount():return False
    for index in geo.tracks.values():
        for other,a,z,w in index.candidates(pt,pt,radius+.55):
            if other!=name and distance(pt,a,z)<radius+w/2+.205-1e-6:return False
    return not any(math.dist(pt,q)<drill/2+d/2+.25-1e-6 for q,d in geo.holes)

def ground_at(pt):
    for v in existing_ground:
        d=math.dist(pt,mm(v.GetPosition()))
        if .8<=d<=1 and all(covered(circle(tuple(v.GetPosition()),pcbnew.FromMM(.24)),fill)for fill in fills.values()):
            return dict(existing_uuid=v.m_Uuid.AsString(),position=mm(v.GetPosition()))
    for radius in(.8,.9,1.):
        for i in range(8):
            p=(round(pt[0]+radius*math.cos(i*math.pi/4),6),round(pt[1]+radius*math.sin(i*math.pi/4),6))
            if via_clear(p,'/LOGIC_GND',.5,.2)and all(covered(circle(tuple(xy(p)),pcbnew.FromMM(.26)),fill)for fill in fills.values()):return dict(new_position=p)
    return None

def escapes(p,row):
    center=mm(p.GetPosition());name=p.GetNetname();result=[];stages=dict(candidates=0,via_clear=0,front_path=0,reference_circle=0,ground=0)
    # Radius includes exact manifest .60 via, maximum actual pour clearance,
    # .02 discretization allowance, and the full .20 outer return annulus.
    radius=.3+max(check.zone_clearance['/LOGIC_GND',l]for l in(pcbnew.In1_Cu,))/1e6+.02+.20
    for d in(.75,1.,1.25,1.5,2.,2.5,3.):
        for i in range(16):
            pt=(round(center[0]+d*math.cos(i*math.pi/8),6),round(center[1]+d*math.sin(i*math.pi/8),6))
            stages['candidates']+=1
            if not via_clear(pt,name,.6,.3):continue
            stages['via_clear']+=1
            front=next((path for path in paths(center,pt)if sum(math.dist(a,z)for a,z in zip(path,path[1:]))<=4.5 and clear(path,name,pcbnew.B_Cu)),None)
            if front is None:continue
            stages['front_path']+=1
            if not all(covered(circle(tuple(xy(pt)),pcbnew.FromMM(radius)),fill)for fill in fills.values()):continue
            stages['reference_circle']+=1
            ground=ground_at(pt)
            if ground:stages['ground']+=1;result.append(dict(position=pt,ground=ground,front_path_mm=front))
            if len(result)>=8:return result
    print(json.dumps(dict(escape_pad=p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),stages=stages)),flush=True)
    return result

def add_segment(a,z,name,layer):
    if math.dist(a,z)<1e-6:return None
    t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(name));t.SetLayer(layer);t.SetStart(xy(a));t.SetEnd(xy(z));t.SetWidth(pcbnew.FromMM(.2));b.Add(t);added.append(t);geo.add(t);return t.m_Uuid.AsString()

def add_via(pt,name,diameter,drill):
    t=pcbnew.PCB_VIA(b);t.SetNet(b.FindNet(name));t.SetPosition(xy(pt));t.SetWidth(pcbnew.FromMM(diameter));t.SetDrill(pcbnew.FromMM(drill));t.SetViaType(pcbnew.VIATYPE_THROUGH);t.SetLayerPair(pcbnew.B_Cu,pcbnew.B_Cu);b.Add(t);added.append(t);geo.add(t);return t.m_Uuid.AsString()

def path(start,end,layer,width=.20,space=.20):
 original=fills[layer]
 clipped=zoneutils.duplicate(original)
 clipped.BooleanIntersection(zoneutils.rectangle((min(start[0],end[0])-15,min(start[1],end[1])-15,max(start[0],end[0])+15,max(start[1],end[1])+15),0))
 clipped.Simplify()
 # A native Boolean intersection only removes the outside reference. Every
 # local segment is still checked against the exact SOURCE-eligible fill.
 added=zoneutils.duplicate(clipped);added.BooleanSubtract(original)
 if added.Area()!=0:raise ValueError('Clipped local reference added area')
 fills[layer]=clipped
 for points in paths(start,end):
  if clear(points,name,layer,width,space):return points
 # Finite literal point-pair A*. No broad net classifier or mask expansion.
 step=.25;margin=15;lo=(math.floor((min(start[0],end[0])-margin)/step)*step,math.floor((min(start[1],end[1])-margin)/step)*step);hi=(max(start[0],end[0])+margin,max(start[1],end[1])+margin)
 def point(v):return(lo[0]+v[0]*step,lo[1]+v[1]*step)
 def index(v):return(round((v[0]-lo[0])/step),round((v[1]-lo[1])/step))
 def nearby(v):
  ix,iy=index(v);return[(ix+dx,iy+dy)for dx in range(-4,5)for dy in range(-4,5)if math.dist(v,point((ix+dx,iy+dy)))<.52 and clear([v,point((ix+dx,iy+dy))],name,layer,width,space)]
 starts,ends=nearby(start),set(nearby(end))
 if not starts or not ends:return None
 heap=[];costs={};parents={};cache={};maxq=index(hi);t0=time.monotonic();count=0
 for v in starts:costs[v]=math.dist(start,point(v));parents[v]=None;heapq.heappush(heap,(costs[v]+math.dist(point(v),end),costs[v],v))
 while heap:
  _,cost,v=heapq.heappop(heap)
  if cost!=costs.get(v):continue
  count+=1
  if v in ends:
   chain=[]
   while v is not None:chain.append(point(v));v=parents[v]
   raw=[start]+list(reversed(chain))+[end];raw=[x for i,x in enumerate(raw)if not i or math.dist(x,raw[i-1])>1e-6];simple=[raw[0]];i=0
   while i<len(raw)-1:
    j=len(raw)-1
    while j>i+1 and not clear([raw[i],raw[j]],name,layer,width,space):j-=1
    simple.append(raw[j]);i=j
   return simple
  if count>25000 or time.monotonic()-t0>15:
   print(json.dumps(dict(search_timeout=True,layer=b.GetLayerName(layer),states=count,seconds=time.monotonic()-t0)),flush=True);return None
  for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
   n=(v[0]+dx,v[1]+dy)
   if not(0<=n[0]<=maxq[0]and 0<=n[1]<=maxq[1]):continue
   key=(v,n)if v<n else(n,v)
   if key not in cache:cache[key]=clear([point(v),point(n)],name,layer,width,space)
   if not cache[key]:continue
   nc=cost+step*math.hypot(dx,dy)
   if nc+1e-8>=costs.get(n,float('inf')):continue
   costs[n]=nc;parents[n]=v;heapq.heappush(heap,(nc+math.dist(point(n),end),nc,n))
 return None

jobs=[]
for name,row in m['nets'].items():
 candidates=[p for p in ps.values()if p.GetNetname()==name and p.IsOnLayer(pcbnew.B_Cu)and p.GetParentFootprint().GetReference()!='U1001']
 for p,q in itertools.combinations(candidates,2):
  length=math.dist(mm(p.GetPosition()),mm(q.GetPosition()))
  if 0<length<=40:jobs.append((length,name,p,q))
attempts=0;search_started=time.monotonic()
for length,name,p,q in sorted(jobs,key=lambda x:x[0]):
 b.BuildConnectivity()
 if q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in b.GetConnectivity().GetConnectedItems(p)}:continue
 if attempts>=100 or len(groups)>=48 or time.monotonic()-search_started>600:break
 attempts+=1
 fills={pcbnew.B_Cu:full_fills[pcbnew.B_Cu]}
 pair=[p.GetParentFootprint().GetReference()+'.'+p.GetNumber(),q.GetParentFootprint().GetReference()+'.'+q.GetNumber()]
 points=path(mm(p.GetPosition()),mm(q.GetPosition()),pcbnew.B_Cu)
 if not points:
  blocked.append(dict(net=name,source_pair=pair,span_mm=length,reason='Finite actual B geometry/reference search has no accepted full path'))
  print(json.dumps(dict(blocked=pair,attempt=attempts)),flush=True);continue
 signal=[add_segment(a,z,name,pcbnew.B_Cu)for a,z in zip(points,points[1:])]
 groups.append(dict(net=name,source_pair=pair,source_pad_UUIDs=[p.m_Uuid.AsString(),q.m_Uuid.AsString()],signal_UUIDs=[u for u in signal if u],ground_UUIDs=[],new_copper_UUIDs=[u for u in signal if u],B_path_mm=points))
 print(json.dumps(dict(added_pair=pair,net=name,newCu=len(signal),attempt=attempts)),flush=True)
dest=OUT/'motherboard-ordinary-B-batch-candidate.kicad_pcb'
pcbnew.SaveBoard(str(dest),b)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
for f in BASE.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
assert all(e.sha(p)==h for p,h in frozen.items())
e.write(OUT/'proposed-groups.json',dict(input_sha256=frozen,base_sha256=e.sha(BASE),groups=groups,blocked=blocked,new_copper_UUIDs=[t.m_Uuid.AsString()for t in added],actual_signal_layers=['B.Cu'],actual_common_reference='In4.Cu',no_added_drills=True,native_refill_DRC_full_return_and_SOURCE_validation_pending=True,manufacturing_ready=False))
print(json.dumps(dict(groups=len(groups),newCu=len(added),blocked=len(blocked))),flush=True)
