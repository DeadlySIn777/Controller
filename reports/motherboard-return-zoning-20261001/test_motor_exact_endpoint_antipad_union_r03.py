"""Native positives and six separate fresh-process persisted negative fixtures."""
import sys,json,subprocess,hashlib
from pathlib import Path
sys.path.insert(0,str(Path.cwd()/'tools'))
from hardware_map_motherboard_domains import sha,write
base=Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r138-logic-reference-collars-r06/motherboard-motor-bank-A-logic-reference-candidate.kicad_pcb')
manifest=Path('reports/motherboard-power-entry-20261001/motor-bank-A-reference-ready-r141/actual-control-segment-manifest.json')
out=Path('reports/motherboard-return-zoning-20261001/motor-exact-antipad-union-native-controls-r03')
if out.exists():raise ValueError('Immutable output already exists')
out.mkdir();worker=Path(__file__).with_name('motor_antipad_native_case_r03.py');check=Path(__file__).with_name('check_motor_pg_negative_fresh_process_r01.py')
inputs=[base,manifest,Path(__file__),worker,check,Path(__file__).with_name('check_exact_endpoint_antipad_union_r01.py'),Path('tools/hardware_check_return_corridors.py'),Path('tools/hardware_check_return_corridors_r04.py')];frozen={str(p):sha(p)for p in inputs}
def command(name,args):
 r=subprocess.run([sys.executable,*map(str,args)],capture_output=True,text=True);(out/(name+'-command.txt')).write_text(r.stdout+r.stderr)
 if r.returncode:raise ValueError(name+' native process failed: '+r.stdout+r.stderr)
 return r
command('actual82-positive',[worker,'positive',base,manifest,out/'actual82-positive.json'])
controls=[]
for name in('cut_actual_Source_Ground_stitch','wrong_signal_via_net','wrong_actual_endpoint_position','wrong_declared_actual_via_geometry','real_foreign_reference_hole_outside_endpoint_antipad','actual_adjacent_reference_plane_absent'):
 p=out/(name+'.kicad_pcb');command(name+'-generation',[worker,'negative',base,name,p]);result=command(name+'-evaluation',[check,p,p.with_suffix('.declaration.json')]);parsed=json.loads(result.stdout.strip().splitlines()[-1]);mutation=json.loads(p.with_suffix('.mutation.json').read_text())
 if not parsed['rejected']or not mutation['passed']or mutation['board_sha256']!=sha(p):raise ValueError('Persisted mutation or rejection failed')
 controls.append(dict(name=name,board=str(p),board_sha256=sha(p),rejected=True,reason=parsed['reason'],asserted_actual_mutation=mutation['evidence'],separate_generation_and_evaluation_native_processes=True))
if any(sha(Path(p))!=h for p,h in frozen.items()):raise ValueError('Frozen actual inputs changed')
write(out/'review.json',dict(passed=True,input_sha256=frozen,board_sha256=sha(base),exact82_actual_control_segment_proofs=json.loads((out/'actual82-positive.json').read_text())['exact82_actual_control_segment_proofs'],actual_native_negative_controls=controls,all_circle_radius_margin_Source_stitch_and_annulus_requirements_retained=True,no_area_filter_or_global_precision_change=True,shared_frozen_checker_bytes_unchanged=True,actual_DRC_Source_cluster_and_micro_island_checks_separately_required=True,manufacturing_ready=False));print('Exact82 native positives and six asserted persisted negatives passed')
