"""Freeze reviewed host-only current patch and unchanged authoritative model evidence."""
import hashlib
import json
from pathlib import Path
import sys
sys.dont_write_bytecode=True
import field_current_guard as G
HERE=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 tests=json.loads((HERE/'host-receipt.json').read_bytes());packet=json.loads((HERE/'construction.json').read_bytes())
 if tests['verdict']!='PASS' or tests['tests']!=21 or tests['failures'] or tests['errors'] or tests['skipped']:raise ValueError('Host controls not complete')
 for name,h in tests['source_sha256'].items():
  if digest(HERE/name)!=h:raise ValueError('Tested source changed')
 if any(digest(p)!=h for p,h in packet['input_sha256'].items()):raise ValueError('Original/model/plan evidence changed')
 spec_path=HERE.parent/'constraint-snapshot/0-field_pdn_spec.json';spec=json.loads(spec_path.read_bytes())
 reports={r['id']:G.rail_status(r) for r in spec['rails']}
 old_plan=Path('Z:/pcb-runs/claude-finish/agent-work/field-pdn/testA3/w/design/design.json')
 plan=json.loads(old_plan.read_bytes());arrays=[dict(v,rail_id=rid) for rid,d in plan['nets'].items() for v in d['via_groups'] if abs((v.get('amps') or 0)-3.05)<.001]
 if len(arrays)!=2 or any((v['amps'],v['n'],v['n_req'],v['ok'])!=(3.05,5,7,False) for v in arrays):raise ValueError('Real five-versus-seven array fixture changed')
 receipt={'verdict':'HOST_FIELD_CURRENT_REJECTION_AND_RAW_ACCOUNTING_PASS','host_tests':21,'rails':reports,
  'real_array_source':{'path':str(old_plan),'sha256':digest(old_plan)},'real_arrays':arrays,
  'seven_via_same_current_controls':[G.array_status(v['amps'],7,spec['via']['amps_per_via'],7) for v in arrays],
  'source_and_model_before':packet['input_sha256'],'source_and_model_after':{p:digest(p) for p in packet['input_sha256']},
  'python_executable':{'path':sys.executable,'sha256':digest(sys.executable)},'drop_budget_v_unchanged':spec['drop_budget_v'],
  'partial_scope':'Only original JD01 documented0.096A FIELD_A return cluster; cannot qualify whole rail',
  'existing_multi_island_current_allocation':'Equal cluster split per groups (terminal mode splits per selected pad count); preserved model assumption, not physical current-sharing proof',
  'nonempty_work_directory_policy':'Reject before reading geometry/spec or producing new outputs; preserve old files; final write also refuses existing routes.json',
  'full_rail_qualified':False,'physical_source_rating_qualified':False,'shared_source_modified_at_freeze':False,
  'heavy_planner_execution':False,'gpu_jobs':0,'native_jobs':0,'board_modified':False,'ledger_modified':False}
 (HERE/'qualification-receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
 report='''Field-current planner source repair

The current guard rejects documented load/design/source-limit inconsistencies before any geometry build, raster search or applicable route output. The unchanged cluster maximum assumptions are FA5.036A/FAG5.268A versus design4.58A and limit5.08A; FB6.55A/FBG6.61A versus design4.82A and limit5.32A. These are documented cluster maxima, not measured simultaneous loads. No loads or fitted channels are reduced and no concurrency assumption is added.

All eight design_a current caps are removed. Actual downstream sums now reach root/branch/segment width/drop calculations and via count ceil without current rounding or epsilon suppression. The saved testA3 FB source and load groups each carry3.05A with5actual vias versus7required by the unchanged0.5A/via policy; their5-via status remains failed. A7-via host count control passes only that arithmetic policy, not physical sharing.

Each requested source pad selector and each positive-cluster selector must independently resolve through the original exact resolver. Wildcard selectors retain the existing any-matching-role semantics. Raw per-path and worst voltage drops qualify against the unchanged0.48V draft budget;0.48004V cannot pass by being printed as0.4800V. Existing multi-island equal allocations and per-pad terminal allocations are preserved model assumptions, not physical current-sharing proof.

Twenty-one host controls pass, including actual source AST execution of preflight/constructor rejection before geometry, actual raw expressions, exact saved arrays, partial source/cluster resolution, wildcard semantics, a rounding-hidden drop excess, and actual write-method emission under routes_UNQUALIFIED_DO_NOT_APPLY.json with reasons and no routes.json. Model-valid0.096A partial current requires an explicit partial cluster scope and retains full_rail_qualified=false. Missing scope/positive pads, incomplete arrays, insufficient IPC width, unserved currents or excessive/missing raw drop prevent the applicable filename. Rip-up proposals retain DO_NOT_APPLY. Any nonempty work directory is rejected before input reads, preserving historical outputs and preventing same-OUT stale route reuse; the final write also refuses existing routes.json.

Scalar capacity/material/geometry/clearance constants and unmodified raster/mask/geometry methods remain exact. No heavy planner import/run, GPU job, native job, candidate/board edit or ledger rewrite occurred. Existing full-current source-rating, current-sharing, thermal/fault/transient/return/native/manufacturing qualifications remain open. Earlier reviewed sources and test-harness attempts are preserved separately.
'''
 (HERE/'REPORT.txt').write_text(report,encoding='utf-8')
 sources={name:digest(HERE/name) for name in ('field_current_guard.py','field_pdn_design.py')}
 files={str(p.resolve()):digest(p) for p in HERE.rglob('*') if p.is_file() and p.name not in ('ready.json','installation-receipt.json') and '__pycache__' not in p.parts}
 ready={'verdict':'READY_TESTED_FIELD_CURRENT_PATCH','files':files,'install_files':sources,
  'original_source_sha256':packet['original_source_sha256'],'host_tests':21,'full_rail_qualified':False,
  'scope':'Future field-current model/proposal gates only; explicit partial scope cannot qualify full rail',
  'installed_at_freeze':False,'native_jobs':0,'gpu_jobs':0,'board_modified':False,'ledger_modified':False}
 (HERE/'ready.json').write_text(json.dumps(ready,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'verdict':ready['verdict'],'files':len(files),'install_files':sources,'ready_sha256':digest(HERE/'ready.json')}))
if __name__=='__main__':main()
