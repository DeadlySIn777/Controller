"""Host-only rejection controls; no native-open job, candidate selection or bundle."""
import hashlib
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
    sources = [HERE / name for name in ("open_check_shared.py", "probe_native_open.py", "run_native_open.py", "test_native_open.py", "run_host_controls.py")]
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in sources}
    log, started = io.StringIO(), time.time()
    result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=Result).run(unittest.defaultTestLoader.discover(str(HERE), pattern="test_native_open.py"))
    unchanged = all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == value for p, value in hashes.items())
    success = result.wasSuccessful() and unchanged
    receipt = {"verdict": "PASS" if success else "FAIL", "evidence_class": "host rejection fixtures only; not native-open evidence",
               "tests": result.testsRun, "subtests": result.subtests, "failures": len(result.failures), "errors": len(result.errors),
               "skips": len(result.skipped), "elapsed_seconds": round(time.time() - started, 3), "source_hashes": hashes,
               "source_hashes_unchanged": unchanged, "native_jobs": 0, "bundle_selected": False, "live_or_adopted_edits": False}
    (HERE / "host-tests.log").write_text(log.getvalue(), encoding="utf-8")
    (HERE / "host-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))
    return 0 if success else 1


if __name__ == "__main__":
    raise SystemExit(main())
