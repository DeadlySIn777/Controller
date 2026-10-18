import sys
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_fix_aux24_field_cell_native import REFS,POSES
from hardware_route_current_delivery_native import Geometry
from hardware_route_logic_return import mm,xy
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
b=pcbnew.LoadBoard(str(Path(__file__).with_name('rejected-field-debug.kicad_pcb')))
fs={f.GetReference():f for f in b.GetFootprints()}; good=[]
for dx,dy in [(dx,dy)for dy in [-10,-12,-14,-16,-18,-20,-22,-24]for dx in [-10,-8,-6,-4,-2,0,2,4]]:
 for r in REFS:
  pt,a=POSES[r];fs[r].SetPosition(xy((pt[0]+dx,pt[1]+dy)))
 collisions=[(r,o.GetReference())for r in REFS for o in b.GetFootprints()if o.GetReference()!=r and o.GetLayer()==fs[r].GetLayer()and intersects(side_box(fs[r]),side_box(o),0)]
 if collisions:
  print((dx,dy),'COURT',collisions[:2],flush=True);continue
 g=Geometry(b);p={(r,p.GetNumber()):p for r in REFS for p in fs[r].Pads()};a8=mm(p['U11015','8'].GetPosition());v=[(mm(p['U11015','7'].GetPosition()),p['U11015','7'].GetNetname(),.4),((a8[0]+.3,a8[1]),p['U11015','8'].GetNetname(),.4)]
 for r,pin in [('U11015','11'),('R11056','1'),('R11056','2'),('C11068','1'),('C11068','2')]:v.append((mm(p[r,pin].GetPosition()),p[r,pin].GetNetname(),.5))
 bad=[(pt,n,b.GetLayerName(l))for pt,n,size in v for l in [pcbnew.F_Cu,pcbnew.B_Cu]if not g.clear([pt,pt],n,l,size)]
 if not bad:good.append((dx,dy))
 else:print((dx,dy),'VIA',bad[:2],flush=True)
print(good)
