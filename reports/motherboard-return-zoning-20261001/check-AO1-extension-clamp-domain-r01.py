import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_route_owned_bypass_loops import Geometry
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_route_logic_return import mm
b=pcbnew.LoadBoard('reports/motherboard-pcb-integration-20261001/source26-entry-return-r56/motherboard-bounded-merged-candidate.kicad_pcb');m=json.loads(Path('reports/motherboard-domains-20261001/source26-r56-r01/domain-map.json').read_text());g=Geometry(b);guard=ReferenceGuard(b,m);n='/motherboard_analog_output/AO1_COM';s=(386.375,249.445)
for q in[(386.375,250.245),(386.375,250.345),(386.375,250.445),(386.875,250.345),(387.0,250.345)]:print(q,'barrel',g.via(q,n),'Fbranch',g.clear([s,q],n,pcbnew.F_Cu,.2),'ownIn1Projection',guard.clear([q,q],n,pcbnew.In1_Cu,.2))
print('clamp',[(p['pin'],p['net'],p['domain'],p['position_mm'])for p in m['pads']if p['reference']=='U14012'])
for p in m['pads']:
 a,y,c,d=p['copper_aabb_mm']
 if a<108.0 and c>105.9 and y<287 and d>285:print('near-origin',p['reference'],p['pin'],p['net'],p['domain'],p['position_mm'])
