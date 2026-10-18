import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,identity
from hardware_place_owned_capacitors_native import side_box
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb');b.BuildConnectivity();fs={f.GetReference():f for f in b.GetFootprints()};c=b.GetConnectivity()
for f in b.GetFootprints():
 x,y=mm(f.GetPosition())
 if 331<x<347 and 166<y<179:print(f.GetReference(),mm(f.GetPosition()),b.GetLayerName(f.GetLayer()),side_box(f))
for p in fs['U11020'].Pads():
 print('PAD',p.GetNumber(),mm(p.GetPosition()),p.GetNetname())
 for t in c.GetConnectedItems(p):
  if isinstance(t,(pcbnew.PCB_TRACK,pcbnew.PCB_VIA))and (mm(t.GetStart())==mm(p.GetPosition())or mm(t.GetEnd())==mm(p.GetPosition())):print(identity(t))
