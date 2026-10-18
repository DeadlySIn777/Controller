"""Complete fresh KiCad checks in an external private output tree, retaining the initial rejection."""
from pathlib import Path
import json
import shutil
import subprocess
import sys
import tempfile
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
external = Path(tempfile.mkdtemp(prefix='controller-audit-20260930-')) / 'native-exports'
start = time.monotonic()
argv = [sys.executable, str(ROOT/'tools/hardware_export_evidence.py'), '--source-root', str(ROOT), '--output-dir', str(external)]
result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=240)
(HERE/'native-exports-external.txt').write_text(result.stdout+result.stderr, encoding='utf-8')
if external.exists():
    shutil.copytree(external, HERE/'native-exports')
data = json.loads((HERE/'check-results.json').read_text(encoding='utf-8'))
data['checks'].append({'name':'native-exports-external', 'argv':argv, 'exit_code':result.returncode,
                       'elapsed_s':round(time.monotonic()-start,3), 'log':'native-exports-external.txt',
                       'note':'Initial attempt was rejected because its output was within the supplied source root. External output retained and copied without changing project inputs.'})
(HERE/'check-results.json').write_text(json.dumps(data,indent=2)+'\n', encoding='utf-8')
print(json.dumps({'exit_code':result.returncode,'external_evidence_retained':str(external),'stdout':result.stdout[-2000:]},indent=2))
sys.exit(result.returncode)
