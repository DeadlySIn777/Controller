"""Run bounded source-only continuity controls and freeze the test receipt."""
from hashlib import sha256
import io
import json
from pathlib import Path
import time
import unittest

HERE = Path(__file__).resolve().parent


class Result(unittest.TextTestResult):
    subtests = 0
    def addSubTest(self, test, subtest, err):
        self.subtests += 1
        super().addSubTest(test, subtest, err)


def main():
    files = [HERE / name for name in ('qualify_continuity.py', 'pin_live_inputs.py', 'live-inputs.json',
                                     'test_continuity.py', 'run_host_controls.py')]
    files += [HERE.parent / 'qualify_bundle.py']
    hashes = {str(path): sha256(path.read_bytes()).hexdigest() for path in files}
    output = io.StringIO()
    start = time.monotonic()
    result = unittest.TextTestRunner(stream=output, verbosity=2, resultclass=Result).run(
        unittest.defaultTestLoader.discover(str(HERE), pattern='test_continuity.py'))
    unchanged = hashes == {str(path): sha256(path.read_bytes()).hexdigest() for path in files}
    receipt = {'verdict': 'PASS' if result.wasSuccessful() and unchanged else 'FAIL',
               'tests': result.testsRun, 'subtests': result.subtests,
               'failures': len(result.failures), 'errors': len(result.errors), 'skips': len(result.skipped),
               'elapsed_seconds': round(time.monotonic() - start, 3), 'source_hashes': hashes,
               'source_hashes_unchanged': unchanged, 'native_jobs': 0, 'gpu_jobs': 0,
               'live_or_shared_edits': False, 'final_bundle_produced': False,
               'evidence_class': 'Host rejection-boundary controls with saved actual refilled r07/c05 partitions; no fresh native job'}
    for name in ('host-tests.log', 'host-receipt.json'):
        if (HERE / name).exists():
            raise ValueError('Existing host evidence is preserved')
    (HERE / 'host-tests.log').write_text(output.getvalue(), encoding='utf-8')
    (HERE / 'host-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(receipt))
    return 0 if receipt['verdict'] == 'PASS' else 1


if __name__ == '__main__':
    raise SystemExit(main())
