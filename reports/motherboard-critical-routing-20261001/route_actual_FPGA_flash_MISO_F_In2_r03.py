"""One actual complete configuration-clock Source pair with bounded BGA neck."""
from pathlib import Path
import sys,copy,json,math,shutil,time,heapq
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
import hardware_route_critical_digital_wip_r05 as authority
import hardware_scope_anchored_reference_pieces as pieces
import hardware_route_owned_bypass_loops_wip_r03 as w
import hardware_zone_motherboard_returns as zoneutils
from hardware_route_local_signals import paths
from hardware_route_logic_return import xy,mm,segment_distance
from hardware_check_return_corridors import covered
e=authority.engine
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83/motherboard-bounded-merged-candidate.kicad_pcb')
MAP=Path('reports/motherboard-domains-20261001/source26-r83-r01/domain-map.json')
SOURCE=Path('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')
OUT=Path(sys.argv[1]);OUT.mkdir(exist_ok=False,parents=True)
name='/fpga_core/FPGA_FLASH_MISO';row=copy.deepcopy(e.read(SOURCE)['nets'][name]);row.update(via_diameter_mm=.6,via_drill_mm=.3,reference_layers={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu'})
b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity();e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
checker=pieces.SourceAnchoredPiecesCheck(b,{name:row},e.read(MAP));fills={pcbnew.F_Cu:checker.reference('/LOGIC_GND',pcbnew.In1_Cu),pcbnew.In2_Cu:checker.reference('/LOGIC_GND',pcbnew.In1_Cu)};g=w.Geometry(b)
pads={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()};p,q=pads['U1001','N1'],pads['U1002','2'];ground=pads['U1001','J1']
if p.GetNetname()!=name or q.GetNetname()!=name or ground.GetNetname()!='/LOGIC_GND'or mm(p.GetPosition())!=(94.0,47.6)or mm(ground.GetPosition())!=(94.0,44.4):raise ValueError('Literal actual native Source recipe changed')

def clear(points,layer,width,space):
 for a,endpt in zip(points,points[1:]):
  z=endpt
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
  # All actual retained wide power tracks remain native physical obstacles.
  # Broad IO3 fill carve/capacity is an explicit pending final proof; this
  # geometry candidate cannot be adopted without the protected feed guard.
 return True

def path(start,end,layer,width=.35,space=.20):
 original=fills[layer]
 clipped=zoneutils.duplicate(original)
 clipped.BooleanIntersection(zoneutils.rectangle((min(start[0],end[0])-8,min(start[1],end[1])-8,max(start[0],end[0])+8,max(start[1],end[1])+8),0))
 clipped.Simplify()
 # A native Boolean intersection only removes the outside reference. Every
 # local segment is still checked against the exact SOURCE-eligible fill.
 added=zoneutils.duplicate(clipped);added.BooleanSubtract(original)
 if added.Area()!=0:raise ValueError('Clipped local reference added area')
 fills[layer]=clipped
 for points in paths(start,end):
  if clear(points,layer,width,space):return points
 # Finite literal point-pair A*. No broad net classifier or mask expansion.
 step=.125;margin=8;lo=(math.floor((min(start[0],end[0])-margin)/step)*step,math.floor((min(start[1],end[1])-margin)/step)*step);hi=(max(start[0],end[0])+margin,max(start[1],end[1])+margin)
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
  if count>50000 or time.monotonic()-t0>180:
   print(json.dumps(dict(search_timeout=True,layer=b.GetLayerName(layer),states=count,seconds=time.monotonic()-t0)),flush=True);return None
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

source_via=(92.9,44.4);ground_via=(92.9,43.6);receiver=(118.,26.365);receiver_ground_at=(118.,25.565)
receiver_ground_pad=pads['U1002','4']
if receiver_ground_pad.GetNetname()!='/LOGIC_GND':raise ValueError('Actual flash Ground4 changed')
print('Searching actual local F receiving path',flush=True)
receiving_path=[mm(q.GetPosition()),receiver]
if not clear(receiving_path,pcbnew.F_Cu,.35,.20):receiving_path=None
print(json.dumps(dict(actual_F_path=receiving_path)),flush=True)
print('Searching actual bounded B configuration-data trunk',flush=True)
trunk=path(source_via,receiver,pcbnew.In2_Cu)
print(json.dumps(dict(actual_B_trunk=trunk)),flush=True)
if not receiving_path or not trunk:
 diagnostics=[]
 for layer,ends in((pcbnew.F_Cu,(mm(q.GetPosition()),receiver)),(pcbnew.In2_Cu,(source_via,receiver))):
  for pt in ends:
   frame=[]
   for dx in(-.25,0,.25):
    for dy in(-.25,0,.25):
     target=(pt[0]+dx,pt[1]+dy)
     frame.append(dict(target=target,clear=clear([pt,target],layer,.35,.20),own_reference=covered(e.corridor_polygon(tuple(xy(pt)),tuple(xy(target)),pcbnew.FromMM(.575)),fills[layer])))
   diagnostics.append(dict(layer=b.GetLayerName(layer),point=pt,nearby=frame))
 e.write(OUT/'endpoint-diagnostics.json',diagnostics)
 e.write(OUT/'blocked.json',dict(base_sha256=e.sha(BASE),source_net=name,receiver_F_path=receiving_path,B_trunk=trunk,no_copper_added=True,reason='No bounded native-clear actual own-reference complete path',manufacturing_ready=False));raise SystemExit('Literal complete Source pair is blocked; no stubs emitted')
added=[];signals=[];grounds=[]
def track(net,a,z,layer,width,dest):
 t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetStart(xy(a));t.SetEnd(xy(z));t.SetLayer(layer);t.SetWidth(pcbnew.FromMM(width));b.Add(t);added.append(t);dest.append(t);return t
def via(net,at,dest):
 diameter,drill=(.6,.3)if net==name else(.5,.2)
 t=pcbnew.PCB_VIA(b);t.SetNet(b.FindNet(net));t.SetPosition(xy(at));t.SetWidth(pcbnew.FromMM(diameter));t.SetDrill(pcbnew.FromMM(drill));t.SetViaType(pcbnew.VIATYPE_THROUGH);t.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);b.Add(t);added.append(t);dest.append(t);return t
track(name,mm(p.GetPosition()),(92.9,47.6),pcbnew.F_Cu,.20,signals)
track(name,(92.9,47.6),source_via,pcbnew.F_Cu,.35,signals);via(name,source_via,signals)
existing_source_ground=next(t for t in b.GetTracks()if t.m_Uuid.AsString()=='1ccf7b83-4236-4c1f-9852-09d8c831069a')
if existing_source_ground.GetNetname()!='/LOGIC_GND' or mm(existing_source_ground.GetPosition())!=(93.6,44.):raise ValueError('Actual existing J1 Ground source witness changed')
via('/LOGIC_GND',receiver_ground_at,grounds)
for a,z in zip(trunk,trunk[1:]):track(name,a,z,pcbnew.In2_Cu,.35,signals)
via(name,receiver,signals)
for a,z in zip(receiving_path,receiving_path[1:]):track(name,a,z,pcbnew.F_Cu,.35,signals)
tree=e.parse(BASE.read_text());old=copy.deepcopy(tree)
for t in added:
 if t.Type()==pcbnew.PCB_VIA_T:n=['via',['at',*[str(v)for v in mm(t.GetPosition())]],['size',str(pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)))],['drill',str(pcbnew.ToMM(t.GetDrill()))],['layers','"F.Cu"','"B.Cu"'],['net',e.q(t.GetNetname())],['uuid',e.q(t.m_Uuid.AsString())]]
 else:n=['segment',['start',*[str(v)for v in mm(t.GetStart())]],['end',*[str(v)for v in mm(t.GetEnd())]],['width',str(pcbnew.ToMM(t.GetWidth()))],['layer',e.q(b.GetLayerName(t.GetLayer()))],['net',e.q(t.GetNetname())],['uuid',e.q(t.m_Uuid.AsString())]]
 tree.append(n)
