"""Actual frozen native board positives and persisted physical negatives."""
import sys,json,copy,subprocess
from pathlib import Path
sys.path[:0]=[str(Path.cwd()/'tools'),str(Path(__file__).parent)]
import pcbnew
from check_exact_endpoint_antipad_union_r01 import ExactEndpointUnionCheck
from hardware_check_return_corridors import circle
from hardware_map_motherboard_domains import sha,write
from hardware_validate_motherboard_return_planes_r06 import exact_twice_area
folder=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r138-logic-reference-collars-r06')
base=folder/'motherboard-motor-bank-A-logic-reference-candidate.kicad_pcb'
manifest=Path('reports/motherboard-power-entry-20261001/motor-bank-A-reference-ready-r141/actual-control-segment-manifest.json')
out=Path('reports/motherboard-return-zoning-20261001/motor-exact-antipad-union-native-controls-r02')
if out.exists():raise ValueError('Fresh immutable native test output required')
out.mkdir();frozen={str(p):sha(p)for p in(base,manifest,Path(__file__),Path(__file__).with_name('check_exact_endpoint_antipad_union_r01.py'))}
decl=dict(return_net='/LOGIC_GND',reference_layers={'F.Cu':'In1.Cu','B.Cu':'In4.Cu'},allow_vias=True,reference_corridor_margin_mm=.4,via_diameter_mm=.5,via_drill_mm=.2,return_stitch_distance_mm=1.)
rows=json.loads(manifest.read_text())['rows'];signal='9e3b3c61-a4fa-4f6d-a8e3-3105c611f45c';via='2b560de3-f84e-4d9e-a5e9-2e7289869ab7';ground='f51de4d1-376b-4ba9-bd45-2472d0d7d531'
def load():
 b=pcbnew.LoadBoard(str(base));b.BuildConnectivity();return b
def items(b):return {t.m_Uuid.AsString():t for t in b.GetTracks()}
def run(b,row=decl,all_rows=False):
 check=ExactEndpointUnionCheck(b,{r['net']:row for r in rows});actual=items(b)
 return [check.segment(actual[r['actual_copper_UUIDs'][0]],row)for r in rows]if all_rows else check.segment(actual[signal],row)
b=load();positive=run(b,all_rows=True)
if len(positive)!=82:raise ValueError('Exact82 actual control obligations drifted')
controls=[]
def rejected(name,mutation,row=decl):
 b=load();mutation(b);b.BuildConnectivity();p=out/(name+'.kicad_pcb');pcbnew.SaveBoard(str(p),b)
 declaration=out/(name+'-declaration.json');write(declaration,row)
 helper=Path(__file__).with_name('check_motor_pg_negative_fresh_process_r01.py')
 result=subprocess.run([sys.executable,str(helper),str(p),str(declaration)],capture_output=True,text=True)
 (out/(name+'-command.txt')).write_text(result.stdout+result.stderr)
 if result.returncode:raise ValueError('Actual native negative process failed '+name)
 parsed=json.loads(result.stdout.strip().splitlines()[-1])
 if not parsed['rejected']:raise ValueError('Actual native negative unexpectedly accepted '+name)
 controls.append(dict(name=name,path=str(p),sha256=sha(p),rejected=True,reason=parsed['reason'],fresh_native_process=True))
rejected('cut_actual_Source_Ground_stitch',lambda b:b.Remove(items(b)[ground]))
rejected('wrong_signal_via_net',lambda b:items(b)[via].SetNetCode(next(t.GetNetCode()for t in b.GetTracks()if t.GetNetname()=='/motherboard_power_entry/MOTION_5V_RAW')))
rejected('wrong_actual_endpoint_position',lambda b:items(b)[via].SetPosition(items(b)[via].GetPosition()+pcbnew.VECTOR2I(pcbnew.FromMM(.01),0)))
wrong=copy.deepcopy(decl);wrong['via_diameter_mm']=.6
rejected('wrong_declared_actual_via_geometry',lambda b:None,wrong)
def cut_reference(b,empty=False):
 hole=circle((pcbnew.FromMM(273.2),pcbnew.FromMM(179.6)),pcbnew.FromMM(.08))
 for z in b.Zones():
  if z.GetIsRuleArea()or z.GetNetname()!='/LOGIC_GND'or not z.HasFilledPolysForLayer(pcbnew.In1_Cu):continue
  poly=pcbnew.SHAPE_POLY_SET();poly.Append(z.GetFilledPolysList(pcbnew.In1_Cu))
  if empty:poly.RemoveAllContours()
  else:poly.BooleanSubtract(hole)
  z.SetFilledPolysList(pcbnew.In1_Cu,poly)
rejected('real_foreign_reference_hole_outside_endpoint_antipad',cut_reference)
rejected('actual_adjacent_reference_plane_absent',lambda b:cut_reference(b,True))
if any(sha(Path(p))!=h for p,h in frozen.items()):raise ValueError('Frozen actual inputs changed')
write(out/'review.json',dict(passed=True,input_sha256=frozen,board_sha256=sha(base),exact82_actual_control_segment_proofs=positive,actual_native_negative_controls=controls,all_circle_radius_margin_Source_stitch_and_annulus_requirements_retained=True,no_area_filter_or_global_precision_change=True,shared_frozen_checker_bytes_unchanged=True,actual_DRC_Source_cluster_and_micro_island_checks_separately_required=True,manufacturing_ready=False))
print('Exact82 actual controls plus six persisted native negatives passed',flush=True)
