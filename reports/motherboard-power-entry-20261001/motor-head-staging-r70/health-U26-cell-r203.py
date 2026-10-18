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
B=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U26-cell-r203');O.mkdir(exist_ok=False);original=pcbnew.LoadBoard(str(B));original.BuildConnectivity();co=original.GetConnectivity();old={t.m_Uuid.AsString():identity(t)for t in original.GetTracks()};op={p.m_Uuid.AsString():pad_identity(p)for p in original.GetPads()};seen=set();groups=[]
for p in original.GetPads():
 u=p.m_Uuid.AsString()
 if u in seen:continue
 gg={u}|{q.m_Uuid.AsString()for q in co.GetConnectedItems(p)if q.Type()==pcbnew.PCB_PAD_T};seen|=gg
 if len(gg)>1:groups.append((u,gg))
h=json.loads(Path('reports/motherboard-power-entry-20261001/health-supply-r99/receipt.json').read_text());ret={v['uuid']for v in h['exact_added_copper']if v['role'].startswith(('U11026_own','FIELD_sink_actual_own_supply'))};ofs={f.GetReference():f for f in original.GetFootprints()};pns={p.GetNumber():p for p in ofs['U11026'].Pads()};control_source={}
for pn,p in pns.items():
 pt=mm(p.GetPosition());ret|={t.m_Uuid.AsString()for t in original.GetTracks()if t.GetNetname()==p.GetNetname()and (pt==mm(t.GetStart())or pt==mm(t.GetEnd()))}
for pn in['1','3']:
 n=pns[pn].GetNetname();other=[p for p in original.GetPads()if p.GetNetname()==n and p.GetParentFootprint().GetReference()!='U11026'];assert len(other)==1 and other[0].GetParentFootprint().GetReference()=='U11025';control_source[pn]=(other[0].GetParentFootprint().GetReference(),other[0].GetNumber());ret|={t.m_Uuid.AsString()for t in original.GetTracks()if t.GetNetname()==n}
