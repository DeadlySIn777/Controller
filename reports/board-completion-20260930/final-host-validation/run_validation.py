"""Independent host-test receipt; never edits or rebuilds engineering sources."""
from __future__ import annotations

from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys
import time

OUT = Path(__file__).resolve().parent
ROOT = OUT.parents[2]
PYTHON = Path('C:/Python314/python.exe')
SCOPES = ('tools', 'tests', 'controller_config', 'controller_backend',
          'controller_lab', 'firmware', 'gateware', 'cnc1', 'config', 'hardware')
TEXT_EXTENSIONS = {'.py', '.c', '.h', '.cpp', '.hpp', '.v', '.sv', '.json',
                   '.toml', '.yaml', '.yml', '.ini', '.cfg', '.md', '.txt',
                   '.csv', '.xml', '.ps1', '.sh', '.ys', '.hex', '.edif',
                   '.kicad_sch', '.kicad_sym', '.kicad_pcb', '.kicad_pro',
                   '.kicad_mod', '.defaults'}
SKIP_DIRS = {'__pycache__', '.git', 'node_modules', 'build', 'build-default',
             'build-uart', 'build-uart-check', 'dist'}
SPECIAL_NAMES = {'CMakeLists.txt', 'Kconfig.projbuild', 'sdkconfig',
                 'fp-lib-table', 'sym-lib-table', 'SHA256SUMS'}


def utc():
    return datetime.now(timezone.utc).isoformat()


def inventory():
    result = {}
    for scope in SCOPES:
        for path in sorted((ROOT / scope).rglob('*')):
            if not path.is_file() or any(x in SKIP_DIRS for x in path.parts):
                continue
            if path.suffix.lower() not in TEXT_EXTENSIONS and path.name not in SPECIAL_NAMES:
                continue
            # UI/gallery HTML/JS are deliberately outside engineering source scope.
            result[path.relative_to(ROOT).as_posix()] = {
                'sha256': hashlib.sha256(path.read_bytes()).hexdigest(),
                'bytes': path.stat().st_size,
            }
    return result


def write(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    if (OUT / 'receipt.json').exists() or (OUT / 'source-before.json').exists():
        raise SystemExit('Refusing to overwrite a prior validation receipt.')
    started = utc()
    before = inventory()
    write('source-before.json', before)
    artifact_dir = OUT / 'test-artifacts'
    artifact_dir.mkdir()
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['TEMP'] = str(artifact_dir)
    env['TMP'] = str(artifact_dir)
    commands = [
        ('motion-card', [str(PYTHON), '-X', 'utf8', '-m', 'unittest', 'discover',
                         '-s', 'tests', '-p', 'test_motion_card_integration.py', '-v']),
        ('full-suite', [str(PYTHON), '-X', 'utf8', '-m', 'unittest', 'discover',
                        '-s', 'tests', '-v']),
    ]
    runs = []
    for name, command in commands:
        run_start, tick = utc(), time.monotonic()
        logpath = OUT / (name + '.log')
        print('Starting ' + name, flush=True)
        with logpath.open('wb') as log:
            process = subprocess.run(command, cwd=ROOT, env=env,
                                     stdout=log, stderr=subprocess.STDOUT)
        data = logpath.read_bytes()
        text = data.decode('utf-8', errors='replace').replace('\r\n', '\n')
        summaries = re.findall(r'^Ran (\d+) tests? in ([\d.]+)s$', text, re.MULTILINE)
        run = {'name': name, 'command': command, 'cwd': str(ROOT),
               'started_utc': run_start, 'finished_utc': utc(),
               'elapsed_wall_seconds': time.monotonic() - tick,
               'exit_code': process.returncode, 'log': logpath.name,
               'log_sha256': hashlib.sha256(data).hexdigest(),
               'unittest_summary': summaries[-1] if summaries else None,
               'failure_or_error_lines': re.findall(r'^(?:FAIL|ERROR):.*$', text, re.MULTILINE),
               'result_footer': text.splitlines()[-8:]}
        runs.append(run)
        write('runs-in-progress.json', runs)
        print(name + ' finished: ' + str(process.returncode) + ', summary ' + str(run['unittest_summary']), flush=True)
    after = inventory()
    write('source-after.json', after)
    changes = {k: {'before': before.get(k), 'after': after.get(k)}
               for k in sorted(set(before) | set(after)) if before.get(k) != after.get(k)}
    receipt = {
        'schema_version': 1, 'started_utc': started, 'finished_utc': utc(),
        'python': str(PYTHON), 'python_version': sys.version,
        'evidence_class': 'disconnected_host_unittest_and_source_hash_inventory',
        'manufacturing_ready': False, 'physical_interfaces_used': False,
        'target_compilation_performed': False, 'HDL_simulation_performed': False,
        'FPGA_vendor_fit_performed': False, 'native_ERC_or_DRC_rerun': False,
        'physical_measurements_performed': False,
        'source_scope': list(SCOPES), 'source_file_count_before': len(before),
        'source_file_count_after': len(after), 'source_hashes_unchanged': not changes,
        'source_changes': changes, 'runs': runs,
        'all_commands_passed': all(r['exit_code'] == 0 for r in runs),
        'validated_same_source_snapshot': not changes,
        'write_paths': {
            'logs_and_receipts': str(OUT),
            'temporary_test_fixtures': str(artifact_dir),
            'python_bytecode': 'disabled by PYTHONDONTWRITEBYTECODE=1',
            'engineering_source_edits_or_rebuilds_by_runner': 'none',
        },
        'exclusions': {
            'file_extensions': 'binary media/compiled artifacts and HTML/JS gallery presentation excluded',
            'directories': sorted(SKIP_DIRS),
            'root_docs_and_reports': 'excluded: concurrent documentation/accounting changes allowed',
            'historical_test_count': 'Existing 714-test history is retained elsewhere; this receipt uses only fresh unittest summaries.',
        },
    }
    write('receipt.json', receipt)
    print(json.dumps({'commands_passed': receipt['all_commands_passed'],
                      'source_hashes_unchanged': not changes,
                      'source_files': len(before), 'source_changes': len(changes),
                      'receipt': str(OUT / 'receipt.json')}, indent=2), flush=True)
    return 0 if receipt['all_commands_passed'] and not changes else 1


if __name__ == '__main__':
    raise SystemExit(main())
