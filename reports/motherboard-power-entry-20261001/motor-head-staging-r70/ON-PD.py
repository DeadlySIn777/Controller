import sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-C17014-bypass-r69/motherboard-bounded-merged-candidate.kicad_pcb')
for f in b.GetFootprints():
 if f.GetReference()in['R11042','R11045']:
  print(f.GetReference(),mm(f.GetPosition()),f.GetOrientationDegrees(),b.GetLayerName(f.GetLayer()))
  for p in f.Pads():print(p.GetNumber(),mm(p.GetPosition()),p.GetNetname())
