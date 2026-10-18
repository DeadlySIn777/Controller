"""Read-only algebra/provenance of one frozen guard rejection.

No checker, circle radius, margin, native copper or source is changed.
"""
import sys,json
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'));import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_check_return_corridors import circle,covered
from hardware_route_selected_additive import corridor_polygon
from hardware_validate_motherboard_return_planes_r06 import exact_twice_area
from hardware_zone_motherboard_returns import split_polygons
folder=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r138-logic-reference-collars-r06')
bp=folder/'motherboard-motor-bank-A-logic-reference-candidate.kicad_pcb'
out=Path('reports/motherboard-return-zoning-20261001/motor-PG-exact-antipad-Boolean-order-r01.json')
if out.exists():raise ValueError('Immutable exact algebra review exists')
b=pcbnew.LoadBoard(str(bp));b.BuildConnectivity();items={t.m_Uuid.AsString():t for t in b.GetTracks()};t=items['9e3b3c61-a4fa-4f6d-a8e3-3105c611f45c']
decl=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,reference_corridor_margin_mm=.4,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.)
check=NativeCollectedAnnulusCheck(b,{t.GetNetname():decl});fill=check.reference('/LOGIC_GND',pcbnew.In1_Cu)
corridor=corridor_polygon(tuple(t.GetStart()),tuple(t.GetEnd()),t.GetWidth()/2+pcbnew.FromMM(.4));old=pcbnew.SHAPE_POLY_SET();old.Append(corridor);augmented=pcbnew.SHAPE_POLY_SET();augmented.Append(fill);circles=[];audits=[]
for endpoint in(tuple(t.GetStart()),tuple(t.GetEnd())):
 for via in check.vias:
  if via.GetNetname()!=t.GetNetname()or tuple(via.GetPosition())!=endpoint:continue
  audit=check.via(via,decl);audits.append(audit)
  radius=pcbnew.FromMM(audit['bounded_antipad_radius_mm']['In1.Cu']);actual=circle(endpoint,radius);circles.append(actual)
  allowed=pcbnew.SHAPE_POLY_SET();allowed.Append(actual);allowed.BooleanSubtract(fill);old.BooleanSubtract(allowed);augmented.BooleanAdd(actual)
old.BooleanSubtract(fill);single=pcbnew.SHAPE_POLY_SET();single.Append(corridor);single.BooleanSubtract(augmented)
residual=[]
for piece in split_polygons(old):
 box=piece.BBox();inside=pcbnew.SHAPE_POLY_SET();inside.Append(piece)
 for actual in circles:inside.BooleanSubtract(actual)
 residual.append(dict(bounds_IU=[box.GetX(),box.GetY(),box.GetRight(),box.GetBottom()],exact_twice_area_nm2=exact_twice_area(piece),literal_polygon=piece.Format(False),outside_reviewed_antipads_twice_area_nm2=exact_twice_area(inside),outside_reviewed_antipads_polygons=inside.Format(False)))
write(out,dict(read_only=True,input_sha256={str(p):sha(p)for p in(bp,Path(__file__))},frozen_guard_repeated_subtraction_rejected=bool(old.OutlineCount()),exact_repeated_subtraction_residuals=residual,single_subtraction_from_fill_union_same_reviewed_antipads_covered=not single.OutlineCount()and exact_twice_area(single)==0,single_residual_native_polygon=single.Format(False),existing_actual_via_annulus_and_Source_stitch_proofs=audits,all_radii_margins_Source_native_checks_unchanged=True,shared_checker_mutated=False,acceptance_pending_new_guard_review_and_meaningful_negative_controls=True))
print(json.dumps(dict(repeated_residuals=len(residual),single_covered=not single.OutlineCount(),residuals=residual),indent=2))
