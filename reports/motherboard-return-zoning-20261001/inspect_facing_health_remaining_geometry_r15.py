"""Read-only exact frozen-loop failures and positive literal unused-piece geometry."""
import sys,json,argparse
from pathlib import Path
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
from hardware_map_motherboard_domains import sha,write
from hardware_check_return_corridors_r04 import NativeCollectedAnnulusCheck
from hardware_collect_native_reference_fills import collect_native_reference_fills
from hardware_route_selected_additive import corridor_polygon
from hardware_zone_motherboard_returns import split_polygons,rectangle
from hardware_validate_motherboard_return_planes_r06 import exact_twice_area
from hardware_route_logic_return import mm
import importlib.util
ap=argparse.ArgumentParser();ap.add_argument('--folder',type=Path,required=True);a=ap.parse_args();D=a.folder;B=D/'motherboard-facing-health-Source-collars-candidate.kicad_pcb';M=D/'current108-final-bypass-manifest.json';R=D/'full-native-resource-review.json';O=D/'exact-remaining-geometry-r15.json';assert not O.exists()
OWN=Path('reports/motherboard-bypass-owners-20261001/complete723-source26-r11/capacitor-owners.json');inputs={str(p):sha(p)for p in(B,M,R,OWN,Path(__file__))}
b=pcbnew.LoadBoard(str(B));b.BuildConnectivity();cu={t.m_Uuid.AsString():t for t in b.GetTracks()};fps={f.GetReference():f for f in b.GetFootprints()};owner={r['ref']:r for r in json.loads(OWN.read_text())['capacitors']};manifest=json.loads(M.read_text());checker=NativeCollectedAnnulusCheck(b,{});loop_fail=[];passed=[]
for g in manifest['owned_loops']:
 if not g['retained']:continue
 row=owner[g['ref']];fp=fps[row['ref']];supply=next(p.GetNetname()for p in fp.Pads()if p.GetNumber()==row['cap_power']);ret=next(p.GetNetname()for p in fp.Pads()if p.GetNumber()==row['cap_return']);decl=dict(return_net=ret,reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.,reference_corridor_margin_mm=.10);checker.rows={supply:decl};checker.audits={};failed=[]
 for uid in g['new_UUIDs']:
  t=cu[uid]
  if t.GetNetname()!=supply:continue
  try:proof=checker.via(t,decl)if t.Type()==pcbnew.PCB_VIA_T else checker.segment(t,decl)
  except ValueError as e:failed.append(dict(uuid=uid,error=str(e),net=supply,layer=b.GetLayerName(t.GetLayer()),start_mm=mm(t.GetStart()),end_mm=mm(t.GetEnd()),width_mm=pcbnew.ToMM(t.GetWidth())))
 if failed:loop_fail.append(dict(ref=g['ref'],owner=g['owner'],failed_items=failed))
 else:passed.append(g['ref'])
resources=json.loads(R.read_text());zones={z.m_Uuid.AsString():z for z in b.Zones()};pieces=[]
for r in resources['unanchored_components']:
 provenance=r['literal_native_positive_metal_provenance'];z=zones[provenance['zone_uuid']];layer=b.GetLayerID(r['reference_layer']);part=list(split_polygons(z.GetFilledPolysList(layer)))[provenance['literal_filled_piece']];assert exact_twice_area(part)==provenance['literal_native_twice_area_nm2'];bb=part.BBox();bounds=[pcbnew.ToMM(v)for v in(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())];cut=rectangle(bounds,.01);contacts=[p.m_Uuid.AsString()for p in b.GetPads()if p.IsOnLayer(layer)and cut.Collide(p.GetEffectiveShape(layer))]+[t.m_Uuid.AsString()for t in b.GetTracks()if t.IsOnLayer(layer)and cut.Collide(t.GetEffectiveShape(layer))];pieces.append(dict(zone_uuid=provenance['zone_uuid'],net=r['net'],layer=r['reference_layer'],literal_piece=provenance['literal_filled_piece'],exact_polygon=part.Format(False),exact_vertices_nm=[[[part.COutline(j).CPoint(i).x,part.COutline(j).CPoint(i).y]for i in range(part.COutline(j).PointCount())]for j in range(part.OutlineCount())],exact_twice_area_nm2=exact_twice_area(part),bounds_mm=bounds,cut_bounds_mm=[bounds[0]-.01,bounds[1]-.01,bounds[2]+.01,bounds[3]+.01],native_Source_conductor_intersections=contacts))
P=Path('reports/motherboard-ordinary-routing-20261001/check_io3_backbone_preservation_r07.py');sp=importlib.util.spec_from_file_location('r07',P);m=importlib.util.module_from_spec(sp);sp.loader.exec_module(m);BASE=Path('reports/motherboard-pcb-integration-20261001/IO3-BankA-complete-antipad-cleanup-baseline-r99a-r02/motherboard-IO3-literal-tip-cleanup-candidate.kicad_pcb');before=pcbnew.LoadBoard(str(BASE));p=collect_native_reference_fills(before,{'/IO_3V3'},[pcbnew.In2_Cu])['/IO_3V3',pcbnew.In2_Cu];q=collect_native_reference_fills(b,{'/IO_3V3'},[pcbnew.In2_Cu])['/IO_3V3',pcbnew.In2_Cu];core=m.duplicate(p);core.Deflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened=m.duplicate(core);opened.Inflate(pcbnew.FromMM(.502),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,pcbnew.FromMM(.001));opened.BooleanIntersection(p);opened.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);narrow=m.subtract(p,opened);aq=m.duplicate(q);aq.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1);escaped=m.subtract(narrow,aq);cuts=[]
for piece in split_polygons(escaped):
 bb=piece.BBox();bounds=[pcbnew.ToMM(v)for v in(bb.GetX(),bb.GetY(),bb.GetRight(),bb.GetBottom())];near=[dict(uuid=t.m_Uuid.AsString(),net=t.GetNetname(),xy_mm=mm(t.GetPosition()))for t in b.GetTracks()if t.Type()==pcbnew.PCB_VIA_T and bounds[0]-2<=mm(t.GetPosition())[0]<=bounds[2]+2 and bounds[1]-2<=mm(t.GetPosition())[1]<=bounds[3]+2];cuts.append(dict(bounds_mm=bounds,area_mm2=piece.Area()/1e12,exact_native_polygon=piece.Format(False),nearby_vias=near))
assert all(sha(Path(p))==h for p,h in inputs.items());result=dict(passed=False,diagnostic_only=True,board_sha256=sha(B),input_sha256=inputs,passed_loops=passed,failed_loops=loop_fail,unanchored_literal_pieces=pieces,IO3_narrow_rejected_polygons=cuts,guard_unchanged=True);write(O,result);print(json.dumps(dict(passed_loops=len(passed),failed_loops=loop_fail,unused_pieces=pieces,IO3_cuts=cuts)),flush=True)
