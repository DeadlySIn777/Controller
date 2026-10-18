"""Fresh, disconnected post-r0.4 host receipt; no source rebuild or interface use.

Prepare this runner before source freeze, execute only after root confirms the
frozen source revision. Previous final-host-validation evidence is immutable.
"""
from __future__ import annotations

import argparse
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
          'controller_lab', 'firmware', 'gateware', 'cnc1', 'config', 'hardware',
          'research')
TEXT_EXTENSIONS = {'.py', '.c', '.h', '.cpp', '.hpp', '.v', '.sv', '.json',
                   '.toml', '.yaml', '.yml', '.ini', '.cfg', '.md', '.txt',
                   '.csv', '.xml', '.ps1', '.sh', '.ys', '.hex', '.edif',
                   '.kicad_sch', '.kicad_sym', '.kicad_pcb', '.kicad_pro',
                   '.kicad_mod', '.defaults'}
SKIP_DIRS = {'__pycache__', '.git', 'node_modules', 'vendor-src', 'build',
             'build-default', 'build-uart', 'build-uart-check', 'dist'}
SPECIAL_NAMES = {'CMakeLists.txt', 'Kconfig.projbuild', 'sdkconfig',
                 'fp-lib-table', 'sym-lib-table', 'SHA256SUMS'}


def utc():
    return datetime.now(timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def inventory():
    result = {}
    for scope in SCOPES:
        for path in sorted((ROOT/scope).rglob('*')):
            if not path.is_file() or any(x in SKIP_DIRS for x in path.parts):
                continue
            included = path.suffix.lower() in TEXT_EXTENSIONS or path.name in SPECIAL_NAMES
            # Retained primary PDFs are engineering inputs. Compiled and binary
            # media outputs remain excluded; research vendor source is skipped.
            included = included or (scope == 'research' and path.suffix.lower() == '.pdf')
            if not included:
                continue
            result[path.relative_to(ROOT).as_posix()] = {
                'sha256':sha(path), 'bytes':path.stat().st_size}
    return result


def write(name, data):
    (OUT/name).write_text(json.dumps(data, indent=2)+'\n', encoding='utf-8')


def summarize(text, exit_code):
    normalized = text.replace('\r\n', '\n')
    summaries = re.findall(r'^Ran (\d+) tests? in ([\d.]+)s$', normalized, re.MULTILINE)
    skipped = re.findall(r'^(.+?) \.\.\. skipped (.+)$', normalized, re.MULTILINE)
    footer = re.findall(r'^OK(?: \(skipped=(\d+)\))?$', normalized, re.MULTILINE)
    failures = re.findall(r'^(?:FAIL|ERROR):.*$', normalized, re.MULTILINE)
    count, elapsed = summaries[-1] if summaries else (None, None)
    skip_count = int(footer[-1] or 0) if footer else None
    coherent = bool(count is not None and int(count) > 0 and footer and
                    skip_count == len(skipped) and not failures and exit_code == 0)
    return {'reported_tests':int(count) if count is not None else None,
            'passed_tests':int(count)-skip_count if coherent else None,
            'skipped_tests':skip_count,
            'unittest_elapsed_seconds':float(elapsed) if elapsed is not None else None,
            'skip_cases':[{'case':case, 'reason':reason} for case,reason in skipped],
            'failure_or_error_lines':failures, 'summary_coherent':coherent,
            'result_footer':normalized.splitlines()[-8:]}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--freeze-confirmed', required=True,
                        help='Parent-confirmed source freeze message/revision label; not permission to operate hardware')
    args = parser.parse_args()
    if (OUT/'receipt.json').exists() or (OUT/'source-before.json').exists():
        raise SystemExit('Refusing to overwrite a prior validation receipt.')
    started = utc()
    before = inventory()
    write('source-before.json', before)
    artifact_dir = OUT/'test-artifacts'
    artifact_dir.mkdir()
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'
    env['TEMP'] = str(artifact_dir)
    env['TMP'] = str(artifact_dir)
    patterns = [('footprint-envelopes','test_mc_footprint_envelopes.py'),
                ('motion-card','test_motion_card_integration.py'),
                ('full-suite',None)]
    runs = []
    for name,pattern in patterns:
        command = [str(PYTHON), '-X','utf8','-m','unittest','discover','-s','tests']
        if pattern:
            command += ['-p',pattern]
        command += ['-v']
        run_start, tick = utc(), time.monotonic()
        logpath = OUT/(name+'.log')
        print('Starting '+name, flush=True)
        with logpath.open('wb') as log:
            process = subprocess.run(command,cwd=ROOT,env=env,
                                     stdout=log,stderr=subprocess.STDOUT)
        data = logpath.read_bytes()
        result = summarize(data.decode('utf-8',errors='replace'),process.returncode)
        run = {'name':name,'command':command,'cwd':str(ROOT),
               'started_utc':run_start,'finished_utc':utc(),
               'elapsed_wall_seconds':time.monotonic()-tick,
               'exit_code':process.returncode,'log':logpath.name,
               'log_sha256':hashlib.sha256(data).hexdigest(),**result}
        runs.append(run)
        write('runs-in-progress.json',runs)
        print(name+' finished: '+str(process.returncode)+', reported '+str(run['reported_tests']),flush=True)
    after = inventory()
    write('source-after.json',after)
    changes = {key:{'before':before.get(key),'after':after.get(key)}
               for key in sorted(set(before)|set(after)) if before.get(key) != after.get(key)}
    passed = all(r['exit_code'] == 0 and r['summary_coherent'] for r in runs)
    receipt = {'schema_version':1,'started_utc':started,'finished_utc':utc(),
        'parent_confirmed_source_freeze':args.freeze_confirmed,
        'python':str(PYTHON),'runner_python_version':sys.version,
        'runner_sha256':sha(Path(__file__)),
        'evidence_class':'disconnected_host_unittest_and_source_hash_inventory',
        'manufacturing_ready':False,'physical_interfaces_used':False,
        'target_compilation_performed':False,'HDL_simulation_performed':False,
        'FPGA_vendor_fit_performed':False,'native_ERC_or_DRC_rerun':False,
        'physical_measurements_performed':False,'source_scope':list(SCOPES),
        'source_file_count_before':len(before),'source_file_count_after':len(after),
        'source_hashes_unchanged':not changes,'source_changes':changes,'runs':runs,
        'all_commands_passed':passed,'validated_same_source_snapshot':not changes,
        'write_paths':{'logs_and_receipts':str(OUT),'temporary_test_fixtures':str(artifact_dir),
            'python_bytecode':'disabled by PYTHONDONTWRITEBYTECODE=1',
            'engineering_source_edits_or_rebuilds_by_runner':'none'},
        'exclusions':{'file_extensions':'compiled/binary media and HTML/JS gallery presentation excluded; retained primary research PDFs included',
            'directories':sorted(SKIP_DIRS),
            'root_docs_and_reports':'excluded; concurrent documentation/accounting changes allowed',
            'focused_cases_are_included_in_full_suite':True,
            'historical_receipts':'final-host-validation and earlier evidence remain unchanged'}}
    write('receipt.json',receipt)
    print(json.dumps({'commands_passed':passed,'source_hashes_unchanged':not changes,
                      'source_files':len(before),'source_changes':len(changes),
                      'receipt':str(OUT/'receipt.json')},indent=2),flush=True)
    return 0 if passed and not changes else 1


if __name__ == '__main__':
    raise SystemExit(main())
