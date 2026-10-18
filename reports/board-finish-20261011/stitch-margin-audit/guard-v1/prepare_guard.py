"""Create reviewable planner patch and replay its exact guard before installation."""
import hashlib
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = Path('Z:/pcb-runs/claude-finish')
PLANNER = ROOT / 'tools/fix/stitch_plan3.py'
AUDITOR = ROOT / 'agent-work/verify-stitch3/scripts/plan_exact_check.py'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def main():
    raw = PLANNER.read_bytes()
    helper = AUDITOR.read_bytes()
    # Unclassified foreign copper must never inherit the logic domain.
    old = b'd1, d2 = dom.get(n1, "DOM_LOGIC"), dom.get(n2, "DOM_LOGIC")'
    new = b'd1, d2 = dom.get(n1, "UNKNOWN"), dom.get(n2, "UNKNOWN")\n    if not (d1.startswith("DOM_") and d2.startswith("DOM_")):\n        return XDOM'
    if helper.count(old) != 1:
        raise ValueError('Unknown original vector auditor version')
    helper = helper.replace(old, new)
    (HERE / 'stitch_vector_audit.py').write_bytes(helper)
    newline = b'\r\n' if b'\r\n' in raw else b'\n'
    marker = b'json.dump({"plan": plan, "failed": failed,'
    if raw.count(marker) != 1 or b'stitch_exact_guard' in raw:
        raise ValueError('Unknown/unexpected planner version')
    insertion = b'from stitch_exact_guard import validate_plan' + newline
    insertion += b'plan = validate_plan(sys.argv[1], plan, OUT, PADMASK)' + newline
    patched = raw.replace(marker, insertion+marker)
    compile(patched.decode(),str(HERE/'stitch_plan3.py'),'exec')
    (HERE / 'stitch_plan3.py').write_bytes(patched)
    import stitch_exact_guard as guard
    work = ROOT / 'integrate/work/r06-stitch-plane-pads-2'
    plan = json.loads((work/'plan3.json').read_bytes())['plan']
    accepted = guard.validate_plan(work/'copy/geom.json', plan, HERE/'replay.json', work/'pad-mask.json')
    if len(plan) != 188 or len(accepted) != 184:
        raise ValueError('Original r06 regression did not reject exactly four faulty stitches')
    guard.validate_plan(work/'copy/geom.json', accepted, HERE/'accepted-recheck.json', work/'pad-mask.json')
    second = json.loads((HERE/'accepted-recheck.json.vector-guard.json').read_bytes())
    if second['rejected']:
        raise ValueError('Accepted proposals still fail independent vector check')
    result = {'verdict':'PLANNER_EXACT_GUARD_SOURCE_AND_R06_REPLAY_PASS','original_planner_sha256':sha(raw),
        'patched_planner_sha256':sha(patched),'original_auditor_sha256':sha(AUDITOR.read_bytes()),
        'guard_sha256':sha((HERE/'stitch_exact_guard.py').read_bytes()),'helper_sha256':sha(helper),
        'original_r06_proposals':188,'rejected':4,'accepted_and_vector_rechecked':184,
        'installed':False,'gpu_jobs':0,'native_jobs':0,'board_modified':False,
        'limits':['No new raster/GPU planner execution or board application',
                  'Vector guard supplements raster and native gates; it does not qualify electrical design']}
    (HERE/'ready.json').write_text(json.dumps(result,indent=2)+'\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main()
