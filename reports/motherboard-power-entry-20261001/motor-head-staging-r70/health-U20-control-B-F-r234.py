import sys,json,shutil,math,subprocess,collections
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_build_assembly import parse,child,value
from hardware_merge_bounded_pcb_delta import dump_board,without_generated_fills
from hardware_fix_motor_receiving_heads_native import FastGeometry
from hardware_route_logic_return import mm,xy,identity
from hardware_route_local_signals import paths
from hardware_route_current_delivery_native import sha
B=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-offland-return-r214/motor-health-U20-cell-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-control-B-F-r234');O.mkdir(exist_ok=False)
r=json.loads((B.parent/'receipt.json').read_text());probe=pcbnew.LoadBoard(str(B));pn=next(p for p in probe.GetPads()if p.GetParentFootprint().GetReference()=='U11020'and p.GetNumber()=='3');n=pn.GetNetname();ret={t.m_Uuid.AsString()for t in probe.GetTracks()if t.GetNetname()==n};t=parse(without_generated_fills(B.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'literal-B-path-retired.kicad_pcb';D.write_text(dump_board(t))
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));g=FastGeometry(b);p=next(p for p in b.GetPads()if p.GetParentFootprint().GetReference()=='U11020'and p.GetNumber()=='3');n=p.GetNetname()
a=(344.8375,178.65);z=(339.8375,174.35);pts=next((p for p in paths(a,z)if g.clear(p,n,pcbnew.F_Cu,.2)),None)
if pts is None:pts=g.grid(a,z,n,pcbnew.F_Cu,.2,step=.1,padding=15,max_nodes=250000)
assert pts,'DIRECT_ACTUAL_F_INPUT_B'
for a,z in zip(pts,pts[1:]):assert g.clear([a,z],n,pcbnew.F_Cu,.2),('NATIVE_CLEAR',a,z)
new=[]
for a,z in zip(pts,pts[1:]):
 tr=pcbnew.PCB_TRACK(b);tr.SetNet(b.FindNet(n));tr.SetStart(xy(a));tr.SetEnd(xy(z));tr.SetWidth(pcbnew.FromMM(.2));tr.SetLayer(pcbnew.F_Cu);b.Add(tr);g.add(tr);new.append(dict(uuid=tr.m_Uuid.AsString(),identity=identity(tr),role='U11020_input_3_actual_source_B'))
old_ids={q['uuid']for q in r['exact_retired_copper']};added_ids={q['uuid']for q in r['exact_added_copper']};original=pcbnew.LoadBoard(str(r['before_board']));old_cu={t.m_Uuid.AsString():identity(t)for t in original.GetTracks()};r['exact_retired_copper']+=[dict(uuid=u,identity=old_cu[u])for u in sorted(ret-added_ids-old_ids)];r['exact_added_copper']=[q for q in r['exact_added_copper']if q['uuid']not in ret]+new;r['routes']=[q for q in r['routes']if q['role']not in['U11020_input_3_actual_source_B','U11020_input_3_actual_receiving_F']];r['routes'].append(dict(role='U11020_input_3_actual_source_B',net=n,layer='F.Cu',width_mm=.2,points_mm=pts,uuids=[q['uuid']for q in new],length_mm=sum(math.dist(a,z)for a,z in zip(pts,pts[1:]))))
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();D=O/'motor-health-U20-cell-candidate.kicad_pcb';pcbnew.SaveBoard(str(D),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(D)],check=True,capture_output=True,text=True);d=json.loads((O/'drc.json').read_text());err=[v for v in d['violations']if v['severity']=='error'];assert not err,err
r.update(candidate_sha256=sha(D),native_errors=err,native_types=dict(collections.Counter(v['type']for v in d['violations'])),actual_input_B_repair=dict(own_endpoint_first_escapes_mm=1.1,avoids_actual_input_A_antipad=True,strict_reference_qualification_pending=True))
(O/'receipt.json').write_text(json.dumps(r,indent=2));(O/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_scope_reason='Necessary actual health receiving circuit, off-land Ground barrel and literal input-B route avoiding input-A antipad; strict reference proof remains required.',reviewed_footprint_references=list(r['old_poses']),reviewed_copper_delta_UUIDs=sorted(q['uuid']for q in r['exact_retired_copper'])+sorted(q['uuid']for q in r['exact_added_copper']),reviewed_added_zone_UUIDs=[]),indent=2));print('DONE',sha(D),len(r['exact_added_copper']),len(r['exact_retired_copper']),flush=True)

