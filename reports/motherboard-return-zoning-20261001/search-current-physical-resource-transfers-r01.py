"""Read-only exact source-bearing reference resource transfer feasibility."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import split_polygons,return_net
from hardware_route_owned_bypass_loops import Geometry
from hardware_check_return_corridors import circle,covered
from hardware_route_logic_return import mm,xy

board_path=Path(sys.argv[1]);report_path=Path(sys.argv[2]);map_path=Path(sys.argv[3]);out=Path(sys.argv[4])
if out.exists():raise ValueError('Use a fresh review path')
b=pcbnew.LoadBoard(str(board_path));b.BuildConnectivity();report=json.load(open(report_path));mapping=json.load(open(map_path))
if report.get('board_sha256') not in(None,sha(board_path)):raise ValueError('Native resource report binds a different board')
nets={r['net']for r in report['unanchored_components']}
fills=collect_native_reference_fills(b,nets,[pcbnew.In1_Cu,pcbnew.In4_Cu]);pieces={k:list(split_polygons(f))for k,f in fills.items()}
qualified={(r['net'],b.GetLayerID(r['reference_layer']),r['filled_piece'])for r in report['filled_components']if r['passed']}
g=Geometry(b);rows=[]
for r in report['unanchored_components']:
 net=r['net'];layer=b.GetLayerID(r['reference_layer']);other=pcbnew.In4_Cu if layer==pcbnew.In1_Cu else pcbnew.In1_Cu
 p=pieces[net,layer][r['filled_piece']];box=p.BBox();bounds=[pcbnew.ToMM(x)for x in(box.GetX(),box.GetY(),box.GetRight(),box.GetBottom())]
 own=[];projections=[]
 for pad in mapping['pads']:
  if not p.Contains(xy(pad['position_mm'])):continue
  if pad['net']==net:own.append(dict(reference=pad['reference'],pin=pad['pin'],position_mm=pad['position_mm'],copper_layers=pad['copper_layers']))
  if return_net(pad)==net:projections.append(dict(reference=pad['reference'],pin=pad['pin'],net=pad['net'],position_mm=pad['position_mm'],copper_layers=pad['copper_layers']))
 candidates=[]
 if p.Area()>1e6:
  for xindex in range(math.ceil((bounds[0]+.26)*2),math.floor((bounds[2]-.26)*2)+1):
   for yindex in range(math.ceil((bounds[1]+.26)*2),math.floor((bounds[3]-.26)*2)+1):
    q=(xindex/2,yindex/2);v=xy(q)
    if not p.Contains(v):continue
    shape=circle(tuple(v),pcbnew.FromMM(.26))
    if not covered(shape,p):continue
    peer=next((i for i,part in enumerate(pieces.get((net,other),[]))if (net,other,i)in qualified and part.Contains(v)and covered(shape,part)),None)
    if peer is None or not g.via(q,net):continue
    candidates.append(dict(position_mm=list(q),source_anchored_peer_layer=b.GetLayerName(other),peer_filled_piece=peer,own_full_point26mm_ring_both_sides=True,actual_geometry_clear=True))
    if len(candidates)>=8:break
   if len(candidates)>=8:break
 rows.append(dict(net=net,reference_layer=r['reference_layer'],filled_piece=r['filled_piece'],area_mm2=p.Area()/1e12,bounds_mm=bounds,actual_own_SOURCE_ground_pads=own,own_reference_pad_projections=projections,candidate_native_through_return_transfers=candidates,physical_connectivity_or_qualified_delivery_claim=False))
 print(net,r['reference_layer'],r['filled_piece'],'sourcePads',len(own),'candidateTransfers',len(candidates),flush=True)
write(out,dict(board_sha256=sha(board_path),native_resource_report_sha256=sha(report_path),source_map_sha256=sha(map_path),rows=rows,read_only=True,actual_post_refill_SOURCE_witness_native_DRC_and_cluster_preservation_still_required=True,manufacturing_ready=False))
