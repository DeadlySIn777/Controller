"""One actual complete configuration-clock Source pair with bounded BGA neck."""
from pathlib import Path
import sys,copy,json,math,shutil,time,heapq
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
import hardware_scope_anchored_reference_pieces as pieces
import hardware_route_owned_bypass_loops_wip_r03 as w
from hardware_route_local_signals import paths
from hardware_route_logic_return import xy,mm,segment_distance
from hardware_check_return_corridors import covered
e=authority.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-C19042-local-bypass-r81/motherboard-bounded-merged-candidate.kicad_pcb')
MAP=Path('reports/motherboard-domains-20261001/source26-r81-r01/domain-map.json')
SOURCE=Path('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')
OUT=Path(sys.argv[1]);OUT.mkdir(exist_ok=False,parents=True)
name='/fpga_core/FPGA_FLASH_MISO';row=copy.deepcopy(e.read(SOURCE)['nets'][name]);row.update(via_diameter_mm=.5,via_drill_mm=.2)
b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity();e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
checker=pieces.SourceAnchoredPiecesCheck(b,{name:row},e.read(MAP));fills={pcbnew.F_Cu:checker.reference('/LOGIC_GND',pcbnew.In1_Cu),pcbnew.B_Cu:checker.reference('/LOGIC_GND',pcbnew.In4_Cu)};g=w.Geometry(b)
pads={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()};p,q=pads['U1001','N1'],pads['U1002','2'];ground=pads['U1001','N2']
if p.GetNetname()!=name or q.GetNetname()!=name or ground.GetNetname()!='/LOGIC_GND'or mm(p.GetPosition())!=(94.0,47.6)or mm(ground.GetPosition())!=(94.8,47.6):raise ValueError('Literal actual native Source recipe changed')

def clear(points,layer,width,space):
 for a,z in zip(points,points[1:]):
  seg=pcbnew.SEG(xy(a),xy(z))
  for pad,_ in g.pads.candidates(a,z,width/2+space+.1):
   if pad.IsOnLayer(layer)and pad.GetNetname()!=name and pad.GetEffectiveShape(layer).Collide(seg,pcbnew.FromMM(width/2+space-1e-6)):return False
  for other,s,t,ow in g.tracks[layer].candidates(a,z,width/2+.5):
   if other!=name and segment_distance(a,z,s,t)<width/2+ow/2+space-1e-6:return False
  copper=e.corridor_polygon(tuple(xy(a)),tuple(xy(z)),pcbnew.FromMM(width/2))
  for zone in g.keepouts:
   if zone.IsOnLayer(layer)and zone.GetDoNotAllowTracks():
    hit=pcbnew.SHAPE_POLY_SET();hit.Append(copper);hit.BooleanIntersection(zone.Outline())
    if hit.Area():return False
  envelope=e.corridor_polygon(tuple(xy(a)),tuple(xy(z)),pcbnew.FromMM(width/2+.40))
  if not covered(envelope,fills[layer]):return False
 return True

def path(start,end,layer,width=.35,space=.20):
 for points in paths(start,end):
  if clear(points,layer,width,space):return points
 # Finite literal point-pair A*. No broad net classifier or mask expansion.
 step=.125;margin=4;lo=(math.floor((min(start[0],end[0])-margin)/step)*step,math.floor((min(start[1],end[1])-margin)/step)*step);hi=(max(start[0],end[0])+margin,max(start[1],end[1])+margin)
 def point(v):return(lo[0]+v[0]*step,lo[1]+v[1]*step)
 def index(v):return(round((v[0]-lo[0])/step),round((v[1]-lo[1])/step))
 def nearby(v):
  ix,iy=index(v);return[(ix+dx,iy+dy)for dx in range(-4,5)for dy in range(-4,5)if math.dist(v,point((ix+dx,iy+dy)))<.52 and clear([v,point((ix+dx,iy+dy))],layer,width,space)]
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
    while j>i+1 and not clear([raw[i],raw[j]],layer,width,space):j-=1
    simple.append(raw[j]);i=j
   return simple
  if count>30000 or time.monotonic()-t0>60:return None
  for dx,dy in((1,0),(-1,0),(0,1),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)):
   n=(v[0]+dx,v[1]+dy)
   if not(0<=n[0]<=maxq[0]and 0<=n[1]<=maxq[1]):continue
   key=(v,n)if v<n else(n,v)
   if key not in cache:cache[key]=clear([point(v),point(n)],layer,width,space)
   if not cache[key]:continue
   nc=cost+step*math.hypot(dx,dy)
   if nc+1e-8>=costs.get(n,float('inf')):continue
   costs[n]=nc;parents[n]=v;heapq.heappush(heap,(nc+math.dist(point(n),end),nc,n))
 return None

