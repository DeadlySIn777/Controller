import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-return-motor-r53/motherboard-bounded-merged-candidate.kicad_pcb');g=Geometry(b);s=(375.775,145);out=[]
for dx in [0,.5,1,-.5,-1,1.5,-1.5]:
 for dy in [-3,-3.5,-4,-4.5]:
  p=(s[0]+dx,s[1]+dy)
  if all(g.clear([p,p],'/LOGIC_GND',l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu])and g.clear([s,p],'/LOGIC_GND',pcbnew.F_Cu,.3):out.append(dict(point=p,length=math.dist(s,p)))
print(json.dumps(out))
