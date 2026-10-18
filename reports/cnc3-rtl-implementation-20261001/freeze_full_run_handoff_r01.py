"""Bind the final new package to its fresh full disconnected validation run."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
RUN = ROOT / 'reports/pre-hardware-validation-20261001/full-r04'
OUT = BASE / 'full-r04-handoff-r01'
assert not OUT.exists()
OUT.mkdir()
def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

report = json.loads((RUN / 'report.json').read_text())
assert report['status'] == 'BLOCKED'
assert report['status_counts'] == {'BLOCKED': 9, 'NOT_RUN': 1, 'PASS': 17}
assert report['source_hashes_unchanged'] and not report['source_changes']
assert report['original_source_file_count'] == 3327
assert report['manufacturing_ready'] is False
stages = {row['name']: row for row in report['stages']}
for name in ['cnc3_structural_RTL', 'host_suite', 'native_test_replay', 'native_ERC', 'native_DRC', 'source_physical_connectivity', 'historical_linuxcnc_six_two', 'input_integrity']:
    assert stages[name]['status'] == 'PASS', name
host = json.loads((RUN / 'host-cases/receipt.json').read_text())
native = json.loads((RUN / 'native-cases/receipt.json').read_text())
assert host['passed'] and host['passed_tests'] == 1876
assert native['passed'] and native['passed_tests'] == 235 and not native['skipped']
freeze_path = BASE / 'new-package-final-freeze-r01/receipt.json'
freeze = json.loads(freeze_path.read_text())
for relative, digest in freeze['files'].items():
    assert sha(ROOT / relative) == digest, relative
paths = [RUN / 'report.json', RUN / 'provisional-characterization.json',
         RUN / 'host-cases/receipt.json', RUN / 'native-cases/receipt.json',
         RUN / 'cnc3-structural-RTL-evidence/receipt.json',
         RUN / 'cnc3-structural-RTL-evidence/family-synthesis/receipt.json',
         RUN / 'connectivity/review.json', freeze_path,
         BASE / 'peer-scope-cold-state-review-r01/receipt.json']
receipt = {
    'status': 'PASS', 'evidence_scope': 'bounded new CNC3 package/full disconnected validation execution',
    'recorded_utc': datetime.now(timezone.utc).isoformat(),
    'evidence_files': {p.relative_to(ROOT).as_posix(): sha(p) for p in paths},
    'full_bench_status': 'BLOCKED', 'full_bench_status_counts': report['status_counts'],
    'source_hashes_unchanged': True, 'source_file_count': 3327,
    'host_passed': 1876, 'actual_KiCad_native_passed': 235,
    'actual_remaining_platform_skips': 5,
    'Source26_unchanged': True, 'Source27_adopted': False,
    'historical_CNC1_unchanged': True, 'external_spec_changed': False,
    'PCB_changed': False, 'manufacturing_ready': False,
    'stateful_CNC3_endpoint_complete': False, 'CNC3_HAL_implemented': False,
    'physical_measurements': False, 'shared_input_freeze_released': True,
}
(OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'status': 'PASS', 'full_bench': 'BLOCKED', 'host': 1876, 'native': 235, 'source_files': 3327}))
