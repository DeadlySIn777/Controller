import sys,json,math,shutil
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import mm,xy
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
B=Path('reports/motherboard-power-entry-20261001/ROOT101-health-U19-facing-cell-r306/motherboard-health-U19-facing-cell-candidate.kicad_pcb');b=pcbnew.LoadBoard(str(B));fs={f.GetReference():f for f in b.GetFootprints()};refs=['U11011','C11059','C11060','R11045','R11046','R11047','U11034','U11033','C11085','C11086','R11078','R11079'];old={r:[mm(fs[r].GetPosition()),fs[r].GetOrientationDegrees(),fs[r].GetLayer()]for r in refs}
base={'U11011':((276,167),0),'C11059':((274.2,165),90),'C11060':((279.25,166.5),0),'R11047':((279,163.5),0),'R11046':((277,170),0),'R11045':((273,154),0),'U11034':((267.5,154),0),'C11086':((268.125,153.25),180),'C11085':((270,155.775),-90),'U11033':((262,148),0),'R11078':((267.5,150),0),'R11079':((273,156),0)}
for r,(pt,ang)in base.items():
 f=fs[r]
 if r.startswith('C')or r in ['R11047','R11046']:
  if f.GetLayer()!=pcbnew.B_Cu:f.Flip(f.GetPosition(),False)
 f.SetPosition(xy(pt));f.SetOrientationDegrees(ang)
print('CURRENT_SCREEN')
for r in refs:print(r,side_box(fs[r]),[(z.GetReference(),side_box(z))for z in fs.values()if z.GetReference()!=r and z.GetLayer()==fs[r].GetLayer()and intersects(side_box(fs[r]),side_box(z),0)])


