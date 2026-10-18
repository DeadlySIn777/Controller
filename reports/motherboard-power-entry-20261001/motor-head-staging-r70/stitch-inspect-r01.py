import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,identity
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-bank-A-r83/motor-bank-A-receiving-candidate.kicad_pcb')
p=[(270.85,180.8),(266.925,181.5),(265.975,199.5),(273.725,179.5),(267.075,193)]
for i,x in enumerate(p):
 print('TRANSFER',i,x)
 for t in b.GetTracks():
  if t.GetNetname()!='/LOGIC_GND':continue
  a=mm(t.GetPosition()) if isinstance(t,pcbnew.PCB_VIA) else mm(t.GetStart());c=a if isinstance(t,pcbnew.PCB_VIA) else mm(t.GetEnd())
  if min(math.dist(a,x),math.dist(c,x))<6:print(identity(t))
