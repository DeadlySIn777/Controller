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
B=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-control-B-F-r234/motor-health-U20-cell-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-control-A-r236');O.mkdir(exist_ok=False)
r=json.loads((B.parent/'receipt.json').read_text());ret={q['uuid']for q in r['exact_added_copper']if q['role']in['U11020_input_1_actual_source_B','U11020_input_3_actual_SOURCE_Ground_stitch','U11020_input_3_SOURCE_Ground_to_actual_C11078']};t=parse(without_generated_fills(B.read_text()));t=[v for v in t if not(isinstance(v,list)and v and v[0]in['segment','via']and value(child(v,'uuid')[1])in ret)];D=O/'literal-B-path-retired.kicad_pcb';D.write_text(dump_board(t))
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
b=pcbnew.LoadBoard(str(D));g=FastGeometry(b);p=next(p for p in b.GetPads()if p.GetParentFootprint().GetReference()=='U11020'and p.GetNumber()=='1');n=p.GetNetname()
s=(343.847560,176.360060);e=(340.6875,175.85);a=(s[0],s[1]+1.1);z=(e[0],e[1]+1.1);middle=next((p for p in paths(a,z)if g.clear(p,n,pcbnew.B_Cu,.2)),None)
if middle is None:middle=g.grid(a,z,n,pcbnew.B_Cu,.2,step=.1,padding=10,max_nodes=100000)
assert middle,'ACTUAL_A_MIDDLE';pts=[s]+middle+[e]
for a,z in zip(pts,pts[1:]):assert g.clear([a,z],n,pcbnew.B_Cu,.2),('NATIVE_CLEAR',a,z)
new=[]
for a,z in zip(pts,pts[1:]):
 tr=pcbnew.PCB_TRACK(b);tr.SetNet(b.FindNet(n));tr.SetStart(xy(a));tr.SetEnd(xy(z));tr.SetWidth(pcbnew.FromMM(.2));tr.SetLayer(pcbnew.B_Cu);b.Add(tr);g.add(tr);new.append(dict(uuid=tr.m_Uuid.AsString(),identity=identity(tr),role='U11020_input_1_actual_source_B'))
r['exact_added_copper']=[q for q in r['exact_added_copper']if q['uuid']not in ret]+new;r['routes']=[q for q in r['routes']if q['role']not in['U11020_input_1_actual_source_B','U11020_input_3_SOURCE_Ground_to_actual_C11078']];r['routes'].append(dict(role='U11020_input_1_actual_source_B',net=n,layer='B.Cu',width_mm=.2,points_mm=pts,uuids=[q['uuid']for q in new],length_mm=sum(math.dist(a,z)for a,z in zip(pts,pts[1:]))))
pcbnew.ZONE_FILLER(b).Fill(b.Zones());b.BuildConnectivity();D=O/'motor-health-U20-cell-candidate.kicad_pcb';pcbnew.SaveBoard(str(D),b)
for e in['.kicad_pro','.kicad_dru']:shutil.copyfile(B.with_suffix(e),D.with_suffix(e))
subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--format','json','--all-track-errors','--severity-all','-o',str(O/'drc.json'),str(D)],check=True,capture_output=True,text=True);d=json.loads((O/'drc.json').read_text());err=[v for v in d['violations']if v['severity']=='error'];assert not err,err
r.update(candidate_sha256=sha(D),native_errors=err,native_types=dict(collections.Counter(v['type']for v in d['violations'])),actual_input_A_repair=dict(exact_source_and_receiving_first_escape_mm=1.1,strict_reference_qualification_pending=True),actual_input_B_repair=dict(continuous_F_source_pad_to_input_pad_path=True,signal_transfer_vias=0,obsolete_added_Source_stitch_retired=True,strict_reference_qualification_pending=True))
(O/'receipt.json').write_text(json.dumps(r,indent=2));(O/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_scope_reason='Necessary actual health receiving circuit, off-land Ground barrel and literal input-B route avoiding input-A antipad; strict reference proof remains required.',reviewed_footprint_references=list(r['old_poses']),reviewed_copper_delta_UUIDs=sorted(q['uuid']for q in r['exact_retired_copper'])+sorted(q['uuid']for q in r['exact_added_copper']),reviewed_added_zone_UUIDs=[]),indent=2));print('DONE',sha(D),len(r['exact_added_copper']),len(r['exact_retired_copper']),flush=True)

