"""Repeat the unchanged original native predicates after the diagnostic pass."""
import datetime, hashlib, json, os, subprocess
from pathlib import Path
HERE = Path(__file__).resolve().parent
PRIOR = HERE / 'combined-power-source-native-r1'
OUT = HERE / 'combined-power-native-repeat-r3'
def sha(p): return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    if OUT.exists(): raise ValueError('Fresh repeat directory required')
    pins = json.loads((PRIOR / 'inputs.json').read_bytes())
    for p, h in pins.items():
        if sha(p) != h: raise ValueError('Frozen input changed: ' + p)
    cmd = json.loads((PRIOR / 'invocation.json').read_bytes())['command']
    cmd[-1] = str((OUT / 'native-parity.json').resolve())
    OUT.mkdir()
    extra = {str(p.resolve()): sha(p) for p in [Path(__file__), PRIOR / 'receipt.json', HERE / 'combined-power-native-diagnostic-r2/receipt.json']}
    (OUT / 'inputs.json').write_text(json.dumps({'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'inherited': pins, 'extra': extra, 'command': cmd}, indent=1)+'\n', encoding='utf-8')
    env = os.environ.copy()
    env['PATH'] = 'C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;' + env['PATH']
    with (OUT / 'native.log').open('w', encoding='utf-8') as log:
        run = subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT)
    for p, h in {**pins, **extra}.items():
        if sha(p) != h: raise ValueError('Repeat input changed: ' + p)
    api = json.loads((OUT / 'native-parity.json').read_bytes()) if (OUT / 'native-parity.json').exists() else {}
    passed = run.returncode == 0 and api.get('summary', {}).get('parity_defects') == 0 and api.get('added_via_annuli', {}).get('verdict') == 'PASS'
    receipt = {'verdict': 'PASS_ORIGINAL_UNCHANGED_NATIVE_PREDICATES' if passed else 'FAIL_ORIGINAL_UNCHANGED_NATIVE_PREDICATES', 'native_exit_code': run.returncode, 'board_sha256': '65065e41b8243fe150a2231c17bbe8203dd0c4bb3fdbb2b1e0554ff9e14fbd41', 'parity_defects': api.get('summary', {}).get('parity_defects'), 'added_via_count': len(api.get('added_via_annuli', {}).get('rows', [])), 'prior_failure_preserved': True, 'original_failure_cause': 'UNRESOLVED', 'refill_DRC_connectivity': 'NOT_EXECUTED', 'adopted': False}
    (OUT / 'receipt.json').write_text(json.dumps(receipt, indent=1)+'\n', encoding='utf-8')
    print(json.dumps(receipt), flush=True)
    return 0 if passed else 1
if __name__ == '__main__': raise SystemExit(main())
