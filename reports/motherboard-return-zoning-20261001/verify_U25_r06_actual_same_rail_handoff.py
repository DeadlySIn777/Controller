from pathlib import Path
import sys,json,subprocess
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path.cwd()/'reports/motherboard-return-zoning-20261001')]
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_correct_motherboard_isolation_crossings import native_pad_clusters
from hardware_trim_empty_return_pockets import clusters_survive
from hardware_route_logic_return import mm
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-orthogonal-Source-feed-r06/motherboard-U25-orthogonal-Source-feed-candidate.kicad_pcb')
G=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-two-local-barrel-correction-r04/generation.json')
M=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101/current106-bypass-manifest.json')
OWN=Path('reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json')
BASE=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb')
O=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-r06-native-focused-proof-r01');assert not O.exists();O.mkdir()
inputs={str(q):sha(q)for q in[B,G,M,OWN,BASE,Path(__file__)]}
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();co=b.GetConnectivity();pads={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()};cu={t.m_Uuid.AsString():t for t in b.GetTracks()}
for start,end in[(('U11013','2'),('U11025','2')),(('U11025','5'),('C11080','1')),(('U11025','2'),('C11080','2')),(('U11025','2'),('U11026','2'))]:
 p,q=pads[start],pads[end];assert p.GetNetname()==q.GetNetname()and q.m_Uuid.AsString()in{x.m_Uuid.AsString()for x in co.GetConnectedItems(p)}
before=pcbnew.LoadBoard(str(BASE));before.BuildConnectivity();nets={p.GetNetname()for p in before.GetPads()if p.GetNumber()};old=native_pad_clusters(before,nets);new=native_pad_clusters(b,nets);assert clusters_survive(old,new);write(O/'all-actual-Source-clusters.json',dict(passed=True,before=old,after=new))
manifest=json.loads(M.read_text());group=next(g for g in manifest['owned_loops']if g['ref']=='C11080');generation=json.loads(G.read_text());group['new_UUIDs']=list(dict.fromkeys(group['new_UUIDs']+generation['exact_added_Cu_UUIDs']+['e7815e4d-590b-44a0-90fa-1224ae819e3f']));group['exact_modified_Cu_UUIDs']=generation['exact_modified_Cu_UUIDs'];group['explicit_rebind_reason']='Off-land pair correction; two actual F VCC escapes; exact same-rail B orthogonal join to retained vertical cap branch, checked in full. Actual shared U13.2 ground continuity independently restored.';manifest.update(board_sha256=sha(B),bounded_current106_C80_rebind=True);write(O/'current106-C80-rebound-manifest.json',manifest);focused=dict(manifest,owned_loops=[group]);write(O/'focused-C80-manifest.json',focused)
r=subprocess.run([sys.executable,'tools/hardware_verify_owned_bypass_batch.py','--board',str(B),'--owners',str(OWN),'--receipt',str(O/'focused-C80-manifest.json'),'--out',str(O/'C80-strict-loop-proof.json')],capture_output=True,text=True);(O/'C80-command.txt').write_text(r.stdout+r.stderr);assert r.returncode==0,'Full actual same-rail cap branch failed frozen reference proof'
ret=pads['U11026','2'].GetNetname();private={pads['U11026',n].GetNetname()for n in('1','3')};decl=dict(return_net=ret,reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.4);checker=ExactEndpointUnionCheck(b,{n:decl for n in private});controls=[]
for t in cu.values():
 if t.GetNetname()not in private:continue
 try:result=checker.via(t,decl)if t.Type()==pcbnew.PCB_VIA_T else checker.segment(t,decl);controls.append(dict(uuid=t.m_Uuid.AsString(),passed=True,review=result))
 except ValueError as e:controls.append(dict(uuid=t.m_Uuid.AsString(),passed=False,error=str(e)))
write(O/'actual-U26-controls.json',dict(board_sha256=sha(B),passed=all(r['passed']for r in controls),rows=controls));assert all(r['passed']for r in controls)
assert all(sha(Path(q))==h for q,h in inputs.items());write(O/'receipt.json',dict(passed=True,board_sha256=sha(B),input_sha256=inputs,actual_Source_cluster_preservation=True,actual_U13_Source_return_restored=True,C80_frozen_strict_loop_passed=True,U26_control_rows=len(controls),full_health_or_manufacturing_qualification=False));print(json.dumps(dict(passed=True,board_sha256=sha(B),U26_controls=len(controls))),flush=True)
