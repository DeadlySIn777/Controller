import sys,json,math,collections,shutil,subprocess
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import identity,mm,xy,segment_distance
from hardware_route_local_signals import paths,GeometryIndex
from hardware_route_current_delivery_native import sha
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT101-two-health-local-anchor-control-repair-r270');O.mkdir(exist_ok=False);o=pcbnew.LoadBoard(str(B));ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in o.GetPads()if p.GetNumber()};n=ps['U11020','3'].GetNetname();old={t.m_Uuid.AsString():identity(t)for t in o.GetTracks()};ret={t.m_Uuid.AsString()for t in o.GetTracks()if t.GetNetname()==n};t=parse(without_generated_fills(B.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'literal-U20-B-input-retired.kicad_pcb';D.write_text(dump_board(t))
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};g=FastGeometry(b);base_clear=g.clear;ground=ps['U11020','2'].GetNetname();viaholes=[(mm(v.GetPosition()),pcbnew.ToMM(v.GetWidth(pcbnew.F_Cu))/2+.2505,v.GetNetname())for v in b.GetTracks()if isinstance(v,pcbnew.PCB_VIA)and v.GetNetname()!=ground]
holeindex=GeometryIndex()
for c,r,vn in viaholes:holeindex.add((c,r,vn),(c[0]-r,c[1]-r,c[0]+r,c[1]+r))
def guarded_clear(points,net,l,w):
 if not base_clear(points,net,l,w):return False
 if net==n:
  for x,y in zip(points,points[1:]):
   for c,r,vn in holeindex.candidates(x,y,w/2+.40+.03):
    if vn==net:continue
    if segment_distance(x,y,c,c)<r+w/2+.40+.03:return False
 return True
g.clear=guarded_clear;added=[];routes=[]
def route(a,z,net,layer,role,width=.2):
 pts=next((v for v in paths(a,z)if g.clear(v,net,layer,width)),None)
 if pts is None:pts=g.grid(a,z,net,layer,width,step=.1,padding=12,max_nodes=300000)
 assert pts,('ACTUAL_NATIVE_PATH',role,a,z);ids=[]
 for x,y in zip(pts,pts[1:]):
  tr=pcbnew.PCB_TRACK(b);tr.SetNet(b.FindNet(net));tr.SetStart(xy(x));tr.SetEnd(xy(y));tr.SetLayer(layer);tr.SetWidth(pcbnew.FromMM(width));b.Add(tr);g.add(tr);ids.append(tr.m_Uuid.AsString());added.append(dict(uuid=tr.m_Uuid.AsString(),identity=identity(tr),role=role))
 routes.append(dict(role=role,net=net,layer=b.GetLayerName(layer),width_mm=width,points_mm=pts,uuids=ids,length_mm=sum(math.dist(x,y)for x,y in zip(pts,pts[1:]))));print('ROUTE',role,pts,flush=True)
a=mm(ps['U11020','3'].GetPosition());z=mm(ps['U11019','4'].GetPosition());chosen=None
for rv in [(341.4375,173.35),(341.8,173.0),(340.8,173.0),(342.0,174.0)]:
 if not all(base_clear([rv,rv],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]):continue
 rp=next((p for p in paths(a,rv)if g.clear(p,n,pcbnew.F_Cu,.2)),None)
 if rp is None:continue
 for sv in [(344.1375,178.65),(344.2,178.65),(344.4,178.6)]:
  if not all(base_clear([sv,sv],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]):continue
  sp=next((p for p in paths(z,sv)if g.clear(p,n,pcbnew.F_Cu,.2)),None)
  if sp is None:continue
  for sx,sy in [(-1.3,0),(1.3,0),(0,-1.3),(0,1.3)]:
   for ry in [-1.3,1.3]:
    r1=(rv[0],rv[1]+ry);s1=(sv[0]+sx,sv[1]+sy)
    if not base_clear([rv,r1],n,pcbnew.B_Cu,.2) or not base_clear([sv,s1],n,pcbnew.B_Cu,.2):continue
    mid=next((p for p in paths(r1,s1)if g.clear(p,n,pcbnew.B_Cu,.2)),None)
    if mid is None:mid=g.grid(r1,s1,n,pcbnew.B_Cu,.2,step=.1,padding=8,max_nodes=50000)
    if mid:chosen=(rv,sv,rp,sp,[rv]+mid+[sv]);break
   if chosen:break
  if chosen:break
 if chosen:break
assert chosen,'NATIVE_TWO_TRANSFERS';rv,sv,rp,sp,bp=chosen
for pt,role in [(rv,'U11020_B_input_receiving_transfer'),(sv,'U11020_B_input_actual_Source_transfer')]:
 v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role=role))
