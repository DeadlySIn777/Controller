"""Record successful existing outputs and exact sources; does not run tests.

--check verifies the saved manifest against the current source, evidence and
module bytes (hashing bytes exactly as they are on disk) and exits non-zero on
any difference; it never rewrites the manifest.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

root=Path(__file__).resolve().parents[2]
directory=root/'cnc1/evidence'
# Expected complete-run counts. They are raised only together with the tests
# that produce them; lowering them to accept a shorter run is not permitted.
COMPILED_MINIMUM=220
V1_CHECKS=252
V2_CHECKS=27
LINUXCNC_CHECKS=27
PERSISTENT_CHECKS=68
RUNTIME_HOST_TESTS=41
PERSISTENT_HOST_TESTS=33
SOURCE_PATTERNS=('cnc1/src/cnc1.*','cnc1/src/hal_cnc1.c','cnc1/src/sim_transport.cpp',
                 'cnc1/tests/test_driver.c','cnc1/tools/build.sh','cnc1/tools/run_linuxcnc.sh',
                 'cnc1/tools/run_persistent.sh','cnc1/tools/record_evidence.py',
                 'cnc1/tools/run_gateware_regression.sh','cnc1/tools/run_host_tests.py','cnc1/profiles/sim/*','controller_config/*.py',
                 'tests/test_runtime_configuration.py','tests/test_persistent_runtime.py','cnc1/*.py','cnc1/*.md',
                 'gateware/rtl/*.v','reports/CNC1_INTEGRATION.md','reports/RUNTIME_CONFIGURATION.md','reports/PERSISTENT_RUNTIME.md')


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def relative(path): return str(path.relative_to(root)).replace('\\','/')


def check_manifest():
    manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    problems=[]
    for section in ('source_sha256','evidence_sha256'):
        for name,expected in manifest[section].items():
            path=root/name
            if not path.is_file(): problems.append(f'{section}: missing {name}')
            elif digest(path)!=expected: problems.append(f'{section}: changed {name}')
    current={relative(p) for pattern in SOURCE_PATTERNS for p in root.glob(pattern) if p.is_file() and '.var' not in p.name}
    for name in sorted(current-set(manifest['source_sha256'])): problems.append(f'source_sha256: unrecorded {name}')
    module=root/'cnc1/build/cnc1_sim.so'
    if not module.is_file(): problems.append('module: cnc1/build/cnc1_sim.so absent (ignored build output)')
    elif digest(module)!=manifest['module_sha256']: problems.append('module: cnc1/build/cnc1_sim.so differs')
    for problem in problems: print(problem)
    print(json.dumps({'manifest_recorded_utc':manifest['recorded_utc'],'problems':len(problems)}))
    return 1 if problems else 0


def record():
    compiled=(directory/'compiled-rtl-tests.log').read_text()
    count=re.search(r'CNC1_COMPILED_RTL_CHECKS=(\d+)',compiled)
    if not count or int(count[1])<COMPILED_MINIMUM or 'FAIL ' in compiled:
        raise SystemExit('No complete passing compiled integration record')
    baseline=(directory/'baseline-regression.log').read_text()
    if ('sources unchanged during the run; exit 0' not in baseline or f'ALL {V1_CHECKS} CHECKS PASSED' not in baseline or f'ALL {V2_CHECKS} V2 CHECKS PASSED' not in baseline or
            'Python independently decoded RTL status' not in baseline or 'Verilator strict lint passed' not in baseline):
        raise SystemExit('Missing default-v1/ABI-v2 regression evidence')
    runtime=json.loads((directory/'linuxcnc.json').read_text())
    if not runtime['success'] or len(runtime['checks'])!=LINUXCNC_CHECKS or not all(c['passed'] for c in runtime['checks']):
        raise SystemExit('Real LinuxCNC integration evidence is incomplete')
    persistent_dir=directory/'persistent'
    persistent=json.loads((persistent_dir/'summary.json').read_text())
    if not persistent['success'] or persistent['separate_linuxcnc_launches']!=9 or persistent['checks']!=PERSISTENT_CHECKS:
        raise SystemExit('Persistent restart evidence is incomplete')
    for scenario in persistent['scenarios']:
        result=json.loads((persistent_dir/(scenario['scenario']+'.json')).read_text())
        if not result['success'] or result['run_id']!=persistent['run_id'] or len(result['checks'])!=scenario['checks'] or not all(c['passed'] for c in result['checks']):
            raise SystemExit('Persistent scenario has stale/incomplete evidence')
    for name,expected in (('runtime-service-tests.log',RUNTIME_HOST_TESTS),('persistent/host-policy-tests.log',PERSISTENT_HOST_TESTS)):
        log=(directory/name).read_text()
        if f'Ran {expected} tests' not in log or '\nOK' not in log or 'FAILED' in log:
            raise SystemExit('Host policy evidence is incomplete: '+name)
    files=[]
    for pattern in SOURCE_PATTERNS:
        files.extend(p for p in root.glob(pattern) if p.is_file() and '.var' not in p.name)
    evidence=[directory/name for name in ('compiled-rtl-tests.log','baseline-regression.log','linuxcnc.json','linuxcnc.log','build-packages.tsv','runtime-service-tests.log')]
    evidence.extend(p for p in sorted(persistent_dir.iterdir()) if p.is_file() and p.suffix in ('.json','.log'))
    manifest={'recorded_utc':datetime.now(timezone.utc).isoformat(),
              'scope':'compiled common/HAL driver + durable scale authority/startup inhibit + separate explicit volatile regression + actual RTL simulation; physical transport and synthesis have separate evidence',
              'compiled_checks':int(count[1]),'default_v1_checks':V1_CHECKS,'abi_v2_rtl_checks':V2_CHECKS,
              'default_v1_evidence':'gateware/tools/run_tests.sh rerun by cnc1/tools/run_gateware_regression.sh on a byte-identical scratch copy of the current gateware/rtl, tests and tools (Icarus HDL simulation, Python status decode, -g2005 elaboration, Verilator lint); HDL simulation only',
              'runtime_service_host_tests':RUNTIME_HOST_TESTS,'persistent_policy_host_tests':PERSISTENT_HOST_TESTS,'linuxcnc_checks':len(runtime['checks']),
              'persistent_checks':persistent['checks'],'persistent_launches':persistent['separate_linuxcnc_launches'],
              'persistent_run_id':persistent['run_id'],'persistent_profile_sha256':persistent['profile_sha256'],
              'runtime_run_id':runtime['run_id'],'wall_seconds':runtime['wall_seconds'],
              'simulated_seconds':runtime['simulated_seconds'],'trace_samples':len(runtime['trace']),
              'source_sha256':{relative(p):digest(p) for p in sorted(set(files))},
              'evidence_sha256':{relative(p):digest(p) for p in evidence},
              'module_sha256':digest(root/'cnc1/build/cnc1_sim.so'),
              'not_proven':['physical SPI transport','real-time target deadlines','production FPGA synthesis/routed timing closure',
                            'electrical interfaces','physical closed-loop machine motion','spindle-synchronized machining']}
    (directory/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
    print(json.dumps({k:manifest[k] for k in ('compiled_checks','default_v1_checks','abi_v2_rtl_checks','linuxcnc_checks','persistent_checks','trace_samples','wall_seconds','simulated_seconds')}))
    return 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='verify the saved manifest; do not record')
    sys.exit(check_manifest() if parser.parse_args().check else record())
