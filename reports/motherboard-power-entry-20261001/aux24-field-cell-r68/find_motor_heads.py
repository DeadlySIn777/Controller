import sys,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import xy,mm
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-field-status-ground-r67/motherboard-bounded-merged-candidate.kicad_pcb');fs={f.GetReference():f for f in b.GetFootprints()};refs=['U11010','U11011','C11057','C11058','C11059','C11060'];ext=[(f.GetReference(),f.GetLayer(),side_box(f))for f in b.GetFootprints()if f.GetReference()not in refs]
template={'U11010':((0,0),0),'U11011':((0,7),0),'C11057':((-2.5,0),180),'C11058':((3.25,-.5),0),'C11059':((-2.5,7),180),'C11060':((3.25,6.5),0)}
good=[]
for cx,cy in sorted([(x,y)for x in range(272,305,2)for y in range(171,211,2)],key=lambda v:math.dist(v,(270,171))):
 for r,(off,ang)in template.items():fs[r].SetPosition(xy((cx+off[0],cy+off[1])));fs[r].SetOrientationDegrees(ang)
 if any(intersects(side_box(fs[r]),box,0)for r in refs for _,l,box in ext if fs[r].GetLayer()==l):continue
 good.append((cx,cy));print('FIT',cx,cy,flush=True)
 if len(good)>12:break
print('FINAL',good)
