import sys
sys.path.insert(0,'tools')
import pcbnew, math
from hardware_route_current_delivery_native import Geometry
from hardware_route_logic_return import mm
from hardware_route_local_signals import paths
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-supply-cells-r13/C11058-supply-debug.kicad_pcb');g=Geometry(b); fs={f.GetReference():f for f in b.GetFootprints()}; p=next(p for p in fs['U11010'].Pads()if p.GetNumber()=='9');cp=next(p for p in fs['C11058'].Pads()if p.GetNumber()=='1');n=p.GetNetname();s=mm(p.GetPosition());c=mm(cp.GetPosition());found=[]
for dx in range(-25,26):
 for dy in range(-25,26):
  q=(c[0]+dx*.1,c[1]+dy*.1)
  if not all(g.clear([q,q],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]):continue
  a=next((pp for pp in paths(s,q)if g.clear(pp,n,pcbnew.F_Cu,.3)),None);z=next((pp for pp in paths(c,q)if g.clear(pp,n,pcbnew.B_Cu,.4)),None)
  if a and z:found.append((math.dist(s,q),q,a,z))
print(sorted(found)[-30:]); print('count',len(found))

