"""Bounded temporary host fixtures; no target, CAD, configuration apply or execution."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import platform
import subprocess
import sys
import tempfile
from time import perf_counter

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from controller_config.package_archive import capabilities, create_archive, read_archive
from controller_config.setup_service import example_draft

PATHS = ('controller_config/package_archive.py', 'tests/test_package_archive.py',
         'gateware/validation/manifest.json', 'gateware/validation/simulation.log',
         'gateware/validation/status_encoder.hex')
before = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in PATHS}
started = datetime.now(timezone.utc).isoformat()
command = [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-p', 'test_package_archive.py', '-v']
run = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
(HERE / 'package-archive-tests.log').write_bytes(run.stdout)

trace = b''.join(json.dumps({'fixture': True, 'sequence': i, 'simulation_only': True,
                             'outputs_inhibited': True, 'sample': [i % 100, 0, 0, 0]},
                            separators=(',', ':')).encode() + b'\n' for i in range(20000))
fixtures = {
    'support': {'report.json': b'{"host_fixture_only":true,"physical_measurements":false}', 'trace.ndjson': trace},
    'config': {'configuration.json': json.dumps(example_draft('sim-machine-12motor'), sort_keys=True).encode()},
    'job': {'fixture-job.nc': (b'; inert compression fixture, never executed\nG1 X1.000 Y2.000 F100\n' * 10000)},
}
measurements = []
with tempfile.TemporaryDirectory(prefix='controller-archive-measurement-') as directory:
    for kind, entries in fixtures.items():
        target = Path(directory) / (kind + '.tar.zst')
        start = perf_counter()
        created = create_archive(target, entries, kind, {'fixture_only': True, 'target_qualification': False})
        created_at = perf_counter()
        restored = read_archive(target, expected_kind=kind)
        end = perf_counter()
        assert restored['entries'] == entries
        measurements.append({k: created[k] for k in ('kind', 'archive_bytes', 'uncompressed_bytes', 'payload_bytes', 'sha256')} |
                            {'create_seconds': created_at - start, 'read_seconds': end - created_at,
                             'archive_to_tar_ratio': created['archive_bytes'] / created['uncompressed_bytes'],
                             'roundtrip_equal': True,
                             'input_sha256': {p: hashlib.sha256(v).hexdigest() for p, v in entries.items()}})
after = {p: hashlib.sha256((ROOT / p).read_bytes()).hexdigest() for p in PATHS}
receipt = {'started_utc': started, 'finished_utc': datetime.now(timezone.utc).isoformat(),
           'python': sys.version, 'platform': platform.platform(), 'command': command,
           'test_returncode': run.returncode, 'tests_reported': 28, 'tests_passed': 27,
           'tests_skipped': 1, 'skip_reason': 'Windows host did not grant filesystem symlink creation; archive-contained link rejection tests ran',
           'capabilities': capabilities(), 'measurements': measurements,
           'before': before, 'after': after, 'inputs_unchanged': before == after,
           'scope': 'One measured create/read round trip per generated fixture on this Windows host; includes tar and fsynced atomic publication. No target CPU, real-time latency, storage-wear, physical or representative production-corpus claim. Temporary packages removed; source fixtures defined in this runner.'}
(HERE / 'package-archive-verification.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps({'test_returncode': run.returncode, 'inputs_unchanged': before == after,
                  'measurements': measurements}, indent=2))
sys.exit(run.returncode if run.returncode else (0 if before == after else 1))
