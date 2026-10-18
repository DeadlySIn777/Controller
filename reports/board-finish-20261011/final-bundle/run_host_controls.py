"""Frozen host-control receipt; no KiCad/GPU/native jobs."""
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
    hashes = {str(p): hashlib.sha256(p.read_bytes()).hexdigest() for p in [HERE / "qualify_bundle.py", HERE / "symbol_resources.py", HERE / "test_bundle.py", Path(__file__)]}
    log = io.StringIO()
    start = time.time()
    result = unittest.TextTestRunner(stream=log, verbosity=2, resultclass=Result).run(unittest.defaultTestLoader.discover(str(HERE), pattern="test_bundle.py"))
    after = {p: hashlib.sha256(Path(p).read_bytes()).hexdigest() for p in hashes}
    ok = result.wasSuccessful() and hashes == after
    receipt = {"verdict": "PASS" if ok else "FAIL", "evidence_class": "host rejection-boundary controls; no native job",
               "tests": result.testsRun, "subtests": result.subtests, "failures": len(result.failures),
               "errors": len(result.errors), "skips": len(result.skipped), "elapsed_seconds": round(time.time() - start, 3),
               "checker_source_hashes": hashes, "source_hashes_unchanged": hashes == after,
               "native_jobs": 0, "live_or_adopted_edits": False, "final_bundle_produced": False}
    (HERE / "host-tests.log").write_text(log.getvalue(), encoding="utf-8")
    (HERE / "host-receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
