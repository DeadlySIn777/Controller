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
if not count or int(count[1])<192 or 'FAIL ' in compiled:
    raise SystemExit('No complete passing compiled integration record')
baseline=(directory/'baseline-regression.log').read_text()
if 'ALL 180 CHECKS PASSED' not in baseline or 'Python independently decoded RTL status' not in baseline:
    raise SystemExit('Missing default-v1 regression evidence')
runtime=json.loads((directory/'linuxcnc.json').read_text())
if not runtime['success'] or len(runtime['checks'])!=26 or not all(c['passed'] for c in runtime['checks']):
    raise SystemExit('Real LinuxCNC integration evidence is incomplete')
persistent_dir=directory/'persistent'
persistent=json.loads((persistent_dir/'summary.json').read_text())
if not persistent['success'] or persistent['separate_linuxcnc_launches']!=9 or persistent['checks']!=59:
    raise SystemExit('Persistent restart evidence is incomplete')
for scenario in persistent['scenarios']:
    result=json.loads((persistent_dir/(scenario['scenario']+'.json')).read_text())
    if not result['success'] or result['run_id']!=persistent['run_id'] or len(result['checks'])!=scenario['checks'] or not all(c['passed'] for c in result['checks']):
        raise SystemExit('Persistent scenario has stale/incomplete evidence')
for name,expected in (('runtime-service-tests.log',25),('persistent/host-policy-tests.log',26)):
    log=(directory/name).read_text()
    if f'Ran {expected} tests' not in log or '\nOK' not in log or 'FAILED' in log:
        raise SystemExit('Host policy evidence is incomplete: '+name)
def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()
files=[]
for pattern in ('cnc1/src/cnc1.*','cnc1/src/hal_cnc1.c','cnc1/src/sim_transport.cpp',
                'cnc1/tests/test_driver.c','cnc1/tools/build.sh','cnc1/tools/run_linuxcnc.sh',
                'cnc1/tools/run_persistent.sh','cnc1/tools/record_evidence.py','cnc1/profiles/sim/*','controller_config/*.py',
                'tests/test_runtime_configuration.py','tests/test_persistent_runtime.py','cnc1/*.py','cnc1/*.md',
                'gateware/rtl/*.v','reports/CNC1_INTEGRATION.md','reports/RUNTIME_CONFIGURATION.md','reports/PERSISTENT_RUNTIME.md'):
    files.extend(p for p in root.glob(pattern) if p.is_file() and '.var' not in p.name)
evidence=[directory/name for name in ('compiled-rtl-tests.log','baseline-regression.log','linuxcnc.json','linuxcnc.log','build-packages.tsv','runtime-service-tests.log')]
evidence.extend(p for p in persistent_dir.iterdir() if p.is_file() and p.suffix in ('.json','.log'))
manifest={'recorded_utc':datetime.now(timezone.utc).isoformat(),
          'scope':'compiled common/HAL driver + durable scale authority/startup inhibit + separate explicit volatile regression + actual RTL simulation; physical transport and synthesis have separate evidence',
          'compiled_checks':int(count[1]),'default_v1_checks':180,'default_v1_evidence':'retained unchanged RTL regression; not rerun for host-only runtime configuration',
          'runtime_service_host_tests':25,'persistent_policy_host_tests':26,'linuxcnc_checks':len(runtime['checks']),
          'persistent_checks':persistent['checks'],'persistent_launches':persistent['separate_linuxcnc_launches'],
          'persistent_run_id':persistent['run_id'],'persistent_profile_sha256':persistent['profile_sha256'],
          'runtime_run_id':runtime['run_id'],'wall_seconds':runtime['wall_seconds'],
          'simulated_seconds':runtime['simulated_seconds'],'trace_samples':len(runtime['trace']),
          'source_sha256':{str(p.relative_to(root)).replace('\\','/'):digest(p) for p in sorted(set(files))},
          'evidence_sha256':{str(p.relative_to(root)).replace('\\','/'):digest(p) for p in evidence},
          'module_sha256':digest(root/'cnc1/build/cnc1_sim.so'),
          'not_proven':['physical SPI transport','real-time target deadlines','production FPGA synthesis/routed timing closure',
                        'electrical interfaces','physical closed-loop machine motion','spindle-synchronized machining']}
(directory/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
print(json.dumps({k:manifest[k] for k in ('compiled_checks','default_v1_checks','linuxcnc_checks','trace_samples','wall_seconds','simulated_seconds')}))
