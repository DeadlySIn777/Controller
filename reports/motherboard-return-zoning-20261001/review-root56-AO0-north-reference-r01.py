import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_zone_motherboard_returns import polygon,duplicate,split_polygons,rectangle
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import covered
from hardware_route_selected_additive import corridor_polygon
from hardware_route_logic_return import xy
base=Path('reports/motherboard-pcb-integration-20261001/source26-entry-return-r56/motherboard-bounded-merged-candidate.kicad_pcb');mp=Path('reports/motherboard-domains-20261001/source26-r56-r01/domain-map.json');b=pcbnew.LoadBoard(str(base));m=json.loads(mp.read_text());guard=ReferenceGuard(b,m);net='/motherboard_analog_output/AO0_COM'
bounds=[385.4,223.5,398.3,233];proposed=polygon([(385.4,223.5),(398.3,223.5),(398.3,233),(395.4,233),(395.4,225.65),(385.4,225.65)]);foreign=[]
for other,p in guard.indices[pcbnew.In1_Cu].candidates(bounds[:2],bounds[2:],.3):
 if other==net:continue
 hit=duplicate(proposed);hit.BooleanIntersection(p)
 if hit.Area()>1e6:foreign.append(dict(other_return=other,intersection_mm2=hit.Area()/1e12));proposed.BooleanSubtract(p)
for z in b.Zones():
 if z.GetIsRuleArea()and z.GetDoNotAllowZoneFills():proposed.BooleanSubtract(z.Outline())
fill=collect_native_reference_fills(b,{net},[pcbnew.In1_Cu])[net,pcbnew.In1_Cu];combined=duplicate(fill);combined.BooleanAdd(proposed)
routes=[[(385.6,226),(387,224.9),(397,224.9),(397,229.825),(394.875,229.825)],[(385.6,225),(387,224.9),(397.5,224.9),(397.5,231.095),(394.875,231.095)],[(385.6,225.5),(387,224.9),(396.5,224.9),(396.5,232.365),(394.875,232.365)]]
checks=[]
for route in routes:
 checks.append(dict(route_mm=route,actual_F_clear=guard.geometry.clear(route,'/motherboard_analog_output/AO0_DAC_SCLK',pcbnew.F_Cu,.2),proposed_own_In1_corridor_covered=all(covered(corridor_polygon(tuple(xy(s)),tuple(xy(e)),pcbnew.FromMM(.3)),combined)for s,e in zip(route,route[1:]))))
vertices=[[[pcbnew.ToMM(q.x),pcbnew.ToMM(q.y)]for q in p.COutline(0).CPoints()]for p in split_polygons(proposed)]
r=dict(board_sha256=sha(base),source_map_sha256=sha(mp),proposed_only=True,adopted=False,own_return_net=net,proposed_In1_outer_polygons_mm=vertices,proposal_area_mm2=proposed.Area()/1e12,subtracted_actual_foreign_projections=foreign,source_native_barriers=[row for row in m['barriers']if row['reference']=='U14605'],route_screen=checks,actual_source_pads=[p for p in m['pads']if p['reference']in ['U14605','U14608']],manufacturing_ready=False);write(Path('reports/motherboard-return-zoning-20261001/source26-r56-AO0-north-reference-review-r01.json'),r);print(json.dumps({k:v for k,v in r.items()if k not in['actual_source_pads','source_native_barriers','proposed_In1_outer_polygons_mm']},indent=2))
