import sys,json,math,shutil,subprocess,collections
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm,xy,identity
from hardware_route_local_signals import paths
from hardware_route_current_delivery_native import sha
B=Path('reports/motherboard-power-entry-20261001/ROOT101-U20-U26-direct-F-input-B-r246/motor-health-U26-direct-F-input-B-candidate.kicad_pcb')
O=Path('reports/motherboard-power-entry-20261001/ROOT101-health-private-LED-power-repair-r252');O.mkdir(exist_ok=False)
o=pcbnew.LoadBoard(str(B));old={t.m_Uuid.AsString():identity(t)for t in o.GetTracks()};ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in o.GetPads()if p.GetNumber()}
selected=[('U11020','6','U11022','2'),('U11026','4','U11030','2')];nets={ps[r,p].GetNetname()for r,p,s,q in selected};fieldn=ps['U11026','4'].GetNetname();coren=ps['U11020','6'].GetNetname();ret={t.m_Uuid.AsString()for t in o.GetTracks()if t.GetNetname()==fieldn or (not isinstance(t,pcbnew.PCB_VIA)and t.IsOnLayer(pcbnew.B_Cu)and t.GetNetname()==coren)}
t=parse(without_generated_fills(B.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'literal-two-private-B-graphs-retired.kicad_pcb';D.write_text(dump_board(t))
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};g=FastGeometry(b);base_clear=g.clear
from hardware_route_power_groups_native import hits
blocked=[(334.2675,186.78,335.9075,188.42),(335.5375,187.25,336.2375,187.95),(331.4125,187.1,332.4125,189.5),(335.3875,187.1,336.3875,189.5),(332.9375,189.75,333.9375,191.5)]
def guarded_clear(points,n,l,w):
 if not base_clear(points,n,l,w):return False
 if n==coren and l==pcbnew.B_Cu:
  for x,y in zip(points,points[1:]):
   for a,c,d,e in blocked:
    if hits(x,y,[(a,c),(d,c),(d,e),(a,e)],w/2+.25):return False
 return True
g.clear=guarded_clear;added=[];routes=[]
for r,p,s,q in selected:
 n=ps[r,p].GetNetname();assert n==ps[s,q].GetNetname();layer=pcbnew.F_Cu if n==fieldn else pcbnew.B_Cu
 if n==fieldn:a,z=mm(ps[r,p].GetPosition()),mm(ps[s,q].GetPosition())
 else:
  vias=[v for v in b.GetTracks()if isinstance(v,pcbnew.PCB_VIA)and v.GetNetname()==n];assert len(vias)==2,(n,len(vias));a,z=[mm(v.GetPosition())for v in vias]
 pts=next((v for v in paths(a,z)if g.clear(v,n,layer,.2)),None)
 if pts is None:pts=g.grid(a,z,n,layer,.2,step=.25,padding=30,max_nodes=300000)
 if pts is None:pts=g.grid(a,z,n,layer,.2,step=.1,padding=18,max_nodes=300000)
 assert pts,('No native-clear exact LED POWER B graph',n,a,z)
 ids=[]
 for x,y in zip(pts,pts[1:]):
  assert g.clear([x,y],n,layer,.2);tr=pcbnew.PCB_TRACK(b);tr.SetNet(b.FindNet(n));tr.SetStart(xy(x));tr.SetEnd(xy(y));tr.SetWidth(pcbnew.FromMM(.2));tr.SetLayer(layer);b.Add(tr);g.add(tr);ids.append(tr.m_Uuid.AsString());added.append(dict(uuid=tr.m_Uuid.AsString(),identity=identity(tr),role='actual_private_LED_POWER_B_'+r+'_'+p))
 routes.append(dict(actual_endpoints=[[r,p],[s,q]],net=n,layer=b.GetLayerName(layer),width_mm=.2,points_mm=pts,uuids=ids,length_mm=sum(math.dist(x,y)for x,y in zip(pts,pts[1:]))));print('ROUTE',n,len(ids),routes[-1]['length_mm'],flush=True);pcbnew.SaveBoard(str(O/('debug-'+r+'.kicad_pcb')),b)
P=O/'motherboard-health-private-LED-power-repaired-candidate.kicad_pcb';pcbnew.SaveBoard(str(P),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),P.with_suffix(e))
for p in B.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty'or p.name=='3dmodels'):shutil.copytree(p,O/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,O/p.name)
receipt=dict(before_board=str(B),before_sha256=sha(B),exact_added_copper=added,exact_retired_copper=[dict(uuid=u,identity=old[u])for u in sorted(ret)],routes=routes,power_only_LED_graphs=True,core_B_forbidden_receiving_envelopes=blocked,field_LED_continuous_F_no_transfer_vias=True,all_component_Source_and_poses_unchanged=True,passed=False,native_and_Source_qualification_pending=True)
(O/'path-staged.json').write_text(json.dumps(receipt,indent=2));pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();co=b.GetConnectivity();private=[]
for r in ['U11020','U11026']:
 for pn in ['1','3','4','6']:
  p=ps[r,pn];other=[q for q in b.GetPads()if q.GetNetname()==p.GetNetname()and q.m_Uuid.AsString()!=p.m_Uuid.AsString()];assert len(other)==1;q=other[0];ok=q.m_Uuid.AsString()in{v.m_Uuid.AsString()for v in co.GetConnectedItems(p)};assert ok;(private.append(dict(owner=[r,pn],actual_endpoint=[q.GetParentFootprint().GetReference(),q.GetNumber()],connected=ok)))
pcbnew.SaveBoard(str(P),b);subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(P)],check=True,capture_output=True,text=True);d=json.loads((O/'drc.json').read_text());err=[v for v in d['violations']if v['severity']=='error'];receipt.update(candidate_sha256=sha(P),actual_private_endpoints=private,native_errors=err,native_types=dict(collections.Counter(v['type']for v in d['violations'])),Source_complete=False);(O/'receipt.json').write_text(json.dumps(receipt,indent=2));(O/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_scope_reason='Necessary physical coexistence repair of the two existing health LED power-only B graphs; actual controls and Source unchanged.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(ret)+[q['uuid']for q in added],reviewed_added_zone_UUIDs=[]),indent=2));assert not err,err;print('DONE',sha(P),len(added),len(ret),flush=True)
