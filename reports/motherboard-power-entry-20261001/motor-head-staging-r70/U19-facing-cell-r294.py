import sys,json,math,collections,shutil,subprocess
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import identity,mm,xy,segment_distance,pad_identity
from hardware_route_local_signals import paths,GeometryIndex
from hardware_route_current_delivery_native import sha
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT101-health-U19-facing-cell-r294');O.mkdir(exist_ok=False);original=pcbnew.LoadBoard(str(B));original.BuildConnectivity();of={f.GetReference():f for f in original.GetFootprints()};ops={(r,p.GetNumber()):p for r,f in of.items()for p in f.Pads()if p.GetNumber()};old={t.m_Uuid.AsString():identity(t)for t in original.GetTracks()};oldposes={r:dict(point_mm=mm(of[r].GetPosition()),angle=of[r].GetOrientationDegrees(),layer=original.GetLayerName(of[r].GetLayer()))for r in ['U11019','C11078']};co=original.GetConnectivity();groups=[];seen=set()
for p in original.GetPads():
 u=p.m_Uuid.AsString()
 if u in seen:continue
 gg={u}|{q.m_Uuid.AsString()for q in co.GetConnectedItems(p)if q.Type()==pcbnew.PCB_PAD_T};seen|=gg
 if len(gg)>1:groups.append((u,gg))
nets=[ops['U11019',p].GetNetname()for p in ['4','6']];ret={t.m_Uuid.AsString()for t in original.GetTracks()if t.GetNetname()in nets}|{'448060d2-6859-4acf-bfe0-75f7029b605a','95eb2e15-8dac-4594-8842-3b785c3f6e83','350392b6-1787-4cb8-8284-38dee462b990','217f09e5-9485-40ce-8274-5c93d67456ab'}
for r in ['U11019','C11078']:
 for p in of[r].Pads():
  pt=mm(p.GetPosition());ret|={t.m_Uuid.AsString()for t in original.GetTracks()if not isinstance(t,pcbnew.PCB_VIA)and t.GetNetname()==p.GetNetname()and pt in[mm(t.GetStart()),mm(t.GetEnd())]}
t=parse(without_generated_fills(B.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'literal-retired-U19-input.kicad_pcb';D.write_text(dump_board(t))
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));fs={f.GetReference():f for f in b.GetFootprints()};fs['U11019'].SetPosition(xy((342.8,175)));fs['U11019'].SetOrientationDegrees(180);fs['C11078'].SetPosition(xy((343.25,178.075)));fs['C11078'].SetOrientationDegrees(-90)
for r in oldposes:
 assert not[(r,z.GetReference())for z in fs.values()if z.GetReference()!=r and z.GetLayer()==fs[r].GetLayer()and intersects(side_box(fs[r]),side_box(z),0)],('COURT',r)
ps={(r,p.GetNumber()):p for r,f in fs.items()for p in f.Pads()if p.GetNumber()};g=FastGeometry(b);base_clear=g.clear;ground=ps['U11019','2'].GetNetname();positive=ps['U11019','5'].GetNetname();added=[];routes=[]
def save():pcbnew.SaveBoard(str(O/'debug.kicad_pcb'),b);(O/'debug.json').write_text(json.dumps(dict(routes=routes,added=added),indent=2))
def via(q,n,role):
 if not all(base_clear([q,q],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):save();raise AssertionError(('VIA',q,n,role))
 for tr in b.GetTracks():
  if isinstance(tr,pcbnew.PCB_VIA)or tr.GetNetname()==n:continue
  if any(tr.IsOnLayer(l)for l in[pcbnew.In1_Cu,pcbnew.In2_Cu,pcbnew.In3_Cu,pcbnew.In4_Cu]):assert segment_distance(q,q,mm(tr.GetStart()),mm(tr.GetEnd()))>=.410+pcbnew.ToMM(tr.GetWidth())/2,('INNER',role,tr.m_Uuid.AsString())
 v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(q));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role=role));return v

def route(points,n,l,role,w=.25,auto=False,guard=False):
 def valid(v):
  if not base_clear(v,n,l,w):return False
  if guard:
   for tr in b.GetTracks():
    if not isinstance(tr,pcbnew.PCB_VIA)or tr.GetNetname()in[n,ground]:continue
    c=mm(tr.GetPosition());r=pcbnew.ToMM(tr.GetWidth(pcbnew.F_Cu))/2+.2505
    if any(segment_distance(s,e,c,c)<r+w/2+.40+.03 for s,e in zip(v,v[1:])):return False
  return True
 pts=[tuple(v)for v in points]
 if auto:pts=next((v for v in paths(pts[0],pts[-1])if valid(v)),None)
 if not pts or not valid(pts):save();raise AssertionError(('PATH',role,points))
 ids=[]
 for x,y in zip(pts,pts[1:]):
  if math.dist(x,y)<1e-8:continue
  tr=pcbnew.PCB_TRACK(b);tr.SetNet(b.FindNet(n));tr.SetStart(xy(x));tr.SetEnd(xy(y));tr.SetLayer(l);tr.SetWidth(pcbnew.FromMM(w));b.Add(tr);g.add(tr);ids.append(tr.m_Uuid.AsString());added.append(dict(uuid=ids[-1],identity=identity(tr),role=role))
 routes.append(dict(role=role,net=n,layer=b.GetLayerName(l),width_mm=w,points_mm=pts,uuids=ids,length_mm=sum(math.dist(x,y)for x,y in zip(pts,pts[1:]))));print('ROUTE',role,pts,flush=True)
