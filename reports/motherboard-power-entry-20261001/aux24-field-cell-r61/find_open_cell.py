import sys,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_fix_aux24_field_cell_native import REFS,POSES
from hardware_route_current_delivery_native import Geometry
from hardware_route_power_groups_native import hits
from hardware_route_logic_return import mm,xy
from hardware_place_owned_capacitors_native import side_box
from hardware_populate_motherboard_pcb import intersects
b=pcbnew.LoadBoard(str(Path(__file__).with_name('rejected-field-debug.kicad_pcb')))
fs={f.GetReference():f for f in b.GetFootprints()}; ext=[(o.GetReference(),o.GetLayer(),side_box(o))for o in b.GetFootprints()if o.GetReference()not in REFS]
retain=[fs[r]for r in REFS]
for f in retain:b.Remove(f)
g=Geometry(b)
for f in retain:b.Add(f)
goods=[]
centres=sorted([(x,y)for x in range(280,451,5)for y in range(170,311,5)],key=lambda v:math.dist(v,(345,185)))
for cx,cy in centres:
 dx,dy=cx-375,cy-208
 for r in REFS:
  pt,a=POSES[r];fs[r].SetPosition(xy((pt[0]+dx,pt[1]+dy)))
 if any(intersects(side_box(fs[r]),box,0)for r in REFS for _,l,box in ext if l==fs[r].GetLayer()):continue
 p={(r,p.GetNumber()):p for r in REFS for p in fs[r].Pads()};a8=mm(p['U11015','8'].GetPosition());v=[(mm(p['U11015','7'].GetPosition()),p['U11015','7'].GetNetname(),.4),((a8[0]+.3,a8[1]),p['U11015','8'].GetNetname(),.4)]
 for r,pin in [('U11015','11'),('R11056','1'),('R11056','2'),('C11068','1'),('C11068','2')]:v.append((mm(p[r,pin].GetPosition()),p[r,pin].GetNetname(),.5))
 if not all(g.clear([pt,pt],n,l,size)for pt,n,size in v for l in [pcbnew.F_Cu,pcbnew.B_Cu]):continue
 bad=False
 for pad in p.values():
  l=pad.GetLayer();poly=pad.GetEffectivePolygon(l);poly=[mm(poly.Outline(0).CPoint(i))for i in range(poly.Outline(0).PointCount())];box=pad.GetBoundingBox();lo=mm(box.GetPosition());hi=(lo[0]+pcbnew.ToMM(box.GetWidth()),lo[1]+pcbnew.ToMM(box.GetHeight()))
  for n,s,e,w in g.tracks[l].candidates(lo,hi,.16):
   if n!=pad.GetNetname()and hits(s,e,poly,.16+w/2):bad=True;break
  if bad:break
 if bad:continue
 goods.append((cx,cy));print('FIT',cx,cy,flush=True)
 if len(goods)>=12:break
print('FINAL',goods)