if e.immutable_objects(tree)!=e.immutable_objects(old):raise ValueError('Source/land/pose/zone definition changed')
dest=OUT/'motherboard-FPGA-flash-MISO-candidate.kicad_pcb';dest.write_text(authority.dump_native_board(tree)+'\n')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
for f in BASE.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
e.write(OUT/'scoped-F-In2-declaration.json',dict(passed_source_review=True,scope='Only actual FPGA FLASH_MISO U1001.N1 to U1002.2',source_net=name,reference_layers={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu'},signal_via_mm=[.6,.3],actual_SOURCE_ground_stitch_max_distance_mm=1.,reference_corridor_margin_mm=.40,frozen_F_B_152_manifest_unchanged=True,retained_wide_power_Cu_untouched=True,broad_fill_ampacity_and22feed_proof_pending=True,loaded_timing_and_factory_process_unqualified=True,manufacturing_ready=False))
e.write(OUT/'proposed-delta.json',dict(base_sha256=e.sha(BASE),source_review_sha256=e.sha(SOURCE),source_net=name,actual_Source_pair=['U1001.N1','U1002.2'],actual_Source_pad_UUIDs=[p.m_Uuid.AsString(),q.m_Uuid.AsString()],new_signal_UUIDs=[t.m_Uuid.AsString()for t in signals],new_SOURCE_ground_UUIDs=[t.m_Uuid.AsString()for t in grounds],source_F_neck=[mm(p.GetPosition()),source_via],actual_outer_source_20mm_escape_length_mm=math.dist(mm(p.GetPosition()),source_via),source_ground_J1_path=[mm(ground.GetPosition()),ground_via],B_trunk=trunk,receiver_F_path=receiving_path,receiving_actual_Source_ground_pin='U1002.4',receiving_new_Source_ground_at=receiver_ground_at,signal_via_mm=[.6,.3],real_return_stitch_max_distance_mm=max(math.dist(source_via,(93.6,44.)),math.dist(receiver,receiver_ground_at)),own_reference_margin_mm=.40,no_incomplete_stub_candidate=True,actual_full_native_and_Source_annulus_validation_pending=True,loaded_configuration_data_timing_and_factory_2oz_profile_unqualified=True,manufacturing_ready=False))
print(json.dumps(dict(complete_Source_path_proposed=True,newCu=len(added),F_escape_mm=math.dist(mm(p.GetPosition()),source_via),B_path_mm=sum(math.dist(a,z)for a,z in zip(trunk,trunk[1:])))),flush=True)
