import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_logic_return import mm,xy
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/io3-positive-delivery-r08/io3-positive-delivery-candidate.kicad_pcb');cf=next(f for f in b.GetFootprints()if f.GetReference()=='C11069');cf.SetPosition(xy((347.575,180.85)));cf.SetOrientationDegrees(0);g=Geometry(b);ps={(f.GetReference(),p.GetNumber()):p for f in b.GetFootprints()for p in f.Pads()if p.GetNumber()};out=[]
for cp,owner in [('1','1'),('2','6')]:
 p=ps['C11069',cp];s=mm(p.GetPosition());e=mm(ps['U11015',owner].GetPosition());n=p.GetNetname();opts=[]
 for ix in range(26):
  for iy in range(26):
   v=(s[0]-2.5+ix*.2,s[1]-2.5+iy*.2)
   if all(g.clear([v,v],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu])and g.clear([s,v],n,pcbnew.B_Cu,.4)and g.clear([e,v],n,pcbnew.F_Cu,.4):opts.append(dict(point=v,combined_length=math.dist(s,v)+math.dist(e,v)))
 print(json.dumps(dict(pin=cp,options=sorted(opts,key=lambda r:r['combined_length'])[:10])))
