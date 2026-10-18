import sys,json,math
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/"tools"));import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_zone_motherboard_returns import split_polygons
from hardware_index_literal_reference_coverage import LiteralReferenceCoverage
from hardware_check_return_corridors import circle,covered
from hardware_route_logic_return import xy,mm
from hardware_route_owned_bypass_loops import Geometry
bp=Path("reports/motherboard-pcb-integration-20261001/source26-local-CMOS-returns-adopted-r74/motherboard-source26-WIP.kicad_pcb");rp=Path("reports/motherboard-return-zoning-20261001/source26-r73-exact-literal-native-resource-review-r01.json");op=Path("reports/motherboard-return-zoning-20261001/source26-r74-three-actual-return-transfer-proposals-r01.json")
b=pcbnew.LoadBoard(str(bp));g=Geometry(b);review=json.loads(rp.read_text());nets={"/LOGIC_GND","/motherboard_do/FIELD_B_0V"};fills=collect_native_reference_fills(b,nets,[pcbnew.In1_Cu,pcbnew.In4_Cu]);pieces={k:list(split_polygons(v))for k,v in fills.items()};fast=LiteralReferenceCoverage(b,nets,[pcbnew.In1_Cu,pcbnew.In4_Cu]);rows=[]
for r in review["unanchored_components"]:
 if r["filled_area_mm2"]<1e-6 or r["reference_layer"]!="In4.Cu"or r["filled_piece"]==19 and r["net"]!="/LOGIC_GND":continue
 net=r["net"];literal=r["literal_native_positive_metal_provenance"];z=next(z for z in b.Zones()if z.m_Uuid.AsString()==literal["zone_uuid"]);target=list(split_polygons(z.GetFilledPolysList(pcbnew.In4_Cu)))[literal["literal_filled_piece"]];box=target.BBox();bounds=[pcbnew.ToMM(v)for v in(box.GetX(),box.GetY(),box.GetRight(),box.GetBottom())];chosen=[];count=0
 for xs in range(math.ceil(bounds[0]*5),math.floor(bounds[2]*5)+1):
  for ys in range(math.ceil(bounds[1]*5),math.floor(bounds[3]*5)+1):
   q=(xs/5,ys/5)
   if not target.Contains(xy(q))or not g.via(q,net):continue
   circ=circle(tuple(xy(q)),pcbnew.FromMM(.24))
   if not covered(circ,target)or not fast.candidate_covered(circ,net,pcbnew.In1_Cu):continue
   anchored=[p for rr in review["filled_components"]if rr["net"]==net and rr["reference_layer"]=="In1.Cu"and rr["passed"]for p in [pieces[net,pcbnew.In1_Cu][rr["filled_piece"]]]if p.Contains(xy(q))]
   if not anchored:continue
   if not fast.final_full_covered(circ,net,pcbnew.In1_Cu):continue
   chosen.append(dict(via_mm=q,exact_own_both_reference_circle_radius_mm=.24,opposite_In1_piece_has_reviewed_actual_Source_witness=True));count+=1
   if count>=4:break
  if count>=4:break
 rows.append(dict(net=net,unanchored_In4_piece=r["filled_piece"],literal_source_zone=literal["zone_uuid"],bounds_mm=bounds,candidates=chosen,only_geometry_and_existing_source_piece_screen=True));print(net,r["filled_piece"],bounds,chosen,flush=True)
write(op,dict(read_only=True,board_sha256=sha(bp),prior_resource_report_sha256=sha(rp),rows=rows,new_native_annulus_Source_and_independent_proof_required=True))
