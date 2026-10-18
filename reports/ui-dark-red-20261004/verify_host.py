"""Relevant offline HTTP/setup regressions; never connect to physical equipment."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import unittest

REPORT = Path(__file__).resolve().parent
ROOT = REPORT.parents[1]
sys.path.insert(0, str(ROOT))
PATTERNS = ["test_setup_web.py", "test_diagnostic_service.py"]


def main():
    def hashes():
        paths = list((ROOT / "controller_config").rglob("*.py"))
        paths += list((ROOT / "controller_config/web").glob("*"))
        paths += [ROOT / "tests" / pattern for pattern in PATTERNS]
        return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in paths if p.is_file()}
    before = hashes()
    suite = unittest.TestSuite(unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern=p)
                               for p in PATTERNS)
    with (REPORT / "host-tests.log").open("w", encoding="utf-8") as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    after = hashes()
    receipt = {"finished_utc": datetime.now(timezone.utc).isoformat(), "patterns": PATTERNS,
               "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
               "skips": [reason for _, reason in result.skipped],
               "source_unchanged_during_tests": before == after, "source_sha256": after,
               "scope": "Temporary disconnected HTTP/service/CLI stores; no physical telemetry or paid provider calls"}
    (REPORT / "host-tests.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in receipt.items() if k != "source_sha256"}, indent=2))
    return int(not result.wasSuccessful() or before != after)


if __name__ == "__main__":
    sys.exit(main())
