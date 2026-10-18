import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/Source27-four-bypass-correct-orientation-r564/debug.kicad_pcb');b.BuildConnectivity();ps={(p.GetParentFootprint().GetReference(),p.GetNumber()):p for p in b.GetPads()if p.GetNumber()}
for cap in ['C11083','C11086']:
 p=ps[cap,'1'];ids={t.m_Uuid.AsString()for t in b.GetConnectivity().GetConnectedItems(p)}
 print(cap,mm(p.GetPosition()))
 print(json.dumps([dict(uuid=t.m_Uuid.AsString(),point=mm(t.GetPosition()))for t in b.GetTracks()if isinstance(t,pcbnew.PCB_VIA)and t.m_Uuid.AsString()in ids],indent=2))