source_via=(93.6,47.2);ground_via=(94.4,47.2);receiver=(117.870038,29.647462)
receiver_ground='87d532db-9d39-437e-81e0-13a8657d3518'
rv=next(t for t in b.GetTracks()if t.m_Uuid.AsString()==receiver_ground)
if rv.Type()!=pcbnew.PCB_VIA_T or rv.GetNetname()!='/LOGIC_GND'or mm(rv.GetPosition())!=(118.670038,29.647462):raise ValueError('Literal actual receiver return witness changed')
receiving_path=path(mm(q.GetPosition()),receiver,pcbnew.F_Cu)
trunk=path(source_via,receiver,pcbnew.B_Cu)
if not receiving_path or not trunk:
 e.write(OUT/'blocked.json',dict(base_sha256=e.sha(BASE),source_net=name,receiver_F_path=receiving_path,B_trunk=trunk,no_copper_added=True,reason='No bounded native-clear actual own-reference complete path',manufacturing_ready=False));raise SystemExit('Literal complete Source pair is blocked; no stubs emitted')
added=[];signals=[];grounds=[]
def track(net,a,z,layer,width,dest):
 t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetStart(xy(a));t.SetEnd(xy(z));t.SetLayer(layer);t.SetWidth(pcbnew.FromMM(width));b.Add(t);added.append(t);dest.append(t);return t
def via(net,at,dest):
 t=pcbnew.PCB_VIA(b);t.SetNet(b.FindNet(net));t.SetPosition(xy(at));t.SetWidth(pcbnew.FromMM(.5));t.SetDrill(pcbnew.FromMM(.2));t.SetViaType(pcbnew.VIATYPE_THROUGH);t.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(t);added.append(t);dest.append(t);return t
track(name,mm(p.GetPosition()),source_via,pcbnew.F_Cu,.20,signals);via(name,source_via,signals)
track('/LOGIC_GND',mm(ground.GetPosition()),ground_via,pcbnew.F_Cu,.20,grounds);via('/LOGIC_GND',ground_via,grounds)
for a,z in zip(trunk,trunk[1:]):track(name,a,z,pcbnew.B_Cu,.35,signals)
via(name,receiver,signals)
for a,z in zip(receiving_path,receiving_path[1:]):track(name,a,z,pcbnew.F_Cu,.35,signals)
tree=e.parse(BASE.read_text());old=copy.deepcopy(tree)
for t in added:
 if t.Type()==pcbnew.PCB_VIA_T:n=['via',['at',*[str(v)for v in mm(t.GetPosition())]],['size','.5'],['drill','.2'],['layers','"F.Cu"','"B.Cu"'],['net',e.q(t.GetNetname())],['uuid',e.q(t.m_Uuid.AsString())]]
 else:n=['segment',['start',*[str(v)for v in mm(t.GetStart())]],['end',*[str(v)for v in mm(t.GetEnd())]],['width',str(pcbnew.ToMM(t.GetWidth()))],['layer',e.q(b.GetLayerName(t.GetLayer()))],['net',e.q(t.GetNetname())],['uuid',e.q(t.m_Uuid.AsString())]]
 tree.append(n)
if e.immutable_objects(tree)!=e.immutable_objects(old):raise ValueError('Source/land/pose/zone definition changed')
dest=OUT/'motherboard-FPGA-flash-MISO-candidate.kicad_pcb';dest.write_text(authority.dump_native_board(tree)+'\n')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
for f in BASE.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
e.write(OUT/'proposed-delta.json',dict(base_sha256=e.sha(BASE),source_review_sha256=e.sha(SOURCE),source_net=name,actual_Source_pair=['U1001.N1','U1002.2'],actual_Source_pad_UUIDs=[p.m_Uuid.AsString(),q.m_Uuid.AsString()],new_signal_UUIDs=[t.m_Uuid.AsString()for t in signals],new_SOURCE_ground_UUIDs=[t.m_Uuid.AsString()for t in grounds],source_F_neck=[mm(p.GetPosition()),source_via],actual_outer_source_20mm_escape_length_mm=math.dist(mm(p.GetPosition()),source_via),source_ground_N2_path=[mm(ground.GetPosition()),ground_via],B_trunk=trunk,receiver_F_path=receiving_path,receiving_actual_Source_ground_via_UUID=receiver_ground,signal_via_mm=[.5,.2],real_return_stitch_max_distance_mm=.8,own_reference_margin_mm=.40,no_incomplete_stub_candidate=True,actual_full_native_and_Source_annulus_validation_pending=True,loaded_configuration_data_timing_and_factory_2oz_profile_unqualified=True,manufacturing_ready=False))
print(json.dumps(dict(complete_Source_path_proposed=True,newCu=len(added),F_escape_mm=math.dist(mm(p.GetPosition()),source_via),B_path_mm=sum(math.dist(a,z)for a,z in zip(trunk,trunk[1:])))),flush=True)
