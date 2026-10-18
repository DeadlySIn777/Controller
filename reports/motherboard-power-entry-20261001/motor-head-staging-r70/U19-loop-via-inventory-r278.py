import sys,json,shutil,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,identity
b=pcbnew.LoadBoard('reports/motherboard-return-zoning-20261001/ROOT101-two-health-real-Source-collars-r01/motherboard-two-health-Source-reference-candidate.kicad_pcb')
for t in b.GetTracks():
 if isinstance(t,pcbnew.PCB_VIA)and 337<=mm(t.GetPosition())[0]<=347 and 172<=mm(t.GetPosition())[1]<=180:print(t.m_Uuid.AsString(),mm(t.GetPosition()),t.GetNetname())
