"""Freeze a minimal planner hook and replay saved ROOT106 proposals, without importing the GPU planner."""
import hashlib
import json
from pathlib import Path
import sys
import time

sys.dont_write_bytecode=True
HERE=Path(__file__).resolve().parent
ROOT=Path('Z:/pcb-runs/claude-finish')
PLANNER=ROOT/'tools/fix/stitch_plan3.py'
ORIGINAL_SHA='269682296227d1ebf58d1ce1cf8ad556b9f7efd9e8b380078d64fb7eae08622c'
def digest(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 started=time.time()
 prefix=sys.argv[1] if len(sys.argv)>1 else ''
 if prefix not in ('','final-','final2-'):raise ValueError('Unexpected receipt prefix')
 identities=json.loads((HERE.parent/'inputs.json').read_bytes())['identities']
 for p,h in identities.items():
  if digest(p)!=h:raise ValueError('Historical input changed: '+p)
 if digest(PLANNER)!=ORIGINAL_SHA:raise ValueError('Unexpected live original planner')
 v1={str(p.resolve()):digest(p) for p in (HERE.parent/'guard-v1').iterdir() if p.is_file()}
 raw=PLANNER.read_bytes();nl=b'\r\n' if b'\r\n' in raw else b'\n'
 marker=b'json.dump({"plan": plan, "failed": failed,'
 if raw.count(marker)!=1 or b'stitch_exact_guard' in raw:raise ValueError('Unexpected planner hook boundary')
 hook=nl.join([b'from stitch_exact_guard import validate_plan',
  b'plan, vector_failed = validate_plan(sys.argv[1], plan, OUT, PADMASK,',
  b'    existing_failed=failed, target_count=sum(len(v) for v in targets.values()),',
  b'    dependency_paths=(__file__, DRU))', b'failed.extend(vector_failed)',b''])
 patched=raw.replace(marker,hook+marker)
 for name in ('stitch_exact_guard.py','stitch_vector_audit.py'):
  compile((HERE/name).read_text(encoding='utf-8'),str(HERE/name),'exec')
 compile(patched.decode(),str(HERE/'stitch_plan3.py'),'exec')
 (HERE/'stitch_plan3.py').write_bytes(patched)
 (HERE/'planner-hook.py.txt').write_bytes(hook)
 (HERE/'original-stitch_plan3.py').write_bytes(raw)
 import stitch_exact_guard as guard
 work=ROOT/'integrate/work/r06-stitch-plane-pads-2'
 document=json.loads((work/'plan3.json').read_bytes())
 if (document['targets'],len(document['plan']),len(document['failed']))!=(436,188,248):raise ValueError('Historical target census differs')
 dependencies=tuple(identities)+ (str(PLANNER),str(HERE/'prepare_v2.py'))
 result=guard.filter_document(work/'copy/geom.json',document,HERE/(prefix+'replay.json'),work/'pad-mask.json',dependencies)
 if (result['targets'],len(result['plan']),len(result['failed']))!=(436,184,252):raise ValueError('Filtered 436 target census differs')
 original_bad=[r for r in json.loads((HERE.parent/'exact.json').read_bytes())['rows'] if r['viol']]
 new_bad=result['failed'][len(document['failed']):]
 if [(r['ref']+'.'+r['pad'],r['net'],r['viol']) for r in original_bad]!=[(r['pad'],r['net'],r['vector_violations']) for r in new_bad]:raise ValueError('Rejected four do not match original exact audit')
 accepted,additional=guard.validate_plan(work/'copy/geom.json',result['plan'],HERE/(prefix+'accepted-recheck.json'),work/'pad-mask.json',existing_failed=result['failed'],target_count=436,dependency_paths=dependencies)
 if accepted!=result['plan'] or additional:raise ValueError('Accepted 184 fail independent recheck')
 (HERE/(prefix+'filtered-plan.json')).write_text(json.dumps(result,indent=1)+'\n',encoding='utf-8')
 for p,h in identities.items():
  if digest(p)!=h:raise ValueError('Historical input changed during replay: '+p)
 if v1!={str(p.resolve()):digest(p) for p in (HERE.parent/'guard-v1').iterdir() if p.is_file()}:raise ValueError('v1 altered')
 receipt={'verdict':'R06_436_TARGET_ACCOUNTING_AND_184_VECTOR_RECHECK_PASS','exit_code':0,
  'elapsed_seconds':round(time.time()-started,3),'targets':436,'original_planned':188,'original_failed':248,
  'accepted':184,'failed_after':252,'new_failed':new_bad,'accepted_recheck_violations':0,
  'historical_input_sha256_before':identities,'historical_input_sha256_after':{p:digest(p) for p in identities},
  'preserved_v1_sha256_before':v1,'preserved_v1_sha256_after':{p:digest(p) for p in v1},
  'original_planner_sha256':ORIGINAL_SHA,'patched_planner_sha256':digest(HERE/'stitch_plan3.py'),
  'guard_sha256':digest(HERE/'stitch_exact_guard.py'),'helper_sha256':digest(HERE/'stitch_vector_audit.py'),
  'installed':False,'gpu_jobs':0,'native_jobs':0,'board_modified':False,
  'scope':'Exact ROOT106450x235 saved geometry/proposal replay; no GPU planner execution or board application',
  'limits':['Loaded Python module/helper/input hashes before and after are pinned; operating-system DLLs are outside this inventory',
   'Stored-fill/vector proof does not establish fresh native connectivity, rooted return, current capacity or full electrical qualification']}
 (HERE/(prefix+'replay-receipt.json')).write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8')
 print(json.dumps({k:receipt[k] for k in ('verdict','targets','accepted','failed_after','accepted_recheck_violations','elapsed_seconds')}))
if __name__=='__main__':main()
