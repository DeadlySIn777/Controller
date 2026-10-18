import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_route_current_delivery_native import sha
P=Path('reports/motherboard-power-entry-20261001/ROOT94-health-U19-transfer-r167/motor-health-U19-transfer-candidate.kicad_pcb');b=pcbnew.LoadBoard(str(P));b.BuildConnectivity();ids=json.loads((P.parent/'receipt.json').read_text())['exact_changed_copper'];ts={t.m_Uuid.AsString():t for t in b.GetTracks()};n=ts[ids[0]['uuid']].GetNetname();d=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.10);c=NativeCollectedAnnulusCheck(b,{n:d});rows=[]
for r in ids:
 t=ts[r['uuid']]
 try:rows.append(dict(uuid=r['uuid'],passed=True,review=c.via(t,d)if isinstance(t,pcbnew.PCB_VIA)else c.segment(t,d)))
 except Exception as e:rows.append(dict(uuid=r['uuid'],passed=False,error=str(e)))
(P.parent/'strict-receiving-loop-review.json').write_text(json.dumps(dict(board_sha256=sha(P),rows=rows),indent=2));print(json.dumps(rows,indent=2))
