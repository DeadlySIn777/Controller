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
B=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-cell-r193');O.mkdir(exist_ok=False);original=pcbnew.LoadBoard(str(B));original.BuildConnectivity();co=original.GetConnectivity();old={t.m_Uuid.AsString():identity(t)for t in original.GetTracks()};op={p.m_Uuid.AsString():pad_identity(p)for p in original.GetPads()};seen=set();groups=[]
for p in original.GetPads():
 u=p.m_Uuid.AsString()
 if u in seen:continue
 gg={u}|{q.m_Uuid.AsString()for q in co.GetConnectedItems(p)if q.Type()==pcbnew.PCB_PAD_T};seen|=gg
 if len(gg)>1:groups.append((u,gg))
frozen=json.loads(Path('reports/motherboard-power-entry-20261001/ROOT94-health-four-loop-gap-r166/U20-two-part-cell-candidates-r176.json').read_text());ret=set(frozen['retired']);original_ps={(f.GetReference(),p.GetNumber()):p for f in original.GetFootprints()for p in f.Pads()if p.GetNumber()};control_source={}
for pn in['1','3']:
 n=original_ps['U11020',pn].GetNetname();other=[p for p in original.GetPads()if p.GetNetname()==n and p.GetParentFootprint().GetReference()!='U11020'];assert len(other)==1 and other[0].GetParentFootprint().GetReference()=='U11019';control_source[pn]=(other[0].GetParentFootprint().GetReference(),other[0].GetNumber());ret|={t.m_Uuid.AsString()for t in original.GetTracks()if t.GetNetname()==n}
for pn in['4','6']:
 n=original_ps['U11020',pn].GetNetname();ret|={t.m_Uuid.AsString()for t in original.GetTracks()if t.GetNetname()==n}
ret-={'8b76be20-4f22-4741-b6f6-b7150c195020','cdb2b347-fd52-4b51-8258-07f2f94d7ba7','881c2e60-ce80-40f5-ba25-23299c7aa94e','3dd7e290-39bc-4c38-9bdb-7cd9ff4a697a'}
t=parse(without_generated_fills(B.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'literal-retired-input.kicad_pcb';D.write_text(dump_board(t))
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));fs={f.GetReference():f for f in b.GetFootprints()};oldposes={r:dict(point_mm=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()))for r in['U11020','C11079']};fs['U11020'].SetPosition(xy((339,175)));fs['U11020'].SetOrientationDegrees(180);fs['C11079'].SetPosition(xy((338.1625,174.225)))
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
 if points is None:points=g.grid(a,z,n,l,w,step=.1,padding=15,max_nodes=500000)
 if not points:debug();raise AssertionError(('ROUTE',role,a,z))
 ids=[]
 for s,e in zip(points,points[1:]):
  t=pcbnew.PCB_TRACK(b);t.SetNet(b.FindNet(n));t.SetStart(xy(s));t.SetEnd(xy(e));t.SetLayer(l);t.SetWidth(pcbnew.FromMM(w));b.Add(t);g.add(t);ids.append(t.m_Uuid.AsString());added.append(dict(uuid=ids[-1],identity=identity(t),role=role))
 routes.append(dict(role=role,net=n,layer=b.GetLayerName(l),width_mm=w,points_mm=points,uuids=ids,length_mm=sum(math.dist(s,e)for s,e in zip(points,points[1:]))));print(role,routes[-1]['length_mm'],flush=True)
