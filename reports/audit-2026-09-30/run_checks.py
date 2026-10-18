"""Read-only source audit and disconnected host tests; writes only this audit folder."""
from pathlib import Path
import hashlib
import json
import subprocess
import sys
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
DIRECTORIES = ('cnc1', 'controller_backend', 'controller_config', 'controller_lab',
               'docs', 'examples', 'firmware', 'gateware', 'hardware', 'research', 'tests', 'tools', 'manufacturing')
EXCLUDED = {'__pycache__', '.git', 'node_modules', 'build', 'attempts', 'results', '.venv', 'venv'}

def inventory():
    paths = list(ROOT.glob('*.md'))
    for name in DIRECTORIES:
        paths.extend(p for p in (ROOT / name).rglob('*') if p.is_file() and not EXCLUDED.intersection(p.relative_to(ROOT).parts)
                     and not p.name.endswith(('.lck', '.bak', '.kicad_prl')))
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(set(paths))}

def save(name, data):
    (HERE / name).write_text(json.dumps(data, indent=2, ensure_ascii=False) + '\n', encoding='utf-8')

def run(name, argv, timeout=240):
    start = time.monotonic()
    result = subprocess.run(argv, cwd=ROOT, capture_output=True, text=True, encoding='utf-8', errors='replace', timeout=timeout)
    (HERE / (name + '.txt')).write_text(result.stdout + result.stderr, encoding='utf-8')
    return {'name': name, 'argv': argv, 'exit_code': result.returncode, 'elapsed_s': round(time.monotonic()-start, 3), 'log': name + '.txt'}

before = inventory()
save('source-before.json', before)
runner = '''import json,sys,unittest
from pathlib import Path
suite=unittest.defaultTestLoader.discover("tests")
result=unittest.TextTestRunner(verbosity=2).run(suite)
Path(sys.argv[1]).write_text(json.dumps({"tests_run":result.testsRun,"failures":len(result.failures),"errors":len(result.errors),"skipped":len(result.skipped),"checks_pass":result.wasSuccessful()},indent=2)+"\\n",encoding="utf-8")
sys.exit(0 if result.wasSuccessful() else 1)
'''
checks = [run('python-tests', [sys.executable, '-c', runner, str(HERE/'python-result.json')])]
for script in ('build_compute_display_matrix.py', 'build_feature_catalog.py', 'build_hardware_cost_data.py'):
    checks.append(run(script[:-3], [sys.executable, 'tools/'+script, '--check']))
native = run('native-exports-run', [sys.executable, 'tools/hardware_export_evidence.py', '--source-root', str(ROOT), '--output-dir', str(HERE/'native-exports')], timeout=240)
checks.append(native)
after = inventory()
save('source-after.json', after)
changed = sorted(k for k in before.keys() | after.keys() if before.get(k)!=after.get(k))
archive = ROOT/'reports/processor-hardware-20260929'
review = json.loads((archive/'review.json').read_text(encoding='utf-8'))
declared = review['input_sha256']
archive_bad = [name for name, value in declared.items() if not (archive/'source'/name).is_file() or hashlib.sha256((archive/'source'/name).read_bytes()).hexdigest()!=value]
working_bad = [name for name, value in declared.items() if not (ROOT/name).is_file() or hashlib.sha256((ROOT/name).read_bytes()).hexdigest()!=value]
save('check-results.json', {'schema_version':1, 'date':'2026-09-30', 'scope':'Disconnected host checks and fresh native circuit exports; no physical target execution or manufacturing approval',
     'checks':checks, 'source_file_count':len(before), 'changed_during_checks':changed,
     'frozen_archive':{'path':str(archive.relative_to(ROOT)), 'declared_files':len(declared), 'copy_mismatches':archive_bad, 'working_tree_mismatches':working_bad},
     'manufacturing_ready':False})
print(json.dumps({'checks':[(c['name'],c['exit_code']) for c in checks], 'files':len(before), 'changed_during_checks':changed, 'archive_copy_mismatches':archive_bad, 'archive_working_mismatches':working_bad}, indent=2))
