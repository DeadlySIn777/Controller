"""Reproducible Windows-spawn-safe disconnected software verification."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
PATTERNS = ["test_setup*.py", "test_diagnostic*.py", "test_machine_state.py",
            "test_package_archive.py", "test_configuration*.py", "test_runtime_configuration.py",
            "test_persistent_runtime.py", "test_recovery_cli.py", "test_motherboard_iol1_readonly.py", "test_release.py"]


def main():
    sources = sorted(list((ROOT / "controller_config").rglob("*.py")) +
                     list((ROOT / "controller_config/web").glob("*")) +
                     list((ROOT / "firmware/motherboard_iol1_readonly").glob("*.c")) +
                     list((ROOT / "firmware/motherboard_iol1_readonly").glob("*.h")) +
                     [path for pattern in PATTERNS for path in (ROOT / "tests").glob(pattern)])
    def hashes():
        return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
                for path in sources if path.is_file()}
    before = hashes()
    suite = unittest.TestSuite(unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern=pattern)
                               for pattern in PATTERNS)
    with (REPORT / "host-tests.log").open("x", encoding="utf-8") as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    after = hashes()
    receipt = {"scope": "Disconnected host/service/CLI/HTTP checks, authored simulation, fake AI transports and temporary files. No paid calls, device access, target execution, HDL/synthesis replay, ERC/DRC or physical qualification.",
               "finished_utc": datetime.now(timezone.utc).isoformat(), "tests_run": result.testsRun,
               "failures": len(result.failures), "errors": len(result.errors),
               "skips": [{"test": str(test), "reason": reason} for test, reason in result.skipped],
               "source_unchanged_during_tests": before == after, "source_sha256": after, "patterns": PATTERNS}
    with (REPORT / "host-tests.json").open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2)
    print(json.dumps({key: value for key, value in receipt.items() if key != "source_sha256"}, indent=2))
    return int(not result.wasSuccessful() or before != after)


if __name__ == "__main__":
    sys.exit(main())
