import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_bridge_owned_return_resources_r03 import ReferenceGuard,source_start_points
from hardware_zone_motherboard_returns import split_polygons,inflation
from hardware_stitch_owned_return_planes import candidate_points
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_map_motherboard_domains import SEEDS
from hardware_route_logic_return import xy
b=pcbnew.LoadBoard('reports/motherboard-return-zoning-20261001/source25-r46-compact-reference-bridges-r05/motherboard-own-return-bridges-candidate.kicad_pcb');m=json.loads(Path('reports/motherboard-return-zoning-20261001/source25-r46-isolation-domain-map-r01/domain-map.json').read_text());g=ReferenceGuard(b,m);fills=collect_native_reference_fills(b,set(SEEDS.values())-{'/CHASSIS'},[pcbnew.In1_Cu,pcbnew.In4_Cu]);tasks=json.loads(Path('reports/motherboard-return-zoning-20261001/source25-r46-opposite-reference-bridges-r06/generation.json').read_text())['required_remaining']
for r in tasks:
 l=b.GetLayerID(r['reference_layer']);n=r['net'];p=list(split_polygons(fills[n,l]))[r['filled_piece']];pts=source_start_points(p,g,n,l)
 print(r,'area',p.Area()/1e12,'safe_start',pts,flush=True)
 for q in list(candidate_points(p))[:6]:
  if p.Contains(xy(q)):print('center',q,'nativeclear',g.geometry.clear([q,q],n,l,.2),'ownprojectionclear',g.clear([q,q],n,l),'barrelclear',g.geometry.via(q,n),flush=True)
