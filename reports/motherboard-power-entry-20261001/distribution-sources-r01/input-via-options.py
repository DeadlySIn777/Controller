import sys,json
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_current_delivery_native import Geometry
from hardware_route_power_groups_native import hits
from hardware_route_logic_return import segment_distance
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/io3-positive-delivery-r08/io3-positive-delivery-candidate.kicad_pcb');g=Geometry(b);net='/motherboard_power_entry/MOTION_5V_RAW';out=[]
for x in [343.2,343.3,343.4,343.5,343.6,343.7]:
 for y in [181.3,181.4,181.5,181.6,181.7,181.8,181.9,182,182.1,182.2,182.3,182.4,182.5,182.6,182.7]:
  p=(x,y)
  if all(g.clear([p,p],net,l,.5)for l in [pcbnew.F_Cu,pcbnew.B_Cu]):out.append(p)
print(json.dumps(dict(clear=out)))
for p in [(343.2,181.3),(343.5,181.3)]:
 for l in [pcbnew.F_Cu,pcbnew.B_Cu]:
  bad=[]
  for n,polys,top,bot,npth in g.pads.candidates(p,p,.41):
   if n!=net and (npth or(top if l==pcbnew.F_Cu else bot))and any(hits(p,p,v,.41)for v in polys):bad.append(('pad',n,polys))
  for n,s,e,w in g.tracks[l].candidates(p,p,.41):
   if n!=net and segment_distance(p,p,s,e)<.41+w/2:bad.append(('cu',n,s,e,w))
  print(json.dumps(dict(point=p,layer=b.GetLayerName(l),bad=bad)))
