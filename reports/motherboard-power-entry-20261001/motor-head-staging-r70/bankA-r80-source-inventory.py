import sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-bank-A-r80/motor-bank-A-receiving-candidate.kicad_pcb');b.BuildConnectivity();co=b.GetConnectivity();fs={f.GetReference():f for f in b.GetFootprints()}
for ref in ['U11019','U11020','U11025','U11026','R11048','R11043','R11071','U11010','U11031','U11032','U11021','U11022','U11027','U11028']:
 print(ref,flush=True)
 for p in fs[ref].Pads():
  cc=[t for t in co.GetConnectedItems(p)if t.Type()==pcbnew.PCB_PAD_T];print(p.GetNumber(),p.GetNetname(),len(cc),[(t.GetParentFootprint().GetReference(),t.GetNumber())for t in cc][:10],flush=True)
