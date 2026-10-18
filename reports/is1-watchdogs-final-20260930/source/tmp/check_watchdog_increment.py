"""Freeze the new standalone block, re-export it privately and test copied inputs."""
import argparse
import datetime
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tools.hardware_export_evidence import canonical_netlist, canonical_erc

parser = argparse.ArgumentParser()
parser.add_argument('--evidence-dir', type=Path, default=Path('reports/is1-watchdogs-20260930'))
args = parser.parse_args()
dest = (ROOT/args.evidence_dir).resolve()
if dest.exists():
    raise SystemExit('Refusing to overwrite an existing evidence snapshot')
names = ['tools/hardware_build_is1_watchdogs.py', 'tools/hardware_validate_is1_watchdogs.py',
         'tools/hardware_build_tx_schematic.py', 'tools/hardware_build_logic_power.py',
         'tools/hardware_export_evidence.py', 'tools/is1_watchdog_analysis.py',
         'tests/test_is1_watchdogs.py', 'tests/test_is1_watchdog_analysis.py',
         'tmp/check_watchdog_increment.py']
for folder in ('hardware/is1_watchdogs', 'research/is1-watchdogs'):
    names += [p.relative_to(ROOT).as_posix() for p in (ROOT/folder).rglob('*')
              if p.is_file() and p.suffix not in ('.kicad_prl', '.pdf') and
              '__pycache__' not in p.parts]
def hash_file(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()
before = {name: hash_file(ROOT/name) for name in sorted(set(names))}
for name in before:
    target = dest/'source'/name
    target.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(ROOT/name, target)
# KiCad operates only on a distinct private native workspace, not retained inputs.
work = dest/'native-workspace'
shutil.copytree(dest/'source/hardware/is1_watchdogs', work/'hardware/is1_watchdogs')
native = work/'hardware/is1_watchdogs'
cli = 'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'
commands = [
    [cli, 'sch', 'export', 'netlist', '--format', 'kicadxml', '--output', str(native/'netlist.xml'), str(native/'is1_watchdogs.kicad_sch')],
    [cli, 'sch', 'erc', '--format', 'json', '--severity-all', '--output', str(native/'erc.json'), str(native/'is1_watchdogs.kicad_sch')],
]
runs = []
for command in commands:
    p = subprocess.run(command, cwd=native, capture_output=True, text=True, encoding='utf-8', timeout=60)
    runs.append({'argv': command, 'returncode': p.returncode, 'stdout': p.stdout, 'stderr': p.stderr})
stored = dest/'source/hardware/is1_watchdogs'
native_matches = {
    'netlist': canonical_netlist((stored/'netlist.xml').read_bytes()) == canonical_netlist((native/'netlist.xml').read_bytes()),
    'erc': canonical_erc((stored/'erc.json').read_bytes()) == canonical_erc((native/'erc.json').read_bytes()),
}
runner = '''import json, pathlib, unittest
suite=unittest.TestSuite()
loader=unittest.TestLoader()
for name in ('test_is1_watchdogs.py','test_is1_watchdog_analysis.py'):
    cases=loader.discover('tests',pattern=name)
    if cases.countTestCases()==0: raise RuntimeError('No tests: '+name)
    suite.addTests(cases)
r=unittest.TextTestRunner(verbosity=2).run(suite)
pathlib.Path('test-result.json').write_text(json.dumps(dict(tests_run=r.testsRun,failures=len(r.failures),errors=len(r.errors),skipped=len(r.skipped),successful=r.wasSuccessful())))
raise SystemExit(0 if r.wasSuccessful() else 1)
'''
p = subprocess.run([sys.executable, '-X', 'utf8', '-c', runner], cwd=dest/'source', capture_output=True,
                   text=True, encoding='utf-8', timeout=60)
(dest/'tests.txt').write_text(p.stdout+p.stderr, encoding='utf-8')
test_result = json.loads((dest/'source/test-result.json').read_text())
after = {name: hash_file(ROOT/name) for name in before}
copied = {name: hash_file(dest/'source'/name) for name in before}
changed = [name for name in before if before[name] != after[name] or before[name] != copied[name]]
erc = json.loads((native/'erc.json').read_text())
violations = [v for s in erc['sheets'] for v in s['violations']]
okay = not changed and all(native_matches.values()) and all(r['returncode']==0 for r in runs) and p.returncode==0 and test_result['successful'] and not test_result['skipped'] and not violations
receipt = {'schema_version': 1, 'captured_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
           'scope': 'Standalone IS-1 timer frontends and numerical screens; not permission integration',
           'checks_pass': okay, 'manufacturing_ready': False, 'assembly_integrated': False,
           'startup_defaults_qualified': False, 'physical_timing_qualified': False,
           'source_count': len(before), 'input_sha256': before, 'copied_sha256': copied,
           'after_sha256': after, 'changed_during_run': changed,
           'native_exports_match': native_matches, 'native_runs': runs,
           'native_erc_violation_count': len(violations), 'tests': test_result,
           'known_integration_blockers': ['T20 weak pull-up defeats 100k input pulldown in configuration',
              'direct SET1 LOW requires qualified FPGA logic standard/conditioning',
              'complete arm/interruption/default circuit and selftest not integrated',
              'SET1 setup table has nominal value only', 'physical leakage/parasitics/propagation unmeasured']}
(dest/'review.json').write_text(json.dumps(receipt, indent=2)+'\n', encoding='utf-8')
print(json.dumps({k: v for k,v in receipt.items() if 'sha256' not in k and k != 'native_runs'}, indent=2))
raise SystemExit(0 if okay else 1)
