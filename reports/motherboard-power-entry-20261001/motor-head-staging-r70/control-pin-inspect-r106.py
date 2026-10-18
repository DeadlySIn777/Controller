import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,identity
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-bank-A-r83/motor-bank-A-receiving-candidate.kicad_pcb')
for f in b.GetFootprints():
 if f.GetReference() in ['U11010','U11032','U11031','U11033']:print(f.GetReference(),[(p.GetNumber(),mm(p.GetPosition()),p.GetNetname())for p in f.Pads()])
for t in b.GetTracks():
 if isinstance(t,pcbnew.PCB_VIA)and 270<mm(t.GetPosition())[0]<276 and 177<mm(t.GetPosition())[1]<182:print(identity(t))
