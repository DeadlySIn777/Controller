"""Disconnected host regressions; main-file entry supports Windows spawn."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
REPORT = Path(__file__).resolve().parent
PATTERNS = ["test_setup*.py", "test_diagnostic*.py", "test_package_archive.py",
            "test_machine_state.py", "test_configuration*.py", "test_runtime_configuration.py",
            "test_persistent_runtime.py", "test_release.py"]


def main():
    sources = sorted(list((ROOT / "controller_config").rglob("*.py")) +
                     list((ROOT / "controller_config/web").glob("*")) +
                     [p for pattern in PATTERNS for p in (ROOT / "tests").glob(pattern)])
    def hashes():
        return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
                for p in sources if p.is_file()}
    before = hashes()
    suite = unittest.TestSuite(unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern=p)
                               for p in PATTERNS)
    with (REPORT / "host-tests.log").open("w", encoding="utf-8") as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    after = hashes()
    receipt = {"scope": "Disconnected host/service/CLI/HTTP tests with authored simulation, fake providers and temporary files. No paid calls, physical telemetry, target compilation, HDL, vendor or electrical qualification.",
               "finished_utc": datetime.now(timezone.utc).isoformat(),
               "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
               "skips": [{"test": str(test), "reason": reason} for test, reason in result.skipped],
               "source_unchanged_during_tests": before == after, "source_sha256": after,
               "patterns": PATTERNS}
    (REPORT / "host-tests.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in receipt.items() if k != "source_sha256"}, indent=2))
    return int(not result.wasSuccessful() or before != after)


if __name__ == "__main__":
    sys.exit(main())