for pts,layer,role in [(rp,pcbnew.F_Cu,'U11020_B_input_receiving_F'),(sp,pcbnew.F_Cu,'U11020_B_input_actual_Source_F'),(bp,pcbnew.B_Cu,'U11020_B_input_actual_reference_middle_B')]:
 ids=[]
 for x,y in zip(pts,pts[1:]):
  assert base_clear([x,y],n,layer,.2);v=pcbnew.PCB_TRACK(b);v.SetNet(b.FindNet(n));v.SetStart(xy(x));v.SetEnd(xy(y));v.SetLayer(layer);v.SetWidth(pcbnew.FromMM(.2));b.Add(v);g.add(v);ids.append(v.m_Uuid.AsString());added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role=role))
 routes.append(dict(role=role,net=n,layer=b.GetLayerName(layer),width_mm=.2,points_mm=pts,uuids=ids,length_mm=sum(math.dist(x,y)for x,y in zip(pts,pts[1:]))));print('ROUTE',role,pts,flush=True)
# Actual receiving transfer gets its own Source-ground escape; the Source-side
# transfer uses retained73987b32 at346.639139,178.532763 only if <=1mm.
source_ground=(sv[0]+.4,sv[1]+.65);assert math.dist(sv,source_ground)<=1.
assert all(base_clear([source_ground,source_ground],ground,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]),('B_SOURCE_GROUND',source_ground)
v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(ground));v.SetPosition(xy(source_ground));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role='U11020_B_input_actual_Source_Ground_stitch'));route(mm(ps['C11078','2'].GetPosition()),source_ground,ground,pcbnew.B_Cu,'U11020_B_input_actual_Source_Ground_short_escape',.25)
rg=(rv[0],rv[1]-.9);assert all(base_clear([rg,rg],ground,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]),('B_RECEIVING_GROUND',rg)
v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(ground));v.SetPosition(xy(rg));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role='U11020_B_input_actual_receiving_Ground_stitch'))
route(mm(ps['C11079','2'].GetPosition()),rg,ground,pcbnew.B_Cu,'U11020_B_input_receiving_Ground_Source_escape',.25)
for cap,point in [('C11079',(338.9125,173.45)),('C11081',(333.5875,186.05))]:
 p=ps[cap,'2'];net=p.GetNetname();assert all(base_clear([point,point],net,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]),('GND_VIA_NATIVE',cap,point)
 for tr in b.GetTracks():
  if tr.GetNetname()==net or isinstance(tr,pcbnew.PCB_VIA):continue
  if any(tr.IsOnLayer(l)for l in[pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu]):assert segment_distance(point,point,mm(tr.GetStart()),mm(tr.GetEnd()))>=.410+pcbnew.ToMM(tr.GetWidth())/2,('INNER_NATIVE_CU',cap,tr.m_Uuid.AsString())
 via=pcbnew.PCB_VIA(b);via.SetNet(b.FindNet(net));via.SetPosition(xy(point));via.SetWidth(pcbnew.FromMM(.5));via.SetDrill(pcbnew.FromMM(.2));via.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);via.SetViaType(pcbnew.VIATYPE_THROUGH);via.SetIsFree(True);via.SetRemoveUnconnected(False);b.Add(via);g.add(via);added.append(dict(uuid=via.m_Uuid.AsString(),identity=identity(via),role=cap+'_actual_local_cap_Ground_anchor'));route(mm(p.GetPosition()),point,net,pcbnew.B_Cu,cap+'_actual_cap_Ground_short_escape',.25)
P=O/'motherboard-two-health-local-anchor-control-candidate.kicad_pcb';pcbnew.SaveBoard(str(P),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),P.with_suffix(e))
for q in B.parent.iterdir():
 if q.is_dir()and(q.suffix=='.pretty'or q.name=='3dmodels'):shutil.copytree(q,O/q.name)
 elif q.name=='fp-lib-table':shutil.copyfile(q,O/q.name)
receipt=dict(before_board=str(B),before_sha256=sha(B),exact_added_copper=added,exact_retired_copper=[dict(uuid=u,identity=old[u])for u in sorted(ret)],routes=routes,all_component_Source_poses_and_power_barrels_unchanged=True,actual_control_reference_margin_mm=.40,extra_hole_search_margin_mm=.03,passed=False,strict_Source_annulus_and_current108_and_global_power_pending=True);(O/'path-staged.json').write_text(json.dumps(receipt,indent=2));pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();pcbnew.SaveBoard(str(P),b)
subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(P)],check=True,capture_output=True,text=True);d=json.loads((O/'drc.json').read_text());err=[q for q in d['violations']if q['severity']=='error'];receipt.update(candidate_sha256=sha(P),native_errors=err,native_types=dict(collections.Counter(q['type']for q in d['violations'])));(O/'receipt.json').write_text(json.dumps(receipt,indent=2));(O/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_scope_reason='Necessary actual health input route antipad avoidance and two off-land local receiving cap-Ground escapes; qualified Source/reference proof remains pending.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(ret)+[q['uuid']for q in added],reviewed_added_zone_UUIDs=[]),indent=2));assert not err,err;print('DONE',sha(P),len(added),len(ret),flush=True)
