"""Capture final host guard tests; verify unchanged firmware against ARM r02."""
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / 'runtime-host-r03'
OUT.mkdir(exist_ok=False)
before = json.loads((OUT.parent / 'firmware-runtime-before.json').read_text(encoding='utf-8'))
raw = {name: (ROOT / name).read_bytes() for name in before['source_sha256']}
patches = []
for name, data in raw.items():
    target = OUT / 'inputs' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_bytes(data)
    old = (OUT.parent / 'before' / name).read_bytes()
    patches.extend(difflib.unified_diff(old.decode('utf-8').splitlines(keepends=True),
        data.decode('utf-8').splitlines(keepends=True), fromfile='original/' + name, tofile=name))
(OUT / 'firmware-runtime-final.diff').write_text(''.join(patches), encoding='utf-8', newline='')
started = datetime.now(timezone.utc).isoformat()

def run(pattern):
    proc = subprocess.run([sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', pattern, '-v'],
                          cwd=ROOT, capture_output=True, text=True)
    text = proc.stdout + proc.stderr
    (OUT / (pattern + '.log')).write_text(text, encoding='utf-8')
    count = re.search(r'Ran (\d+) tests?', text)
    return {'pattern': pattern, 'exit_code': proc.returncode, 'tests': int(count[1]) if count else None}

with ThreadPoolExecutor(max_workers=5) as executor:
    results = list(executor.map(run, ['test_runtime_configuration.py', 'test_persistent_runtime.py',
                  'test_configuration_recovery.py', 'test_motherboard_iol1_readonly.py', 'test_recovery_cli.py']))
r02 = json.loads((OUT.parent / 'firmware-host-target-r02/receipt.json').read_text(encoding='utf-8'))
firmware_current = all(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == sha
                       for name, sha in r02['input_sha256'].items() if name.startswith('firmware/'))
receipt = {'started_utc': started, 'completed_utc': datetime.now(timezone.utc).isoformat(),
           'scope': 'disconnected host tests; no HAL/device connection', 'python_host_suites': results,
           'source_sha256': {name: hashlib.sha256(data).hexdigest() for name, data in raw.items()},
           'inputs_unchanged': all((ROOT / name).read_bytes() == data for name, data in raw.items()),
           'firmware_sources_match_r02_compiled_inputs': firmware_current,
           'firmware_compilation_receipt': '../firmware-host-target-r02/receipt.json',
           'C_checks_or_target_compilation_rerun': False, 'physical_tests': False,
           'HDL_rerun': False, 'production_ready': False}
(OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps({key: value for key, value in receipt.items() if key != 'source_sha256'}, indent=2))
raise SystemExit(0 if receipt['inputs_unchanged'] and firmware_current and all(row['exit_code'] == 0 for row in results) else 1)
