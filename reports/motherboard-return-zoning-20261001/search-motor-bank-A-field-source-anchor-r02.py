"""Find a genuine own Field return contact; no signal-reference borrowing."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_zone_motherboard_returns import rectangle,return_net
from hardware_route_local_signals import GeometryIndex
from hardware_route_owned_bypass_loops import Geometry
from hardware_route_logic_return import xy,mm
from hardware_bridge_owned_return_resources_r04 import legal_path
from hardware_route_selected_additive import corridor_polygon

bp=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r83-clipped-reference-collars-r02/motherboard-motor-bank-A-clipped-reference-candidate.kicad_pcb')
mp=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r83-source-collar-screen-r02/actual-moved-source-domain-map.json')
inspect=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-field-source-anchor-inspection-r01.json')
out=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-field-source-anchor-proposal-r02.json')
b=pcbnew.LoadBoard(str(bp));b.BuildConnectivity();mapping=json.loads(mp.read_text());g=Geometry(b)
net='/motherboard_motors/FIELD_GND';metal=GeometryIndex()
for row in mapping['pads']:
 if return_net(row)==net:continue
 bounds=row['copper_aabb_mm'];metal.add((row['reference'],row['pin'],rectangle(bounds,.15)),[bounds[0]-.15,bounds[1]-.15,bounds[2]+.15,bounds[3]+.15])
class PowerOnly:
 def clear(self,path,n,layer,width=.2):
  if n!=net or not g.clear(path,n,layer,width):return False
  for a,c in zip(path,path[1:]):
   shape=corridor_polygon(tuple(xy(a)),tuple(xy(c)),pcbnew.FromMM(width/2))
   for ref,pin,other in metal.candidates(a,c,width/2+.15):
    if shape.Collide(other):return False
  return True
facts=json.loads(inspect.read_text());ends=[r for r in facts['nearby_Source_backed_ground_vias']if math.dist(r['xy_mm'],(290,231))<45]
# A true same-domain Ground via within 1 mm of the actual field LED power
# transfer. The eventual native collar must cover its entire .24 mm annulus.
actual=(289.9,233.365);candidates=[]
positions=[(290.7,233.365),(290.7,233.0),(290.7,233.6)]+[(ix/10,iy/10)for ix in range(2890,2911)for iy in range(2325,2343)]
for q in positions:
 if not g.via(q,net)or math.dist(q,actual)>.9:continue
 for e in sorted(ends,key=lambda v:math.dist(v['xy_mm'],q)):
  p=legal_path(q,e['xy_mm'],net,pcbnew.In3_Cu,PowerOnly(),60,False)
  if p:candidates.append(dict(ground_via_xy_mm=q,actual_field_signal_transfer_xy_mm=actual,distance_mm=math.dist(q,actual),Source_backed_existing_Ground_via=e,power_only_In3_Ground_path_mm=p,length_mm=sum(math.dist(a,c)for a,c in zip(p,p[1:]))));break
write(out,dict(read_only=True,input_sha256={str(p):sha(p)for p in(bp,mp,inspect,Path(__file__))},literal_return_net=net,candidates=sorted(candidates,key=lambda r:r['length_mm'])[:10],no_local_reference_or_Source_qualification_claim=True))
print('actual own Ground power transfer candidates',len(candidates),flush=True)