t=parse(without_generated_fills(B.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'literal-retired-input.kicad_pcb';D.write_text(dump_board(t))
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));fs={f.GetReference():f for f in b.GetFootprints()};oldposes={r:dict(point_mm=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()))for r in['U11026','C11081']};fs['U11026'].SetPosition(xy((333.5,188)));fs['C11081'].SetPosition(xy((334.3375,187.225)))
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
pg=ps['U11026','5'].GetNetname();gn=ps['U11026','2'].GetNetname();pv=(335.0875,188);gv=(335.8875,188);og=(331.9125,188)
via(pv,pg,'U11026_local_positive_transfer');via(gv,gn,'U11026_local_Source_return_stitch');via(og,gn,'U11026_actual_ground_pin_transfer')
route(mm(ps['U11026','5'].GetPosition()),pv,pg,pcbnew.F_Cu,'U11026_own_positive_F');route(mm(ps['C11081','1'].GetPosition()),pv,pg,pcbnew.B_Cu,'U11026_own_positive_B');route(mm(ps['C11081','2'].GetPosition()),gv,gn,pcbnew.B_Cu,'U11026_own_bypass_return');route(mm(ps['U11026','2'].GetPosition()),og,gn,pcbnew.F_Cu,'U11026_actual_own_Ground_pin')
p=ps['U11026','1'];route(mm(p.GetPosition()),mm(ps[control_source['1']].GetPosition()),p.GetNetname(),pcbnew.F_Cu,'U11026_actual_input_1',.2)
p=ps['U11026','3'];cn=p.GetNetname();rv=(331.9125,188.85);sv=(332.5875,192.65);sg=(333.4375,192.65)
candidates=[];cp=mm(ps[control_source['3']].GetPosition());cg=mm(ps['C11080','2'].GetPosition())
for d in[.9,1.,1.25,1.5,2.,2.5,3.,4.]:
 for dx,dy in[(1,0),(-1,0),(0,1),(0,-1),(.707107,.707107),(-.707107,.707107),(.707107,-.707107),(-.707107,-.707107)]:
  v=(cp[0]+d*dx,cp[1]+d*dy)
  if not all(g.clear([v,v],cn,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):continue
  if not any(g.clear(q,cn,pcbnew.F_Cu,.2)for q in paths(cp,v)):continue
  for ex,ey in[(.85,0),(-.85,0),(0,.85),(0,-.85),(.6,.6),(-.6,.6),(.6,-.6),(-.6,-.6)]:
   q=(v[0]+ex,v[1]+ey)
   if not all(g.clear([q,q],gn,l,.5)for l in[pcbnew.F_Cu,pcbnew.B_Cu]):continue
   if any(g.clear(z,gn,pcbnew.B_Cu,.25)for z in paths(cg,q)):candidates.append((v,q))
assert candidates,'U25_FIELD_Y2_SOURCE_PAIR';sv,sg=candidates[0];print('SOURCE_Y2_PAIR',sv,sg,flush=True)
via(rv,cn,'U11026_input_3_receiving_transfer');via(sv,cn,'U11026_input_3_actual_SOURCE_transfer');via(sg,gn,'U11026_input_3_actual_SOURCE_return_stitch');route(mm(ps['C11080','2'].GetPosition()),sg,gn,pcbnew.B_Cu,'U11026_input_3_SOURCE_return_to_C11080',.25);route(mm(p.GetPosition()),rv,cn,pcbnew.F_Cu,'U11026_input_3_receiving_F',.2);route(mm(ps[control_source['3']].GetPosition()),sv,cn,pcbnew.F_Cu,'U11026_input_3_SOURCE_F',.2);route(rv,sv,cn,pcbnew.B_Cu,'U11026_input_3_actual_source_B',.2)
for pn,rv,sv in [('4',(335.3375,188.95),(327.5875,191.65)),('6',(335.3375,187.05),(329.0875,190.35))]:
 p=ps['U11026',pn];n=p.GetNetname();via(rv,n,'U11026_LED_POWER_'+pn+'_local_transfer');route(mm(p.GetPosition()),rv,n,pcbnew.F_Cu,'U11026_LED_POWER_'+pn+'_F',.2);route(rv,sv,n,pcbnew.B_Cu,'U11026_LED_POWER_'+pn+'_B',.2)
route(pv,(332.5875,191),pg,pcbnew.B_Cu,'U11026_actual_field_supply_from_U11025',.25)
debug();pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();co=b.GetConnectivity();pm={p.m_Uuid.AsString():p for p in b.GetPads()}
for u,gg in groups:assert gg<=({u}|{p.m_Uuid.AsString()for p in co.GetConnectedItems(pm[u])if p.Type()==pcbnew.PCB_PAD_T}),('SOURCE',u,gg-({u}|{p.m_Uuid.AsString()for p in co.GetConnectedItems(pm[u])if p.Type()==pcbnew.PCB_PAD_T}))
for ref,pn,target,tp in[('U11026','5','C11081','1'),('U11026','2','C11081','2'),('U11026','5','C11055','1'),('U11026','2','C11055','2')]:assert ps[target,tp].m_Uuid.AsString()in{p.m_Uuid.AsString()for p in co.GetConnectedItems(ps[ref,pn])},('OWNER',ref,pn,target,tp)
D=O/'motor-health-U26-cell-candidate.kicad_pcb';pcbnew.SaveBoard(str(D),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(D)],check=True,capture_output=True,text=True);d=json.loads((O/'drc.json').read_text());err=[v for v in d['violations']if v['severity']=='error']
(O/'receipt.json').write_text(json.dumps(dict(before_board=str(B),before_sha256=sha(B),candidate_sha256=sha(D),exact_added_copper=added,exact_retired_copper=[dict(uuid=u,identity=old[u])for u in sorted(ret)],old_poses=oldposes,new_poses={r:dict(point_mm=mm(fs[r].GetPosition()),angle=fs[r].GetOrientationDegrees(),layer=b.GetLayerName(fs[r].GetLayer()))for r in oldposes},routes=routes,old_source_clusters_preserved=len(groups),native_errors=err,native_types=dict(collections.Counter(v['type']for v in d['violations'])),pending=['Strict actual receiving return and two logic input reference routes','Actual relative IO3 backbone guard']),indent=2));(O/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_footprint_references=list(oldposes),reviewed_copper_delta_UUIDs=sorted(ret)+[r['uuid']for r in added],reviewed_added_zone_UUIDs=[]),indent=2));assert not err,err;print('DONE',sha(D),len(added),len(ret),flush=True)
