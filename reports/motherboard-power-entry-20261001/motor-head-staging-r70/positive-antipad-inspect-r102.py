from pathlib import Path
import pcbnew,json,sys,math
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_route_logic_return import mm,identity
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-bank-A-r83/motor-bank-A-receiving-candidate.kicad_pcb')
for t in b.GetTracks():
 if isinstance(t,pcbnew.PCB_VIA)and 250<mm(t.GetPosition())[0]<272 and 191<mm(t.GetPosition())[1]<202 and t.GetNetname()=='/motherboard_power_entry/MOTION_5V_RAW':
  pos=mm(t.GetPosition());print('VIA',identity(t))
  for s in b.GetTracks():
   if not isinstance(s,pcbnew.PCB_VIA)and s.GetNetname()==t.GetNetname()and (mm(s.GetStart())==pos or mm(s.GetEnd())==pos):print('  LEG',identity(s))
