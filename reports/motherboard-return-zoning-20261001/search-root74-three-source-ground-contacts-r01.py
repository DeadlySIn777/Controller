import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"tools"));import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_route_logic_return import xy,mm
from hardware_zone_motherboard_returns import split_polygons
from hardware_route_owned_bypass_loops import Geometry
from hardware_bridge_owned_return_resources_r04 import ReferenceGuard,legal_path,source_start_points
from hardware_validate_motherboard_return_planes_r02 import physical_reference_contact
from hardware_validate_motherboard_return_planes_r06 import exact_twice_area
bp=Path("reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb");mp=Path("reports/motherboard-domains-20261001/source26-r74-r01/domain-map.json");rp=Path("reports/motherboard-return-zoning-20261001/source26-r73-exact-literal-native-resource-review-r01.json");op=Path("reports/motherboard-return-zoning-20261001/source26-r74-three-source-ground-contact-proposals-r01.json")
b=pcbnew.LoadBoard(str(bp));b.BuildConnectivity();c=b.GetConnectivity();g=Geometry(b);guard=ReferenceGuard(b,json.loads(mp.read_text()));prior=json.load(open(rp));rows=[]
for r in prior["unanchored_components"]:
 if r["filled_area_mm2"]<1e-6 or r["reference_layer"]!="In4.Cu"or r["filled_piece"]==19 and r["net"]!="/LOGIC_GND":continue
 net=r["net"];w=r["literal_native_positive_metal_provenance"];z=next(z for z in b.Zones()if z.m_Uuid.AsString()==w["zone_uuid"]);target=list(split_polygons(z.GetFilledPolysList(pcbnew.In4_Cu)))[w["literal_filled_piece"]];bb=target.BBox();bounds=[pcbnew.ToMM(v)for v in(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())];starts=source_start_points(target,guard,net,pcbnew.In4_Cu)
 # More exact target interior points near existing real Source-ground vias.
 ends=[]
 for t in b.GetTracks():
  if t.Type()!=pcbnew.PCB_VIA_T or t.GetNetname()!=net or not physical_reference_contact(t,pcbnew.In4_Cu,c):continue
  peers=[p for p in c.GetConnectedItems(t)if p.Type()==pcbnew.PCB_PAD_T and p.GetNumber()and p.GetNetname()==net]
  if not peers:continue
  q=mm(t.GetPosition());distance=math.hypot(max(bounds[0]-q[0],0,q[0]-bounds[2]),max(bounds[1]-q[1],0,q[1]-bounds[3]))
  if distance>20:continue
  ends.append((q,t.m_Uuid.AsString(),dict(reference=peers[0].GetParentFootprint().GetReference(),pin=peers[0].GetNumber())))
  for dx in(-.75,-.5,-.25,0,.25,.5,.75):
   for dy in(-.75,-.5,-.25,0,.25,.5,.75):
    start=(round(q[0]+dx,6),round(q[1]+dy,6))
    if target.Contains(xy(start))and g.clear([start,start],net,pcbnew.In4_Cu,.2):starts.append(start)
 options=sorted((math.dist(s,e),s,e,uid,wit)for s in starts for e,uid,wit in ends);proposals=[]
 for _,s,e,uid,wit in options[:400]:
  path=legal_path(s,e,net,pcbnew.In4_Cu,guard,30,False)
  if path:
   proposals.append(dict(actual_source_via_uuid=uid,actual_source_via_position_mm=e,Source_witness=wit,new_own_In4_ground_contact_path_mm=path,all_physical_reference_foreign_projections_preserved=True));break
 if not proposals:
  for _,s,e,uid,wit in options[:4]:
   path=legal_path(s,e,net,pcbnew.In4_Cu,guard,30,True)
   if path:proposals.append(dict(actual_source_via_uuid=uid,actual_source_via_position_mm=e,Source_witness=wit,new_own_In4_ground_contact_path_mm=path,all_physical_reference_foreign_projections_preserved=True));break
 rows.append(dict(net=net,piece=r["filled_piece"],literal_zone_uuid=w["zone_uuid"],bounds_mm=bounds,target_starts=len(starts),actual_Source_backed_In4_via_ends=len(ends),proposals=proposals));print(rows[-1],flush=True)
write(op,dict(read_only=True,board_sha256=sha(bp),resource_report_sha256=sha(rp),rows=rows,actual_native_DRC_refill_newCuSource_and_oldSource_proof_required=True))
