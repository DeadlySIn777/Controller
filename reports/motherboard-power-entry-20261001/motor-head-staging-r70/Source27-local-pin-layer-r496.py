import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/Source27-reset-native-proof-r490/motherboard-staged-Source27-reset-routed-candidate.kicad_pcb')
for f in b.GetFootprints():
 if f.GetReference()in ['U11034','U11037','U11038','C11085','C11086','C11091','C11092','R11083']:
  print(f.GetReference(),b.GetLayerName(f.GetLayer()),[[p.GetNumber(),mm(p.GetPosition()),p.GetNetname()]for p in f.Pads()],flush=True)
