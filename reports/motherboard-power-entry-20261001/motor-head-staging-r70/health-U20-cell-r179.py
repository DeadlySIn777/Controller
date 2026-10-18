import sys,json,shutil,math,subprocess,collections
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm,xy,identity,pad_identity
from hardware_route_local_signals import paths
from hardware_route_current_delivery_native import sha
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
B=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-cell-r179');O.mkdir(exist_ok=False);original=pcbnew.LoadBoard(str(B));original.BuildConnectivity();co=original.GetConnectivity();old={t.m_Uuid.AsString():identity(t)for t in original.GetTracks()};op={p.m_Uuid.AsString():pad_identity(p)for p in original.GetPads()};seen=set();groups=[]
for p in original.GetPads():
 u=p.m_Uuid.AsString()
 if u in seen:continue
 gg={u}|{q.m_Uuid.AsString()for q in co.GetConnectedItems(p)if q.Type()==pcbnew.PCB_PAD_T};seen|=gg
 if len(gg)>1:groups.append((u,gg))
frozen=json.loads(Path('reports/motherboard-power-entry-20261001/ROOT94-health-four-loop-gap-r166/U20-two-part-cell-candidates-r176.json').read_text());ret=set(frozen['retired']);t=parse(without_generated_fills(B.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'literal-retired-input.kicad_pcb';D.write_text(dump_board(t))
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));fs={f.GetReference():f for f in b.GetFootprints()};oldposes={r:dict(point_mm=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()))for r in['U11020','C11079']};fs['U11020'].SetPosition(xy((339,175)));fs['C11079'].SetPosition(xy((339.8375,174.225)))
for r in oldposes:
 for z in fs.values():
  if z.GetReference()!=r and z.GetLayer()==fs[r].GetLayer():assert not intersects(side_box(fs[r]),side_box(z),0),('COURT',r,z.GetReference())
ps={(f.GetReference(),p.GetNumber()):p for f in fs.values()for p in f.Pads()if p.GetNumber()};g=FastGeometry(b);added=[];routes=[]
def debug():
 pcbnew.SaveBoard(str(O/'debug.kicad_pcb'),b);(O/'debug.json').write_text(json.dumps(dict(routes=routes,added=added),indent=2))
def via(pt,n,role):
 assert all(g.clear([pt,pt],n,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]),('VIA',role,pt)
 v=pcbnew.PCB_VIA(b);v.SetNet(b.FindNet(n));v.SetPosition(xy(pt));v.SetWidth(pcbnew.FromMM(.5));v.SetDrill(pcbnew.FromMM(.2));v.SetViaType(pcbnew.VIATYPE_THROUGH);v.SetLayerPair(pcbnew.F_Cu,pcbnew.B_Cu);v.SetIsFree(True);v.SetRemoveUnconnected(False);b.Add(v);g.add(v);added.append(dict(uuid=v.m_Uuid.AsString(),identity=identity(v),role=role));return v

def route(a,z,n,l,role,w=.25):
 points=next((v for v in paths(a,z)if g.clear(v,n,l,w)),None)
 if points is None:points=g.grid(a,z,n,l,w,step=.1,padding=5,max_nodes=45000)
 if not points:debug();raise AssertionError(('ROUTE',role,a,z))
 ids=[]
 for s,e in zip(points,points[1:]):
  t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetStart(xy(s));t.SetEnd(xy(e));t.SetLayer(l);t.SetWidth(pcbnew.FromMM(w));b.Add(t);g.add(t);ids.append(t.m_Uuid.AsString());added.append(dict(uuid=ids[-1],identity=identity(t),role=role))
 routes.append(dict(role=role,net=n,layer=b.GetLayerName(l),width_mm=w,points_mm=points,uuids=ids,length_mm=sum(math.dist(s,e)for s,e in zip(points,points[1:]))));print(role,routes[-1]['length_mm'],flush=True)
pg=ps['U11020','5'].GetNetname();gn=ps['U11020','2'].GetNetname();pv=(340.5875,175);gv=(341.1875,175.6);og=(337.4125,175)
via(pv,pg,'U11020_local_positive_transfer');via(gv,gn,'U11020_local_Source_return_stitch');via(og,gn,'U11020_actual_ground_pin_transfer')
route(mm(ps['U11020','5'].GetPosition()),pv,pg,pcbnew.F_Cu,'U11020_own_positive_F');route(mm(ps['C11079','1'].GetPosition()),pv,pg,pcbnew.B_Cu,'U11020_own_positive_B');route(mm(ps['C11079','2'].GetPosition()),gv,gn,pcbnew.B_Cu,'U11020_own_bypass_return');route(mm(ps['U11020','2'].GetPosition()),og,gn,pcbnew.F_Cu,'U11020_actual_own_Ground_pin')
# Reattach the exact former external endpoint of each moved pin leaf.
for pn,anchor in [('5',(345.3375,175)),('1',(343.8625,174.35)),('3',(343.1625,176.65)),('4',(346.85,175.65)),('6',(344.85,174.135))]:
 p=ps['U11020',pn];route(mm(p.GetPosition()),anchor,p.GetNetname(),pcbnew.F_Cu,'U11020_reconnect_actual_pin_'+pn,.3 if pn=='5'else.2)
debug();pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();co=b.GetConnectivity();pm={p.m_Uuid.AsString():p for p in b.GetPads()}
for u,gg in groups:assert gg<=({u}|{p.m_Uuid.AsString()for p in co.GetConnectedItems(pm[u])if p.Type()==pcbnew.PCB_PAD_T}),('SOURCE',u,gg-({u}|{p.m_Uuid.AsString()for p in co.GetConnectedItems(pm[u])if p.Type()==pcbnew.PCB_PAD_T}))
for ref,pn,target,tp in[('U11020','5','C11079','1'),('U11020','2','C11079','2'),('U11020','5','C11029','1'),('U11020','2','C11088','2')]:assert ps[target,tp].m_Uuid.AsString()in{p.m_Uuid.AsString()for p in co.GetConnectedItems(ps[ref,pn])},('OWNER',ref,pn,target,tp)
D=O/'motor-health-U20-cell-candidate.kicad_pcb';pcbnew.SaveBoard(str(D),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(D)],check=True,capture_output=True,text=True);d=json.loads((O/'drc.json').read_text());err=[v for v in d['violations']if v['severity']=='error']
(O/'receipt.json').write_text(json.dumps(dict(before_board=str(B),before_sha256=sha(B),candidate_sha256=sha(D),exact_added_copper=added,exact_retired_copper=[dict(uuid=u,identity=old[u])for u in sorted(ret)],old_poses=oldposes,new_poses={r:dict(point_mm=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()))for r in oldposes},routes=routes,old_source_clusters_preserved=len(groups),native_errors=err,native_types=dict(collections.Counter(v['type']for v in d['violations'])),pending=['Strict actual receiving return and two logic input reference routes','Actual relative IO3 backbone guard']),indent=2));(O/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_footprint_references=list(oldposes),reviewed_copper_delta_UUIDs=sorted(ret)+[r['uuid']for r in added],reviewed_added_zone_UUIDs=[]),indent=2));assert not err,err;print('DONE',sha(D),len(added),len(ret),flush=True)
