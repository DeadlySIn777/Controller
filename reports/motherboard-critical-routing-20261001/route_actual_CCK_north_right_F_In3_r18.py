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
BASE=Path('reports/motherboard-critical-routing-20261001/CORE-literal-antipad-join-baseline-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb')
MAP=Path('reports/motherboard-domains-20261001/source26-root84-CORE-collar-baseline-r03/domain-map.json')
SOURCE=Path('reports/motherboard-critical-routing-20261001/source26-critical-digital-r02/prototype-route-geometry-review.json')
OUT=Path(sys.argv[1]);OUT.mkdir(exist_ok=False,parents=True)
name='/fpga_core/FPGA_FLASH_CCK_SOURCE';row=copy.deepcopy(e.read(SOURCE)['nets'][name]);row.update(via_diameter_mm=.6,via_drill_mm=.3,reference_layers={'F.Cu':'In1.Cu','In3.Cu':'In4.Cu'})
b=pcbnew.LoadBoard(str(BASE));b.BuildConnectivity();e.native_source_check(b,e.read('hardware/motherboard/design.json'),Path('hardware/motherboard/netlist.xml'))
checker=pieces.SourceAnchoredPiecesCheck(b,{name:row},e.read(MAP));fills={pcbnew.F_Cu:checker.reference('/LOGIC_GND',pcbnew.In1_Cu),pcbnew.In3_Cu:checker.reference('/LOGIC_GND',pcbnew.In4_Cu)}
# Search uses the original frozen reference subset; a fresh candidate map and
# native Source witness review are mandatory before any adoption.
moved_cap=next(f for f in b.GetFootprints()if f.GetReference()=='C1022');moved_cap.SetOrientationDegrees(90);moved_cap.SetPosition(xy((94.5,48.0)))
g=w.Geometry(b)
pads={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()};p,q=pads['U1001','M3'],pads['R1002','1'];ground=pads['U1001','N2']
if p.GetNetname()!=name or q.GetNetname()!=name or ground.GetNetname()!='/LOGIC_GND'or mm(p.GetPosition())!=(95.6,46.8)or mm(ground.GetPosition())!=(94.8,47.6):raise ValueError('Literal actual native Source recipe changed')

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

source_via=(96.0,46.4);source_ground=(96.0,45.6);receiver=(109.,27.);receiver_ground=(109.,26.2);cap_feed=(93.6,48.8)
def via_screen(net,at,diameter,drill):
 issues=[];gaps=[];shape=pcbnew.SHAPE_CIRCLE(xy(at),pcbnew.FromMM(diameter/2))
 for f in b.GetFootprints():
  for pad in f.Pads():
   if pad.GetNetname()==net:continue
   clearance=.125 if f.GetReference()=='U1001'else .20
   for layer in g.tracks:
    if pad.IsOnLayer(layer)and pad.GetEffectiveShape(layer).Collide(shape,pcbnew.FromMM(clearance-1e-6)):
     issues.append(dict(kind='actual_foreign_pad',reference=f.GetReference(),pin=pad.GetNumber(),layer=b.GetLayerName(layer),required_clearance_mm=clearance))
   if f.GetReference()=='U1001':
    gap=math.dist(at,mm(pad.GetPosition()))-diameter/2-pcbnew.ToMM(pad.GetSize().x)/2
    if gap<.3:gaps.append(dict(reference='U1001',pin=pad.GetNumber(),nominal_circular_land_to_via_gap_mm=gap,scoped_minimum_mm=.125))
 for layer,index in g.tracks.items():
  for other,s,t,ow in index.candidates(at,at,diameter/2+.7):
   if other!=net and segment_distance(at,at,s,t)<diameter/2+ow/2+.20-1e-6:issues.append(dict(kind='actual_foreign_Cu',layer=b.GetLayerName(layer),net=other,start=s,end=t))
 for pos,d in g.holes:
  if math.dist(at,pos)<drill/2+d/2+.25-1e-6:issues.append(dict(kind='actual_hole_spacing',other_xy=pos,other_drill=d))
 for z in g.keepouts:
  if z.GetDoNotAllowVias()and z.Outline().Collide(shape):issues.append(dict(kind='actual_via_keepout',uuid=z.m_Uuid.AsString()))
 return dict(at=at,net=net,diameter_mm=diameter,drill_mm=drill,passed=not issues,issues=issues,actual_manufacturer_land_gaps=gaps,CORE_IO3_filled_geometry_and_current_not_qualified_by_this_screen=True)
screens=[via_screen(net,at,d,dr)for net,at,d,dr in((name,source_via,.5,.2),('/LOGIC_GND',source_ground,.5,.2),(name,receiver,.6,.3),('/LOGIC_GND',receiver_ground,.5,.2),('/IO_3V3',cap_feed,.5,.2))]
e.write(OUT/'actual-native-geometry-preflight.json',dict(base_sha256=e.sha(BASE),actual_source=(mm(p.GetPosition()),mm(q.GetPosition())),via_screens=screens,original_U1001_pad_via_125mm_rule_preserved=True,via_annular_ring_mm=.15,pin_pitch_mm=.8,pin_land_mm=.35,nominal_center_gap_mm=math.hypot(.4,.4)-.25-.175,CORE_relative_power_guard_pending=True,manufacturing_ready=False))
if any(not r['passed']for r in screens):raise SystemExit('Actual native preflight rejects one or more literal vias; no copper emitted')
if not clear([mm(p.GetPosition()),source_via],pcbnew.F_Cu,.20,.20):raise SystemExit('Actual .20 diagonal Source escape fails copper/reference guard; no copper emitted')
receiving_path=[receiver,mm(q.GetPosition())]
if not clear(receiving_path,pcbnew.F_Cu,.35,.20):raise SystemExit('Actual receiving Source leg obstructed; no copper emitted')
print('Searching exact complete north-right CCK F/In3 with actual In1/In4 references',flush=True)
trunk=path(source_via,receiver,pcbnew.In3_Cu)
if not trunk:
 e.write(OUT/'blocked.json',dict(no_copper_added=True,source_pair=['U1001.M3','R1002.1'],reason='No complete In3 path with .40 ownIn1 reference',manufacturing_ready=False));raise SystemExit('No complete Source pair; no stubs emitted')
