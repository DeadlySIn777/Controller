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
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-U20-U26-actual-unfilled-composition-r01/motherboard-U20-U26-unfilled-candidate.kicad_pcb')
R=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U26-cell-Source-pending-r235/receipt.json')
O=Path('reports/motherboard-power-entry-20261001/ROOT101-U20-U26-direct-F-input-B-r246');O.mkdir(exist_ok=False)
r=json.loads(R.read_text());original=pcbnew.LoadBoard(str(B));old={t.m_Uuid.AsString():identity(t)for t in original.GetTracks()};ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in original.GetPads()if p.GetNumber()};n=ps['U11026','3'].GetNetname();ret={t.m_Uuid.AsString()for t in original.GetTracks()if t.GetNetname()==n}
ret|={q['uuid']for q in r['exact_added_copper']if q['role'] in ['U11026_input_3_actual_SOURCE_return_stitch','U11026_input_3_SOURCE_return_to_C11080']};assert ret<=set(old)
t=parse(without_generated_fills(B.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'literal-input-B-retired.kicad_pcb';D.write_text(dump_board(t))
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()};g=FastGeometry(b);a=mm(ps['U11026','3'].GetPosition());z=mm(ps['U11025','4'].GetPosition());assert n==ps['U11025','4'].GetNetname();pts=next((v for v in paths(a,z)if g.clear(v,n,pcbnew.F_Cu,.2)),None)
if pts is None:pts=g.grid(a,z,n,pcbnew.F_Cu,.2,step=.1,padding=12,max_nodes=500000)
assert pts,'No actual native-clear continuous-F input B path';added=[]
for s,e in zip(pts,pts[1:]):
 assert g.clear([s,e],n,pcbnew.F_Cu,.2)
 tr=pcbnew.PCB_TRACK(b);tr.SetNet(b.FindNet(n));tr.SetStart(xy(s));tr.SetEnd(xy(e));tr.SetWidth(pcbnew.FromMM(.2));tr.SetLayer(pcbnew.F_Cu);b.Add(tr);g.add(tr);added.append(dict(uuid=tr.m_Uuid.AsString(),identity=identity(tr),role='U11026_actual_input_3_continuous_F'))
P=O/'motor-health-U26-direct-F-input-B-candidate.kicad_pcb';pcbnew.SaveBoard(str(P),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),P.with_suffix(e))
for p in B.parent.iterdir():
 if p.is_dir()and(p.suffix=='.pretty' or p.name=='3dmodels'):shutil.copytree(p,O/p.name)
 elif p.name=='fp-lib-table':shutil.copyfile(p,O/p.name)
receipt=dict(before_board=str(B),before_sha256=sha(B),receipt_input_sha256=sha(R),exact_added_copper=added,exact_retired_copper=[dict(uuid=u,identity=old[u])for u in sorted(ret)],actual_route=dict(role='U11026_actual_input_3_continuous_F',net=n,layer='F.Cu',width_mm=.2,points_mm=pts,uuids=[q['uuid']for q in added],length_mm=sum(math.dist(s,e)for s,e in zip(pts,pts[1:]))),signal_transfer_vias=0,all_component_poses_and_Source_unchanged=True,passed=False,native_and_Source_and_reference_qualification_pending=True,manufacturing_ready=False)
(O/'path-staged.json').write_text(json.dumps(receipt,indent=2));print('PHYSICAL_PATH',pts,flush=True)
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();co=b.GetConnectivity();private=[]
for pn in ['1','3','4','6']:
 p=ps['U11026',pn];other=[q for q in b.GetPads()if q.GetNetname()==p.GetNetname()and q.m_Uuid.AsString()!=p.m_Uuid.AsString()];assert len(other)==1;q=other[0];ok=q.m_Uuid.AsString()in{v.m_Uuid.AsString()for v in co.GetConnectedItems(p)};assert ok;private.append(dict(pin=pn,actual_endpoint=[q.GetParentFootprint().GetReference(),q.GetNumber()],connected=ok))
pcbnew.SaveBoard(str(P),b);subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(P)],check=True,capture_output=True,text=True);d=json.loads((O/'drc.json').read_text());err=[v for v in d['violations']if v['severity']=='error'];receipt.update(candidate_sha256=sha(P),actual_private_endpoints=private,native_errors=err,native_types=dict(collections.Counter(v['type']for v in d['violations'])),Source_complete=False);(O/'receipt.json').write_text(json.dumps(receipt,indent=2));(O/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_scope_reason='Necessary Source-specific health input B direct F route removes actual two signal transfers and obsolete Source-return stitch; qualification pending.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(ret)+[q['uuid']for q in added],reviewed_added_zone_UUIDs=[]),indent=2));assert not err,err;print('DONE',sha(P),len(added),len(ret),flush=True)