# Reuse the old two exact reference-hole centres for the new local VCC and receiving Ground.
pv=(343.,176.3);gv=(343.84756,176.36006);og=(344.3875,175);cg=(342.25,178.85)
for q,n,role in[(pv,positive,'U11019_local_positive_transfer'),(gv,ground,'U11019_local_RECEIVING_Ground'),(og,ground,'U11019_actual_owner_Ground'),(cg,ground,'C11078_actual_off_land_Ground')]:via(q,n,role)
route([mm(ps['U11019','5'].GetPosition()),(342.8,175),(342.8,176.3),pv],positive,pcbnew.F_Cu,'U11019_own_local_VCC_F')
route([mm(ps['C11078','1'].GetPosition()),pv],positive,pcbnew.B_Cu,'U11019_own_local_VCC_B',auto=True)
route([pv,(345.85,178)],positive,pcbnew.B_Cu,'U11019_actual_CORE_supply_distribution',.3,auto=True)
route([mm(ps['U11019','2'].GetPosition()),og],ground,pcbnew.F_Cu,'U11019_actual_owner_Ground_short')
route([mm(ps['C11078','2'].GetPosition()),cg],ground,pcbnew.B_Cu,'C11078_actual_local_Ground_short')
route([gv,(342.4125,178)],ground,pcbnew.F_Cu,'U11019_receiving_Ground_to_actual_Source',.25,auto=True)
for rp,up in [('1','6'),('3','4')]:route([mm(ps['U11020',rp].GetPosition()),mm(ps['U11019',up].GetPosition())],ps['U11020',rp].GetNetname(),pcbnew.F_Cu,'U11020_actual_input_'+rp+'_short_F',.2,auto=True,guard=True)
# Local input duplication preserves actual source semantics. The remote MC_RAILS producer path remains explicitly unrouted.
n=ps['U11019','1'].GetNetname();assert n==ps['U11019','3'].GetNetname();route([mm(ps['U11019','1'].GetPosition()),(345.6375,175.65),(345.6375,174.35),mm(ps['U11019','3'].GetPosition())],n,pcbnew.F_Cu,'U11019_actual_common_health_input_local_tie',.2)
for cap,point in [('C11079',(337.4125,173.45)),('C11081',(335.3875,186.65))]:
 p=ps[cap,'2'];n=p.GetNetname();via(point,n,cap+'_actual_off_land_local_Ground');route([mm(p.GetPosition()),point],n,pcbnew.B_Cu,cap+'_actual_short_local_Ground',.25,auto=True)
P=O/'motherboard-health-U19-facing-cell-candidate.kicad_pcb';pcbnew.SaveBoard(str(P),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),P.with_suffix(e))
for q in B.parent.iterdir():
 if q.is_dir()and(q.suffix=='.pretty'or q.name=='3dmodels'):shutil.copytree(q,O/q.name)
 elif q.name=='fp-lib-table':shutil.copyfile(q,O/q.name)
receipt=dict(before_board=str(B),before_sha256=sha(B),old_poses=oldposes,new_poses={r:dict(point_mm=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()))for r in oldposes},exact_added_copper=added,exact_retired_copper=[dict(uuid=u,identity=old[u])for u in sorted(ret)],routes=routes,Source_unchanged=True,passed=False,remaining=['Actual remote MC_RAILS_OK_5V producer path','Strict Source/native reference and receiving loop rebind','Full relative IO3/CORE power guard']);(O/'path-staged.json').write_text(json.dumps(receipt,indent=2));pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();pcbnew.SaveBoard(str(P),b);co=b.GetConnectivity();pm={p.m_Uuid.AsString():p for p in b.GetPads()};splits=[]
for u,gg in groups:
 remain=gg-({u}|{p.m_Uuid.AsString()for p in co.GetConnectedItems(pm[u])if p.Type()==pcbnew.PCB_PAD_T})
 if remain:splits.append(dict(source=u,missing=sorted(remain)))
subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(P)],check=True,capture_output=True,text=True);d=json.loads((O/'drc.json').read_text());receipt.update(candidate_sha256=sha(P),native_errors=[q for q in d['violations']if q['severity']=='error'],native_types=dict(collections.Counter(q['type']for q in d['violations'])),prior_Source_cluster_splits=splits,native_uncapped_joins=b.GetConnectivity().GetUnconnectedCount(False));(O/'receipt.json').write_text(json.dumps(receipt,indent=2));(O/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_footprint_references=list(oldposes),reviewed_copper_delta_UUIDs=sorted(ret)+[q['uuid']for q in added],reviewed_added_zone_UUIDs=[]),indent=2));print('DONE',sha(P),receipt['native_types'],len(splits),flush=True)


