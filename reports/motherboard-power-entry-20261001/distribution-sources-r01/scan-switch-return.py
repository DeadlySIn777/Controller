import sys
sys.path.insert(0,'tools')
import pcbnew, math
from hardware_route_current_delivery_native import Geometry
from hardware_route_logic_return import mm
from hardware_route_local_signals import paths
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-supply-cells-r16/C11058-return-debug.kicad_pcb');g=Geometry(b); fs={f.GetReference():f for f in b.GetFootprints()}; p=next(p for p in fs['U11010'].Pads()if p.GetNumber()=='6');cp=next(p for p in fs['C11058'].Pads()if p.GetNumber()=='2');n=p.GetNetname();s=mm(p.GetPosition());c=mm(cp.GetPosition());found=[]
for dx in range(-15,16):
 for dy in range(-15,16):
  q=(c[0]+dx*.2,c[1]+dy*.2)
  if not all(g.clear([q,q],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]):continue
  a=[s,q];z=next((pp for pp in paths(c,q)if g.clear(pp,n,pcbnew.B_Cu,.4)),None)
  if a and z:found.append((math.dist(s,q),q,a,z))
print(sorted(found)[:10]); print('count',len(found))


