from pathlib import Path
import sys,json,math
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
import check_literal_CCK_CORE_preservation_r01 as prior
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_check_return_corridors import circle
from hardware_zone_motherboard_returns import split_polygons
from hardware_route_logic_return import mm
p=Path(__file__).parent;out=p/'CORE-collar-pair-antipads-review-r03';out.mkdir(exist_ok=False)
b=pcbnew.LoadBoard(str(p/'CORE-literal-antipad-join-baseline-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb'));a=pcbnew.LoadBoard(str(p/'CORE-literal-antipad-join-cck-r03/motherboard-CORE-literal-antipad-join-candidate.kicad_pcb'))
net='/CORE_1V2';bp=collect_native_reference_fills(b,{net},[pcbnew.In3_Cu])[net,pcbnew.In3_Cu];ap=collect_native_reference_fills(a,{net},[pcbnew.In3_Cu])[net,pcbnew.In3_Cu];removed=prior.f.subtract(bp,ap)
old={t.m_Uuid.AsString()for t in b.GetTracks()};vias=[t for t in a.GetTracks()if t.m_Uuid.AsString()not in old and t.Type()==pcbnew.PCB_VIA_T];mask=pcbnew.SHAPE_POLY_SET();vr=[]
for via in vias:
 r=via.GetWidth(pcbnew.In3_Cu)//2+pcbnew.FromMM(.20);mask.BooleanAdd(circle(tuple(via.GetPosition()),r))
 vr.append(dict(uuid=via.m_Uuid.AsString(),net=via.GetNetname(),xy=mm(via.GetPosition()),diameter_In3_mm=pcbnew.ToMM(via.GetWidth(pcbnew.In3_Cu)),drill_mm=pcbnew.ToMM(via.GetDrill()),FlashLayer_In3=via.FlashLayer(pcbnew.In3_Cu),native_Cu_shape=via.GetEffectiveShape(pcbnew.In3_Cu).Format(),old_mask_radius_mm=pcbnew.ToMM(r)))
residual=prior.f.subtract(removed,mask);rows=[]
for poly in split_polygons(residual):
 box=poly.BBox();rows.append(dict(bounds_mm=[pcbnew.ToMM(v)for v in(box.GetX(),box.GetY(),box.GetRight(),box.GetBottom())],area_mm2=poly.Area()/1e12,exact_polygon=poly.Format(False)))
zones=[dict(uuid=z.m_Uuid.AsString(),net=z.GetNetname(),clearance_mm=pcbnew.ToMM(z.GetLocalClearance()),minimum_thickness_mm=pcbnew.ToMM(z.GetMinThickness()))for z in a.Zones()if z.GetNetname()==net and z.IsOnLayer(pcbnew.In3_Cu)]
report=dict(passed=False,removed_mm2=removed.Area()/1e12,residual_mm2=residual.Area()/1e12,literal_new_vias=vr,literal_actual_CORE_zones=zones,residual_polygons=rows,generic_guard_unchanged=True,manufacturing_ready=False)
(out/'review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(dict(residual_polygons=rows,newvia=vr,zones=zones)))
