"""Disconnected release tests and fresh gate reports, only in this audit folder."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
paths = ['tools/check_release.py', 'tests/test_release.py',
         'manufacturing/release-manifest.json', 'manufacturing/product-acceptance.json',
         'reports/prototype-release-check.json', 'reports/production-release-check.json',
         'hardware/motherboard/design.json',
         'hardware/board_review/revisions/20261002-30/motherboard-native-candidate.kicad_pcb']
snapshot = lambda: {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}
before = snapshot()
command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_release.py', '-v']
started = datetime.now(timezone.utc).isoformat()
result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
(OUT / 'product-acceptance-tests.log').write_text(result.stdout + result.stderr, encoding='utf-8', newline='\n')
spec = importlib.util.spec_from_file_location('product_release_check', ROOT / 'tools/check_release.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
manifest = json.loads((ROOT / 'manufacturing/release-manifest.json').read_text())
gates = {stage: module.check_release(manifest, ROOT, stage) for stage in ('prototype', 'production')}
for stage, value in gates.items():
    (OUT / f'{stage}-release-check.json').write_text(json.dumps(value, indent=2) + '\n', encoding='utf-8', newline='\n')
after = snapshot()
receipt = dict(started_utc=started, finished_utc=datetime.now(timezone.utc).isoformat(), command=command,
               returncode=result.returncode, inputs_unchanged=before == after, before=before, after=after,
               gates={stage: dict(ready=value['ready'], blocker_count=len(value['blockers'])) for stage,value in gates.items()},
               scope='Release-checker host tests and local evidence validation only; no hardware/native/target/physical qualification.')
(OUT / 'product-acceptance-verification.json').write_text(json.dumps(receipt,indent=2)+'\n', encoding='utf-8', newline='\n')
print((result.stdout + result.stderr)[-2000:])
print(json.dumps(receipt['gates'],indent=2))
print(json.dumps(dict(returncode=result.returncode, inputs_unchanged=before == after)))
raise SystemExit(result.returncode)
