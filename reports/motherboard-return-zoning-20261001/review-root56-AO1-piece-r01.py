import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import return_net,pad_supports_reference,track_supports_reference,split_polygons,rectangle
board=Path('reports/motherboard-pcb-integration-20261001/source26-entry-return-r56/motherboard-bounded-merged-candidate.kicad_pcb');mp=Path('reports/motherboard-domains-20261001/source26-r56-r01/domain-map.json');m=json.loads(mp.read_text());b=pcbnew.LoadBoard(str(board));net='/motherboard_analog_output/AO1_COM';l=pcbnew.In1_Cu;piece=list(split_polygons(collect_native_reference_fills(b,{net},[l])[net,l]))[1];box=piece.BBox();domains={p['net']:p['domain']for p in m['pads']};ps=[];ts=[]
for p in m['pads']:
 if return_net(p)==net and pad_supports_reference(p,'In1.Cu')and piece.Collide(rectangle(p['copper_aabb_mm']),pcbnew.FromMM(.4)):ps.append(p)
for t in b.GetTracks():
 if return_net(dict(domain=domains.get(t.GetNetname()),net=t.GetNetname()))==net and track_supports_reference(b,t,'In1.Cu')and piece.Collide(t.GetEffectiveShape(),pcbnew.FromMM(.4)):ts.append(dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),layer=b.GetLayerName(t.GetLayer()),start_mm=[pcbnew.ToMM(v)for v in t.GetStart()],end_mm=[pcbnew.ToMM(v)for v in t.GetEnd()]))
r=dict(board_sha256=sha(board),source_map_sha256=sha(mp),return_net=net,reference_layer='In1.Cu',filled_piece=1,area_mm2=piece.Area()/1e12,bounds_mm=[pcbnew.ToMM(v)for v in(box.GetX(),box.GetY(),box.GetRight(),box.GetBottom())],exact_SOURCE_pad_projections=ps,exact_SOURCE_copper_projections=ts,source_projection_needed=bool(ps or ts),passed=False,no_mutation=True)
write(Path('reports/motherboard-return-zoning-20261001/source26-r56-AO1-unanchored-piece-review-r01.json'),r);print(json.dumps({**r,'exact_SOURCE_pad_projections':[(p['reference'],p['pin'],p['net'])for p in ps]},indent=2))
