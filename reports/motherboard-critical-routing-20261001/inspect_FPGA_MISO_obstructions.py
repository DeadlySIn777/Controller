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


records=[]
def reason(a,z,layer,width=.35,space=.20):
 seg=pcbnew.SEG(xy(a),xy(z))
 for pad,_ in g.pads.candidates(a,z,width/2+space+.1):
  if pad.IsOnLayer(layer)and pad.GetNetname()!=name and pad.GetEffectiveShape(layer).Collide(seg,pcbnew.FromMM(width/2+space-1e-6)):return dict(kind='actual_foreign_pad',reference=pad.GetParentFootprint().GetReference(),pin=pad.GetNumber(),net=pad.GetNetname())
 for other,s,t,ow in g.tracks[layer].candidates(a,z,width/2+.5):
  if other!=name and segment_distance(a,z,s,t)<width/2+ow/2+space-1e-6:return dict(kind='actual_foreign_track_or_via',net=other,start=s,end=t,width=ow)
 copper=e.corridor_polygon(tuple(xy(a)),tuple(xy(z)),pcbnew.FromMM(width/2))
 for zone in g.keepouts:
  if zone.IsOnLayer(layer)and zone.GetDoNotAllowTracks():
   hit=pcbnew.SHAPE_POLY_SET();hit.Append(copper);hit.BooleanIntersection(zone.Outline())
   if hit.Area():return dict(kind='actual_native_rule_area',uuid=zone.m_Uuid.AsString())
 envelope=e.corridor_polygon(tuple(xy(a)),tuple(xy(z)),pcbnew.FromMM(width/2+.40))
 if not covered(envelope,fills[layer]):return dict(kind='actual_own_reference_uncovered')
 return dict(kind='clear')
for label,layer,a,z in [('flash_left_F',pcbnew.F_Cu,(119.4125,26.365),(115.0,26.365)),('flash_lower_F',pcbnew.F_Cu,(117.870038,29.647462),(115.0,29.647462)),('FPGA_west_B',pcbnew.B_Cu,(93.6,47.2),(90.0,47.2)),('FPGA_north_B',pcbnew.B_Cu,(93.6,47.2),(93.6,36.0)),('FPGA_south_B',pcbnew.B_Cu,(93.6,47.2),(93.6,55.0))]:
 n=math.ceil(math.dist(a,z)/.125);rows=[]
 for i in range(n):
  x=(a[0]+(z[0]-a[0])*i/n,a[1]+(z[1]-a[1])*i/n);y=(a[0]+(z[0]-a[0])*(i+1)/n,a[1]+(z[1]-a[1])*(i+1)/n)
  rows.append(dict(start=x,end=y,reason=reason(x,y,layer)))
 records.append(dict(label=label,layer=b.GetLayerName(layer),rows=rows))
e.write(OUT/'literal-obstructions.json',dict(board_sha256=e.sha(BASE),map_sha256=e.sha(MAP),records=records,no_source_or_board_mutation=True))
print(json.dumps([{r['label']:[x for x in r['rows']if x['reason']['kind']!='clear'][:4]}for r in records]),flush=True)
