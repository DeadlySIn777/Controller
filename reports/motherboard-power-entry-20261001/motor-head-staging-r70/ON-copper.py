import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-C17014-bypass-r69/motherboard-bounded-merged-candidate.kicad_pcb')
for t in b.GetTracks():
 if t.GetNetname() in ['/motherboard_power_entry/MOTOR_FEED_ON_A','/motherboard_power_entry/MOTOR_FEED_ON_B']:print(t.m_Uuid.AsString(),t.GetNetname(),b.GetLayerName(t.GetLayer()),mm(t.GetStart()),mm(t.GetEnd()),pcbnew.ToMM(t.GetWidth(pcbnew.F_Cu)if isinstance(t,pcbnew.PCB_VIA)else t.GetWidth()))

