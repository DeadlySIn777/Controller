"""Record the spidev laboratory-backend evidence produced by test_spidev.sh.

Run test_spidev.sh first with its output captured, for example
  sh cnc1/tools/test_spidev.sh > cnc1/evidence/spidev/tests.log 2>&1
This recorder runs no tests and opens no device. It validates the captured log,
then hashes the sources, the compiled-header copy, the logs and the test
binaries that test_spidev.sh preserved. --check verifies the saved manifest.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

root=Path(__file__).resolve().parents[2]
directory=root/'cnc1/evidence/spidev'
PRIOR_ARCHIVES=('cnc1/evidence/spidev/before-audit-fixes-2026-09-28',  # pre-audit-fix record
                'cnc1/evidence/spidev/before-audit-repair-2026-09-28')  # first audit-fix record, superseded
SOURCES=('cnc1/src/spidev_transport.h','cnc1/src/spidev_transport.c','cnc1/tests/test_spidev.c',
         'cnc1/tests/test_spidev_cpp.cpp','cnc1/tools/test_spidev.sh','cnc1/tools/record_spidev_evidence.py',
         'reports/SPI_TRANSPORT_IMPLEMENTATION.md','cnc1/src/cnc1.h')
EVIDENCE=('tests.log','build-packages.tsv','build-cnc1.h','initial-sanitizer-environment.log',
          'intermediate-header-regression.log','before-persistent-header/archive-index.json')
BINARIES=('test_spidev','test_spidev_sanitized','test_spidev_cpp','spidev_transport.o')


def digest(path): return hashlib.sha256(path.read_bytes()).hexdigest()


def check_manifest():
    manifest=json.loads((directory/'manifest.json').read_text(encoding='utf-8'))
    problems=[]
    for section in ('source_sha256','evidence_sha256','binary_sha256'):
        for name,expected in manifest[section].items():
            path=root/name
            if not path.is_file(): problems.append(f'{section}: missing {name}')
            elif digest(path)!=expected: problems.append(f'{section}: changed {name}')
    if digest(root/'cnc1/src/cnc1.h')!=manifest['compiled_common_header']['sha256']:
        problems.append('compiled_common_header: cnc1/src/cnc1.h differs from the compiled copy')
    for problem in problems: print(problem)
    print(json.dumps({'manifest_recorded_utc':manifest['recorded_utc'],'problems':len(problems)}))
    return 1 if problems else 0


def record():
    log=(directory/'tests.log').read_text(encoding='utf-8')
    counts=[int(value) for value in re.findall(r'^PASS (\d+) assertions; all device operations mocked; no physical SPI opened$',log,re.M)]
    if len(counts)!=2 or counts[0]!=counts[1] or 'FAIL' in log or 'ERROR' in log or \
            'PASS C++ public header links to actual C object; no device opened' not in log:
        raise SystemExit('No complete passing normal + ASan/UBSan + C++ linkage record in tests.log')
    header=directory/'build-cnc1.h'
    matches=digest(header)==digest(root/'cnc1/src/cnc1.h')
    if not matches:
        raise SystemExit('Compiled header copy differs from cnc1/src/cnc1.h; rerun test_spidev.sh')
    rel=lambda path: str(path.relative_to(root)).replace('\\','/')
    manifest={
        'date':datetime.now(timezone.utc).date().isoformat(),
        'scope':'Linux spidev laboratory backend, all successful device operations mocked; no physical measurements',
        'checks':{'normal_assertions':counts[0],'asan_ubsan_assertions':counts[1],
                  'cpp_header_c_object_link':'passed','physical_device_opens':0},
        'source_sha256':{name:digest(root/name) for name in SOURCES},
        'compiled_common_header':{'path':rel(header),'sha256':digest(header),'current_common_header_matches':matches,
                                  'current_common_header_sha256':digest(root/'cnc1/src/cnc1.h'),
                                  'note':'Copied by test_spidev.sh from the isolated rootfs work/spidev-lab/src/cnc1.h after the successful normal+ASan/UBSan+C++ link run.'},
        'evidence_sha256':{rel(directory/name):digest(directory/name) for name in EVIDENCE if (directory/name).is_file()},
        'binary_sha256':{rel(directory/'binaries'/name):digest(directory/'binaries'/name) for name in BINARIES},
        'limitations':['Synchronous ioctl has no enforced completion deadline.',
                       'Advisory flock is cooperative ownership, not system-wide exclusion.',
                       'No default HAL profile loads this backend.',
                       'No target electrical, timing, device-tree or machine qualification.'],
        'initial_failure':'Sanitizer initially could not inspect /proc in isolated rootfs. Launcher corrected by mounting proc in private namespaces. The retained initial-sanitizer-environment.log was produced from an earlier revision of cnc1/tests/test_spidev.c (840 assertions, all passed before LeakSanitizer aborted); it does not correspond to the test_spidev.c hash in source_sha256 and is kept only as the failed-environment record.',
        'recorded_utc':datetime.now(timezone.utc).isoformat(),
        'regression':'Rerun from a clean rootfs work copy against the current common header (driver fields for the persistence stage revision and watchdog-derived limits, with the repair-round comment correction on what the persistence precondition guarantees); spidev transport/test sources unchanged',
        'prior_runs':[{'archive':name,'prior_manifest_sha256':digest(root/name/'manifest.json') if (root/name/'manifest.json').is_file() else None}
                      for name in PRIOR_ARCHIVES],
        'intermediate_regression':'intermediate-header-regression.log preserves an earlier successful header refresh (historical, before-persistent-header milestone).'}
    (directory/'manifest.json').write_bytes((json.dumps(manifest,indent=2)+'\n').encode())
    print(json.dumps({'checks':manifest['checks'],'header_matches':matches}))
    return 0


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check',action='store_true',help='verify the saved manifest; do not record')
    sys.exit(check_manifest() if parser.parse_args().check else record())
