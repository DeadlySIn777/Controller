import sys,json,collections
from pathlib import Path
sys.path.insert(0,str(Path('tools').resolve()))
import pcbnew
from hardware_route_logic_return import xy,mm
from hardware_zone_motherboard_returns import build_side_polygons,inflation
from hardware_map_motherboard_domains import native,classify,positioned
b=pcbnew.LoadBoard('reports/motherboard-power-entry-20261001/motion-raw-delivery-r45/motion-raw-delivery-candidate.kicad_pcb');model=json.loads(Path('hardware/motherboard/design.json').read_text());parts={r:c for r,c in model['components'].items()if c.get('physical',c.get('role')!='schematic_boundary_not_orderable')};nodes,nc,functions=native(Path('hardware/motherboard/netlist.xml'));domains,barriers,*_=classify(parts,nodes,nc);mapping=positioned(b,parts,nodes,nc,functions,domains,barriers);ex=pcbnew.SHAPE_POLY_SET()
for side in['In1.Cu','In4.Cu']:
 regions,barrier,ug=build_side_polygons(mapping,b,side);ex.Append(barrier);ex.Append(ug)
 for r in regions.values():ex.Append(inflation(r,.25))
ex.Simplify();ex.Inflate(pcbnew.FromMM(1),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.01))
for p in[(266.2,171),(343.2,182),(341.275,182.5),(343.2,186)]:print(p,ex.Contains(xy(p)))
start=(266,171);end=(343,182);minx,maxx,miny,maxy=230,360,90,240;step=1;q=collections.deque([start]);prev={start:None};blocked={};done=False
while q:
 p=q.popleft()
 if p==end:done=True;break
 for dx,dy in[(1,0),(-1,0),(0,1),(0,-1)]:
  n=(p[0]+dx,p[1]+dy)
  if n in prev or not(minx<n[0]<maxx and miny<n[1]<maxy):continue
  if n not in blocked:blocked[n]=ex.Contains(xy(n))
  if blocked[n]:continue
  prev[n]=p;q.append(n)
path=[]
if done:
 p=end
 while p:path.append(p);p=prev[p]
 path.reverse()
print(json.dumps(dict(route=path,reachable=len(prev),blocked=len(blocked),ends=done)))
