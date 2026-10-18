"""Retire only the failed, unadopted C17014 addition on combined ROOT60."""
import copy,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from hardware_build_assembly import parse,children,child,value
from hardware_merge_bounded_pcb_delta import without_generated_fills,dump_board
from hardware_populate_motherboard_pcb import sha,write
base=ROOT/'reports/motherboard-pcb-integration-20261001/source26-owned-bypass-r60/motherboard-bounded-merged-candidate.kicad_pcb'
audit=base.parent/'combined-bypass-audit-r02.json';failed=json.loads(audit.read_text())['actual_return_corridor_failures']
if len(failed)!=1 or failed[0]['ref']!='C17014':raise ValueError('Exact reviewed failing addition differs')
ids=set(failed[0]['new_UUIDs'])
out=ROOT/'reports/motherboard-pcb-integration-20261001/source26-rejected-HF-donor-r61'
if out.exists():raise ValueError('Fresh donor required')
out.mkdir();tree=parse(without_generated_fills(base.read_text()));found=set()
for kind in ('segment','via','arc'):
 for obj in list(children(tree,kind)):
  uid=value(child(obj,'uuid')[1])
  if uid in ids:tree.remove(obj);found.add(uid)
if found!=ids:raise ValueError('Rejected actual new Cu missing')
donor=out/'rejected-HF-donor.kicad_pcb';donor.write_text(dump_board(tree))
scope=out/'bounded-scope.json'
write(scope,dict(electrical_source_unchanged=True,reviewed_scope_reason='Retire exactly the five new objects of the unadopted C17014 bypass group. The frozen strict actual checker rejected its CORE5 reference corridor after combination. All other SOURCE lands/poses, old source26 routing and 93 qualified groups remain; this is failed-new-addition retirement, not removal of a required circuit or a manufacturing waiver.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=sorted(ids),reviewed_added_zone_UUIDs=[]))
result=ROOT/'reports/motherboard-pcb-integration-20261001/source26-rejected-HF-r61'
run=subprocess.run([sys.executable,str(ROOT/'tools/hardware_merge_bounded_pcb_delta.py'),'--before',str(base),'--donor',str(donor),'--target',str(base),'--scope',str(scope),'--out',str(result)],cwd=ROOT,capture_output=True,text=True)
(result/'merge-command.txt').write_text(run.stdout+run.stderr)
if run.returncode:raise ValueError(run.stderr[-1800:])
original=ROOT/'reports/motherboard-owned-bypass-routing-20261001/source26-r56-first-batch-r04/receipt.json'
adjusted=json.loads(original.read_text());group=next(g for g in adjusted['owned_loops'] if g['ref']=='C17014')
if set(group['new_UUIDs'])!=ids or not group['retained']:raise ValueError('Original exact group differs')
group['retained']=False
adjusted['required_remaining'].append(dict(ref='C17014',reason='Strict actual CORE5 return corridor failed on combined ROOT60; exactly five new objects retired. Reroute required.'))
adjusted.update(board_sha256=sha(result/'motherboard-bounded-merged-candidate.kicad_pcb'),combined_board_adjustment=dict(original_receipt_path=str(original),original_receipt_sha256=sha(original),rejected_combination_audit_path=str(audit),rejected_combination_audit_sha256=sha(audit),retired_new_UUIDs=sorted(ids)),scope='Only retained group definitions rebased here. Full actual final proof is separate; original donor observations remain history.',passed=False,actual_final_proof_pending=True)
write(result/'rebased-HF-group-ledger.json',adjusted)
report=json.loads((result/'drc.json').read_text())
if report.get('ignored_checks') or any(r['severity']!='warning' for r in report['violations']):raise ValueError('Native error/ignored check; candidate remains unadopted')
write(result/'baseline-disposition.json',dict(board_sha256=sha(result/'motherboard-bounded-merged-candidate.kicad_pcb'),routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=report['violations'],ignored_checks=[]))
print(run.stdout[-1000:],flush=True)
