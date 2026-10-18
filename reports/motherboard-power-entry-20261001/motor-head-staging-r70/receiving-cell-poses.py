import sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-C17014-bypass-r69/motherboard-bounded-merged-candidate.kicad_pcb')
for f in b.GetFootprints():
 if f.GetReference()in['U11017','U11018','U11019','U11020','U11021','U11022','U11023','U11024','U11027','U11029','U11031','U11032','U11033','U11034','R11074','R11075','R11078','R11079','C11081','C11082','C11084','C11085']:
  print(f.GetReference(),mm(f.GetPosition()),f.GetOrientationDegrees(),b.GetLayerName(f.GetLayer()))