pg=ps['U11020','5'].GetNetname();gn=ps['U11020','2'].GetNetname();pv=(337.4125,175);gv=(336.8,175.6);og=(340.5875,175)
via(pv,pg,'U11020_local_positive_transfer');via(gv,gn,'U11020_local_Source_return_stitch');via(og,gn,'U11020_actual_ground_pin_transfer')
route(mm(ps['U11020','5'].GetPosition()),pv,pg,pcbnew.F_Cu,'U11020_own_positive_F');route(mm(ps['C11079','1'].GetPosition()),pv,pg,pcbnew.B_Cu,'U11020_own_positive_B');route(mm(ps['C11079','2'].GetPosition()),gv,gn,pcbnew.B_Cu,'U11020_own_bypass_return');route(mm(ps['U11020','2'].GetPosition()),og,gn,pcbnew.F_Cu,'U11020_actual_own_Ground_pin')
# Reattach two logic inputs through their actual retained source transfers.
for pn,rv,sv,sg in [('1',(340.6875,175.85),(343.847560,176.360060),(343.0,176.3)),('3',(340.5875,174.15),(344.1375,178.65),(344.1375,179.5))]:
 p=ps['U11020',pn];cn=p.GetNetname();via(rv,cn,'U11020_input_'+pn+'_actual_receiving_transfer');via(sg,gn,'U11020_input_'+pn+'_actual_SOURCE_Ground_stitch');route(mm(p.GetPosition()),rv,cn,pcbnew.F_Cu,'U11020_input_'+pn+'_actual_receiving_F',.2);route(rv,sv,cn,pcbnew.B_Cu,'U11020_input_'+pn+'_actual_source_B',.2)
# Preserve the actual Source Ground at the output-side source transfer.
route((344.1375,179.5),mm(ps['C11078','2'].GetPosition()),gn,pcbnew.B_Cu,'U11020_input_3_SOURCE_Ground_to_actual_C11078',.25)
for pn,rv,other,sv in [('4',(336.5,177),('U11024','2'),(347.6,173.635)),('6',(336.5,178),('U11022','2'),(271.6,234.635))]:
 p=ps['U11020',pn];n=p.GetNetname();via(rv,n,'U11020_LED_POWER_'+pn+'_receiving_transfer');via(sv,n,'U11020_LED_POWER_'+pn+'_actual_contact_transfer');route(mm(ps[other].GetPosition()),sv,n,pcbnew.F_Cu,'U11020_LED_POWER_'+pn+'_actual_contact_F',.2);route(mm(p.GetPosition()),rv,n,pcbnew.F_Cu,'U11020_LED_POWER_'+pn+'_receiving_F',.2);route(rv,sv,n,pcbnew.B_Cu,'U11020_LED_POWER_'+pn+'_actual_contact_B',.2)
route(mm(ps['U11020','5'].GetPosition()),(345.3375,175),pg,pcbnew.F_Cu,'U11020_actual_CORE_source_reconnection',.3)
debug();pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();co=b.GetConnectivity();pm={p.m_Uuid.AsString():p for p in b.GetPads()}
for u,gg in groups:assert gg<=({u}|{p.m_Uuid.AsString()for p in co.GetConnectedItems(pm[u])if p.Type()==pcbnew.PCB_PAD_T}),('SOURCE',u,gg-({u}|{p.m_Uuid.AsString()for p in co.GetConnectedItems(pm[u])if p.Type()==pcbnew.PCB_PAD_T}))
for ref,pn,target,tp in[('U11020','5','C11079','1'),('U11020','2','C11079','2'),('U11020','5','C11029','1'),('U11020','2','C11088','2')]:assert ps[target,tp].m_Uuid.AsString()in{p.m_Uuid.AsString()for p in co.GetConnectedItems(ps[ref,pn])},('OWNER',ref,pn,target,tp)
D=O/'motor-health-U20-cell-candidate.kicad_pcb';pcbnew.SaveBoard(str(D),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(D)],check=True,capture_output=True,text=True);d=json.loads((O/'drc.json').read_text());err=[v for v in d['violations']if v['severity']=='error']
(O/'receipt.json').write_text(json.dumps(dict(before_board=str(B),before_sha256=sha(B),candidate_sha256=sha(D),exact_added_copper=added,exact_retired_copper=[dict(uuid=u,identity=old[u])for u in sorted(ret)],old_poses=oldposes,new_poses={r:dict(point_mm=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()))for r in oldposes},routes=routes,old_source_clusters_preserved=len(groups),native_errors=err,native_types=dict(collections.Counter(v['type']for v in d['violations'])),pending=['Strict actual receiving return and two logic input reference routes','Actual relative IO3 backbone guard']),indent=2));(O/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_footprint_references=list(oldposes),reviewed_copper_delta_UUIDs=sorted(ret)+[r['uuid']for r in added],reviewed_added_zone_UUIDs=[]),indent=2));assert not err,err;print('DONE',sha(D),len(added),len(ret),flush=True)
