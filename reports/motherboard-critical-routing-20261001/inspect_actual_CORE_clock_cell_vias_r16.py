from pathlib import Path
import sys,json
sys.path[:0]=[str(Path.cwd()/'tools')]
import pcbnew
from hardware_route_logic_return import mm,identity
b=pcbnew.LoadBoard('reports/motherboard-critical-routing-20261001/CORE-literal-antipad-join-baseline-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb')
print(json.dumps([dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),identity=identity(t),In3_flash=t.FlashLayer(pcbnew.In3_Cu))for t in b.GetTracks()if t.Type()==pcbnew.PCB_VIA_T and mm(t.GetPosition())in((93.6,44.),(95.2,44.))],indent=2))
