from pathlib import Path
import sys,json
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import write,sha
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
B=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-orthogonal-Source-feed-r06/motherboard-U25-orthogonal-Source-feed-candidate.kicad_pcb')
M=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-r06-native-focused-proof-r01/focused-C80-manifest.json')
O=Path('reports/motherboard-return-zoning-20261001/ROOT101-U25-r06-literal-cap-branch-failure-r01');assert not O.exists();O.mkdir();b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};ret='/motherboard_motors/FIELD_GND';d=dict(return_net=ret,reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.10);checker=NativeCollectedAnnulusCheck(b,{});checker.rows={'/motherboard_power_entry/FIELD_5V':d};rows=[]
for u in json.loads(M.read_text())['owned_loops'][0]['new_UUIDs']:
 t=cu[u]
 if t.GetNetname()!='/motherboard_power_entry/FIELD_5V':continue
 try:v=checker.via(t,d)if t.Type()==pcbnew.PCB_VIA_T else checker.segment(t,d);rows.append(dict(uuid=u,passed=True,review=v))
 except ValueError as e:rows.append(dict(uuid=u,passed=False,error=str(e)))
write(O/'diagnostic.json',dict(board_sha256=sha(B),rows=rows));print(json.dumps([r for r in rows if not r['passed']]),flush=True)
