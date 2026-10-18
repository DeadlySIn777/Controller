import sys,json,hashlib,importlib.util,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_route_logic_return import identity,mm
H=Path('reports/motherboard-ordinary-routing-20261001/check_io3_backbone_preservation_r07.py');spec=importlib.util.spec_from_file_location('r07',H);m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m)
B=Path('reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb');A=Path('reports/motherboard-power-entry-20261001/Source27-closer-bypass-native-proof-r596/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb');S=Path('reports/motherboard-power-entry-20261001/ROOT103-BankB-physical-stage-r532/motherboard-bounded-merged-candidate.kicad_pcb');O=Path('reports/motherboard-power-entry-20261001/Source27-power-context-r612');assert not O.exists();O.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
inputs={str(p):sha(p)for p in[B,A,S,H,Path(__file__)]};b=pcbnew.LoadBoard(str(B));a=pcbnew.LoadBoard(str(A));s=pcbnew.LoadBoard(str(S));old={t.m_Uuid.AsString():t for t in b.GetTracks()};new={t.m_Uuid.AsString():t for t in a.GetTracks()}
bf=collect_native_reference_fills(b,{'/IO_3V3'},[pcbnew.In2_Cu])['/IO_3V3',pcbnew.In2_Cu];sf=collect_native_reference_fills(s,{'/IO_3V3'},[pcbnew.In2_Cu])['/IO_3V3',pcbnew.In2_Cu]
contexts=[]
for label,pt in [('new_A_lowcurrent_feeds',(261.7,199.1)),('former_B_cell_contour',(354.25,189.43)),('new_B_Ground_barrel',(279.4,168.6))]:
 pads=[];near=[]
 for p in a.GetPads():
  if math.dist(pt,mm(p.GetPosition()))<=4:pads.append(dict(ref=p.GetParentFootprint().GetReference(),pin=p.GetNumber(),net=p.GetNetname(),position_mm=mm(p.GetPosition()),distance_mm=math.dist(pt,mm(p.GetPosition()))))
 for t in a.GetTracks():
  if isinstance(t,pcbnew.PCB_VIA)and math.dist(pt,mm(t.GetPosition()))<=4:near.append(dict(uuid=t.m_Uuid.AsString(),actual=identity(t),new=t.m_Uuid.AsString()not in old,distance_mm=math.dist(pt,mm(t.GetPosition()))))
 region=m.box(pt[0]-.6,pt[1]-.6,pt[0]+.6,pt[1]+.6)
 contexts.append(dict(label=label,point_mm=pt,actual_pads=sorted(pads,key=lambda x:x['distance_mm']),actual_barrels=sorted(near,key=lambda x:x['distance_mm']),BankB_stage_already_changed_old_power=m.subtract(m.intersection(bf,region),m.intersection(sf,region)).Format(False)))
target=new['be91e795-0007-4adb-9c00-e7085583a5a5'];p=target.GetPosition();attached=[dict(uuid=t.m_Uuid.AsString(),actual=identity(t))for t in a.GetTracks()if not isinstance(t,pcbnew.PCB_VIA)and(p==t.GetStart()or p==t.GetEnd())]
assert all(sha(Path(p))==h for p,h in inputs.items());result=dict(input_hashes=inputs,contexts=contexts,be91_attached_leaves=attached,no_source_or_board_mutation=True);(O/'review.json').write_text(json.dumps(result,indent=2));print(json.dumps(result,indent=2),flush=True)
