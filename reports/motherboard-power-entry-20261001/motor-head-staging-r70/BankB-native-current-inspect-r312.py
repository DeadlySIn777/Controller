import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm
from hardware_place_owned_capacitors_native import side_box
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/ROOT101-health-U19-facing-cell-r306/motherboard-health-U19-facing-cell-candidate.kicad_pcb');fs={f.GetReference():f for f in b.GetFootprints()}
for r in ['U11011','C11059','C11060','R11045','R11046','R11047','U11034','U11033','C11085','C11086','R11078','R11079','U11023','U11024','U11029','U11030','R11069','R11073']:
 f=fs[r];print('PART',r,mm(f.GetPosition()),f.GetOrientationDegrees(),b.GetLayerName(f.GetLayer()),side_box(f))
 for p in f.Pads():print('PAD',p.GetNumber(),mm(p.GetPosition()),p.GetNetname())
