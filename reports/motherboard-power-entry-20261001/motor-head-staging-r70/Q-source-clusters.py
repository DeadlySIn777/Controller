import sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-C17014-bypass-r69/motherboard-bounded-merged-candidate.kicad_pcb');b.BuildConnectivity();co=b.GetConnectivity()
for f in b.GetFootprints():
 if f.GetReference()in['U11032','U11034']:
  print('LATCH',f.GetReference(),mm(f.GetPosition()))
  for p in f.Pads():
   pp=[(v.GetParentFootprint().GetReference(),v.GetNumber())for v in co.GetConnectedItems(p)if v.Type()==pcbnew.PCB_PAD_T];print(p.GetNumber(),p.GetNetname(),len(pp),pp[:15])
