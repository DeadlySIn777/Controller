"""Read-only native Source pin to own adjacent reference contact candidates."""
import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_owned_bypass_loops import Geometry
from hardware_route_logic_return import xy

board=Path(sys.argv[1]);previous=Path(sys.argv[2]);out=Path(sys.argv[3])
if out.exists():raise ValueError('Use a fresh review path')
data=json.load(open(previous));assert sha(board)==data['board_sha256']
b=pcbnew.LoadBoard(str(board));g=Geometry(b);rows=[]
for row in data['rows']:
 if row['candidate_native_through_return_transfers'] or not row['actual_own_SOURCE_ground_pads']:continue
 candidates=[]
 for pad in row['actual_own_SOURCE_ground_pads']:
  layer=pcbnew.F_Cu if 'F.Cu'in pad['copper_layers'] else pcbnew.B_Cu
  for radius in(.65,.85,1.05,1.3,1.6,2,2.5,3):
   for angle in range(0,360,45):
    a=math.radians(angle);p=tuple(pad['position_mm']);q=(round(p[0]+radius*math.cos(a),6),round(p[1]+radius*math.sin(a),6))
    if not g.via(q,row['net'])or not g.clear([p,q],row['net'],layer,.2):continue
    ref=b.GetLayerID(row['reference_layer'])
    if not g.clear([q,p],row['net'],ref,.2):continue
    candidates.append(dict(Source=pad,via_mm=list(q),actual_Source_outer_branch_layer=b.GetLayerName(layer),outer_branch_length_mm=radius,own_reference_contact_layer=row['reference_layer'],inner_same_net_ground_contact_points_mm=[list(q),list(p)],actual_geometry_clear=True,not_a_two_reference_layer_signal_stitch_qualification=True))
    if len(candidates)>=6:break
   if len(candidates)>=6:break
  if candidates:break
 rows.append(dict(net=row['net'],reference_layer=row['reference_layer'],filled_piece=row['filled_piece'],candidates=candidates))
 print(row['net'],row['reference_layer'],row['filled_piece'],len(candidates),flush=True)
write(out,dict(board_sha256=sha(board),input_review_sha256=sha(previous),rows=rows,read_only=True,actual_refill_native_Source_contact_DRC_cluster_proof_still_required=True,manufacturing_ready=False))
