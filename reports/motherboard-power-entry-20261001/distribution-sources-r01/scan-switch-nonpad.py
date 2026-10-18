import sys
sys.path.insert(0,'tools')
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_logic_return import mm
from hardware_route_power_groups_native import hits
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motor-supply-cells-r13/C11058-supply-debug.kicad_pcb');g=Geometry(b);cp=next(p for f in b.GetFootprints()if f.GetReference()=='C11058'for p in f.Pads()if p.GetNumber()=='1');n=cp.GetNetname();out=[]
for dx in range(-25,26):
 for dy in range(-25,26):
  q=(344.4+dx*.1,185.525+dy*.1)
  if not all(g.clear([q,q],n,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]):continue
  if any(any(hits(q,q,p,.3)for p in polys)for net,polys,top,bot,npth in g.pads.candidates(q,q,.3)):continue
  out.append(q)
print(out)
