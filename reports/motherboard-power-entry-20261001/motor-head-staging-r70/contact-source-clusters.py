import sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-digital-bias-returns-adopted-r73/motherboard-source26-WIP.kicad_pcb');b.BuildConnectivity();co=b.GetConnectivity()
for f in b.GetFootprints():
 if f.GetReference()in['U11021','U11023','U11027','U11029']:
  print('CONTACT',f.GetReference())
  for p in f.Pads():print(p.GetNumber(),p.GetNetname(),[(v.GetParentFootprint().GetReference(),v.GetNumber())for v in co.GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T])
