"""Record successful existing outputs and exact sources; does not run tests."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

root=Path(__file__).resolve().parents[2]
directory=root/'cnc1/evidence'
compiled=(directory/'compiled-rtl-tests.log').read_text()
count=re.search(r'CNC1_COMPILED_RTL_CHECKS=(\d+)',compiled)
if not count or int(count[1])<157 or 'FAIL ' in compiled:
    raise SystemExit('No complete passing compiled integration record')
baseline=(directory/'baseline-regression.log').read_text()
if 'ALL 180 CHECKS PASSED' not in baseline or 'Python independently decoded RTL status' not in baseline:
    raise SystemExit('Missing default-v1 regression evidence')
runtime=json.loads((directory/'linuxcnc.json').read_text())
if not runtime['success'] or len(runtime['checks'])!=11 or not all(c['passed'] for c in runtime['checks']):
    raise SystemExit('Real LinuxCNC integration evidence is incomplete')
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
files=[]
for pattern in ('cnc1/src/*','cnc1/tests/*','cnc1/tools/*','cnc1/profiles/sim/*',
                'cnc1/*.py','cnc1/*.md','gateware/rtl/*.v','reports/CNC1_INTEGRATION.md'):
    files.extend(p for p in root.glob(pattern) if p.is_file() and '.var' not in p.name)
evidence=[directory/name for name in ('compiled-rtl-tests.log','baseline-regression.log','linuxcnc.json','linuxcnc.log','build-packages.tsv')]
manifest={'recorded_utc':datetime.now(timezone.utc).isoformat(),
          'scope':'compiled common/HAL driver + actual RTL simulation; physical transports absent',
          'compiled_checks':int(count[1]),'default_v1_checks':180,'linuxcnc_checks':11,
          'runtime_run_id':runtime['run_id'],'wall_seconds':runtime['wall_seconds'],
          'simulated_seconds':runtime['simulated_seconds'],'trace_samples':len(runtime['trace']),
          'source_sha256':{str(p.relative_to(root)).replace('\\','/'):digest(p) for p in sorted(set(files))},
          'evidence_sha256':{str(p.relative_to(root)).replace('\\','/'):digest(p) for p in evidence},
          'module_sha256':digest(root/'cnc1/build/cnc1_sim.so'),
          'not_proven':['physical SPI transport','real-time target deadlines','FPGA synthesis/timing closure',
                        'electrical interfaces','physical closed-loop machine motion','spindle-synchronized machining']}
(directory/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
print(json.dumps({k:manifest[k] for k in ('compiled_checks','default_v1_checks','linuxcnc_checks','trace_samples','wall_seconds','simulated_seconds')}))
