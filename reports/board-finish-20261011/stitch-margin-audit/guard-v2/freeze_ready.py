"""Freeze reviewed source/host evidence; this does not launch the planner or install anything."""
import difflib
import hashlib
import json
from pathlib import Path
HERE=Path(__file__).resolve().parent
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 receipt=json.loads((HERE/'final2-replay-receipt.json').read_bytes());tests=json.loads((HERE/'host-receipt.json').read_bytes())
 if tests['verdict']!='PASS' or tests['tests']!=16 or tests['failures'] or tests['errors'] or tests['skipped']:raise ValueError('Host controls not complete')
 if (receipt['targets'],receipt['accepted'],receipt['failed_after'],receipt['accepted_recheck_violations'])!=(436,184,252,0):raise ValueError('Historical accounting/recheck differs')
 names=('stitch_vector_audit.py','stitch_exact_guard.py','stitch_plan3.py')
 sources={name:digest(HERE/name) for name in names}
 if tests['tested_source_sha256']!=sources:raise ValueError('Host tested source changed')
 if receipt['guard_sha256']!=sources['stitch_exact_guard.py'] or receipt['helper_sha256']!=sources['stitch_vector_audit.py'] or receipt['patched_planner_sha256']!=sources['stitch_plan3.py']:raise ValueError('Actual replay source changed')
 for p,h in receipt['historical_input_sha256_before'].items():
  if digest(p)!=h:raise ValueError('Historical input changed')
 for p,h in receipt['preserved_v1_sha256_before'].items():
  if digest(p)!=h:raise ValueError('v1 changed')
 for stem in ('final2-replay.json','final2-accepted-recheck.json'):
  r=json.loads((HERE/(stem+'.vector-guard.json')).read_bytes())
  for table in ('input_sha256_before','input_sha256_after'):
   if any(digest(p)!=h for p,h in r[table].items()):raise ValueError('Replay input/helper changed')
  provenance=r['helper_dependency_provenance']
  for table in ('before','after','inputs_before','inputs_after'):
   if any(digest(p)!=h for p,h in provenance[table].items()):raise ValueError('Executed helper dependency changed')
 original=Path('Z:/pcb-runs/claude-finish/agent-work/verify-stitch3/scripts/plan_exact_check.py')
 (HERE/'helper-original-to-v2.diff').write_text(''.join(difflib.unified_diff(original.read_text().splitlines(True),(HERE/'stitch_vector_audit.py').read_text().splitlines(True),fromfile=str(original),tofile='stitch_vector_audit.py')),encoding='utf-8')
 (HERE/'planner-original-to-v2.diff').write_text(''.join(difflib.unified_diff((HERE/'original-stitch_plan3.py').read_text().splitlines(True),(HERE/'stitch_plan3.py').read_text().splitlines(True),fromfile='original-stitch_plan3.py',tofile='stitch_plan3.py')),encoding='utf-8')
 report='''ROOT106 stitch planner margin guard v2

The mandatory hook runs before the existing planner JSON save. Each independent vector rejection becomes a failed target with its original ref.pad, net, reason, full proposal and vector violations. The original188 proposal replay rejects exactly4 same-domain via gaps:0.145/0.110/0.145/0.145mm against0.15mm. The184 accepted proposals independently recheck with zero violations. All436 targets remain accounted:184 accepted+252 failed (248 original+4 vector rejections).

Sixteen host controls pass, including malformed dimensions/nonfinite values, classless and unknown-domain inputs, contradictory classes, duplicated planned/failed physical roles, fabricated failed pad identities, exact pad pose/layer identity, target-count mismatch, input/output alias rejection, actual unknown foreign copper0.6mm cross-domain behavior, and isolated execution of the real final planner hook plus its original JSON-save AST. No Torch/CUDA planner import or execution occurred.

The original Claude vector helper is preserved and hashed. The v2 helper adds conservative unknown-domain handling plus before/after identity for every loaded Python module file, the executed helper/interpreter and every vector input; the outer guard also binds its own source, planner and rules. Historical board/geometry/project/rules/padmask/removal receipts and all v1 files remain unchanged. Operating-system DLLs are outside the Python module-file inventory.

Scope is explicit ROOT106450x235 only. Existing vector coverage/rounding limits remain: stored-fill landing is not fresh native fill/connectivity, a rooted return or current capacity; reservations, matching project and uncapped partitions/API/DRC/electrical qualification remain separate gates. This closes the measured planner margin failure before any future JSON save; it does not restart stitches, apply copper, rewrite a ledger or qualify manufacture.

Initial and final-prefixed replay receipts are preserved; final2 receipts bind the final strict failed-pad identity implementation. Original planner SHA269682296227d1ebf58d1ce1cf8ad556b9f7efd9e8b380078d64fb7eae08622c is backed up before authorized installation. Installation receipt separately records exact installed hashes, live board/ledger hashes and the active combined measurement's frozen read-set before/after.
'''
 (HERE/'REPORT.txt').write_text(report,encoding='utf-8')
 files={str(p.resolve()):digest(p) for p in HERE.iterdir() if p.is_file() and p.name not in ('ready.json','installation-receipt.json')}
 result={'verdict':'READY_TESTED_ROOT106_VECTOR_GUARD_V2','files':files,'install_files':sources,
  'original_planner_sha256':receipt['original_planner_sha256'],'original_vector_helper_sha256':digest(original),
  'preserved_v1_files':receipt['preserved_v1_sha256_before'],'targets':436,'accepted':184,'failed_after':252,
  'new_failed':4,'accepted_recheck_violations':0,'host_tests':16,'installed_at_freeze':False,
  'gpu_jobs':0,'native_jobs':0,'board_modified':False,'ledger_modified':False,
  'scope':'ROOT106450x235 host vector filter mandatory before planner JSON save; separate fresh native/electrical qualification required'}
 (HERE/'ready.json').write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({'verdict':result['verdict'],'files':len(files),'install_files':sources,'ready_sha256':digest(HERE/'ready.json')}))
if __name__=='__main__':main()
