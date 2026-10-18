import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_power_groups_native import hits
from hardware_route_logic_return import mm,xy,segment_distance
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/io3-positive-delivery-r08/io3-positive-delivery-candidate.kicad_pcb')
f={x.GetReference():x for x in b.GetFootprints()}
f['C11069'].SetOrientationDegrees(0);f['C11069'].SetPosition(xy((347.5,180.85)))
f['C11070'].SetPosition(xy((353.075,179.75)));f['C11068'].SetPosition(xy((351.799999,183)))
g=Geometry(b);s=(348.975,180.85);e=(348.975,182.2);n='/motherboard_motors/FIELD_GND';gap=.36;bad=[]
for net,polys,top,bot,npth in g.pads.candidates(s,e,gap):
 if net!=n and (npth or bot)and any(hits(s,e,p,gap)for p in polys):bad.append(('pad',net,polys))
for net,a,c,w in g.tracks[pcbnew.B_Cu].candidates(s,e,gap):
 if net!=n and segment_distance(s,e,a,c)<gap+w/2:bad.append(('cu',net,a,c,w))
print(json.dumps(bad))
print('path',g.grid(s,(349.75,182.2),n,pcbnew.B_Cu,.4,step=.1,padding=4,max_nodes=5000))