signals=[];grounds=[];added=[]
def add_track(net,a,z,layer,width,dest):
 t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(net));t.SetStart(xy(a));t.SetEnd(xy(z));t.SetLayer(layer);t.SetWidth(pcbnew.FromMM(width));b.Add(t);dest.append(t);added.append(t)
def add_via(net,at,d,dr,dest):
 t=pcbnew.PCB_VIA(b);t.SetNet(b.FindNet(net));t.SetPosition(xy(at));t.SetWidth(pcbnew.FromMM(d));t.SetDrill(pcbnew.FromMM(dr));t.SetViaType(pcbnew.VIATYPE_THROUGH);t.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);t.SetIsFree(True);b.Add(t);dest.append(t);added.append(t)
add_track(name,mm(p.GetPosition()),source_via,pcbnew.F_Cu,.20,signals)
for a,z in zip(trunk,trunk[1:]):add_track(name,a,z,pcbnew.In3_Cu,.35,signals)
for a,z in zip(receiving_path,receiving_path[1:]):add_track(name,a,z,pcbnew.F_Cu,.35,signals)
add_via(name,source_via,.5,.2,signals);add_via(name,receiver,.6,.3,signals)
add_via('/LOGIC_GND',source_ground,.5,.2,grounds);add_via('/LOGIC_GND',receiver_ground,.5,.2,grounds)
cap_cu=[];cap_power=next(p for p in moved_cap.Pads()if p.GetNumber()=='1');add_via('/IO_3V3',cap_feed,.5,.2,cap_cu);add_track('/IO_3V3',mm(cap_power.GetPosition()),cap_feed,pcbnew.B_Cu,.35,cap_cu)
temporary=OUT/'native-posed-copy.kicad_pcb';pcbnew.SaveBoard(str(temporary),b);tree=e.parse(temporary.read_text());old=copy.deepcopy(e.parse(BASE.read_text()))
# Native-save exact geometry remains subject to independent old-Cu/pad/pose comparison.
# Only C1022 native pose and the explicit additions are allowed.
dest=OUT/'motherboard-FPGA-flash-CCK-candidate.kicad_pcb';dest.write_text(authority.dump_native_board(tree)+'\n')
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
for f in BASE.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
e.write(OUT/'scoped-F-In3-declaration.json',dict(source_net=name,literal_SOURCE_pair=['U1001.M3','R1002.1'],source_design_sha256=e.sha('hardware/motherboard/design.json'),source_netlist_sha256=e.sha('hardware/motherboard/netlist.xml'),reference_layers={'F.Cu':'In1.Cu','In3.Cu':'In4.Cu'},reference_corridor_margin_mm=.40,actual_Source_ground_stitch_max_distance_mm=.8,signal_via_BGA_mm=[.5,.2],receiver_signal_via_mm=[.6,.3],no_source_architecture_changes=True,frozen_F_B_manifest_unchanged=True,CORE_relative_power_review_pending=True,loaded_clock_timing_and_exact_factory_process_unqualified=True,manufacturing_ready=False))
e.write(OUT/'proposed-delta.json',dict(base_sha256=e.sha(BASE),source_review_sha256=e.sha(SOURCE),source_net=name,actual_Source_pair=['U1001.M3','R1002.1'],actual_Source_pad_UUIDs=[p.m_Uuid.AsString(),q.m_Uuid.AsString()],new_signal_UUIDs=[t.m_Uuid.AsString()for t in signals],new_SOURCE_ground_UUIDs=[t.m_Uuid.AsString()for t in grounds],new_C1022_local_power_UUIDs=[t.m_Uuid.AsString()for t in cap_cu],exact_C1022_pose_before=[[95.225,46.75],180],exact_C1022_pose_after=[[94.5,48],90],C1022_local_feed=cap_feed,owner_power_pad_distance_mm=math.dist(mm(cap_power.GetPosition()),mm(pads['U1001','L6'].GetPosition())),owner_2mm_engineering_target_NOT_passed=True,source_F_leg=[mm(p.GetPosition()),source_via],source_F_width_mm=.20,aggregate_15mm_neck_length_mm=0.,In3_trunk=trunk,receiver_F_path=receiving_path,source_ground_at=source_ground,receiver_ground_at=receiver_ground,no_incomplete_stub_candidate=True,actual_native_connectivity_and_return_annulus_checks_pending=True,relative_CORE_power_preservation_pending=True,manufacturing_ready=False))
print(json.dumps(dict(complete_Source_pair_proposed=True,newCu=len(added),actual_In3_path=trunk)),flush=True)


