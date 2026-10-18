"""Freeze and run the actual native zone-outline transaction checks."""
import hashlib,json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
OUT=Path(__file__).resolve().parent/'native-r01'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
paths=[ROOT/'tools/hardware_merge_bounded_pcb_delta.py',ROOT/'tests/test_reviewed_zone_outlines_native.py']
paths+=list((ROOT/'reports/motherboard-owned-bypass-routing-20261001/native-fixture-r08/top').glob('fixture.kicad_*'))
frozen={str(p):sha(p)for p in paths};OUT.mkdir(exist_ok=False)
run=subprocess.run([sys.executable,str(paths[1])],capture_output=True,text=True)
log=run.stdout+run.stderr;(OUT/'native.log').write_text(log,encoding='utf8')
passed=run.returncode==0 and 'Ran 11 tests' in log and 'OK' in log and all(sha(Path(p))==s for p,s in frozen.items())
receipt=dict(passed=passed,exit_code=run.returncode,native_transaction_cases=1,adversarial_or_scope_cases=10,reported_tests=11,frozen_inputs=frozen,inputs_unchanged=all(sha(Path(p))==s for p,s in frozen.items()),test_only_six_layer_fixture=True,whole_controller_planes_qualified=False,manufacturing_ready=False)
(OUT/'receipt.json').write_text(json.dumps(receipt,indent=2)+'\n');print(json.dumps(receipt));raise SystemExit(not passed)
