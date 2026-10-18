import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_route_current_delivery_native import sha
P=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U20-cell-r202/motor-health-U20-cell-candidate.kicad_pcb');b=pcbnew.LoadBoard(str(P));b.BuildConnectivity();r=json.loads((P.parent/'receipt.json').read_text());ts={t.m_Uuid.AsString():t for t in b.GetTracks()};checker=NativeCollectedAnnulusCheck(b,{});reviews=[]
for row in r['exact_added_copper']:
 role=row['role'];qual=role.startswith(('U11020_local_positive','U11020_own_positive','U11020_input_1_actual','U11020_input_3_actual'))
 if not qual:continue
 t=ts[row['uuid']];margin=.10 if role.startswith(('U11020_local_positive','U11020_own_positive'))else.40
 d=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=margin);checker.rows={t.GetNetname():d}
 try:v=checker.via(t,d)if isinstance(t,pcbnew.PCB_VIA)else checker.segment(t,d);reviews.append(dict(uuid=row['uuid'],role=role,passed=True,review=v))
 except Exception as e:reviews.append(dict(uuid=row['uuid'],role=role,passed=False,error=str(e)))
(P.parent/'strict-local-bypass-and-controls.json').write_text(json.dumps(dict(board_sha256=sha(P),reviews=reviews),indent=2));print('REVIEWS',len(reviews),'FAIL',sum(not q['passed']for q in reviews),flush=True)
for q in reviews:
 if not q['passed']:print(q['role'],q['uuid'],q['error'],flush=True)
