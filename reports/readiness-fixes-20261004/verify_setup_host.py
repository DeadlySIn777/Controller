"""Host-only regression runner; a real main file supports Windows spawn tests."""
from pathlib import Path
import hashlib
import json
import sys
import unittest
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

def main():
    report = Path(__file__).resolve().parent
    files = sorted(list((ROOT / "controller_config").glob("setup_*.py")) +
                   list((ROOT / "controller_config/web").glob("*")) +
                   list((ROOT / "tests").glob("test_setup*.py")))
    def snapshot():
        return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in files if p.is_file()}
    before = snapshot()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_setup*.py")
    with (report / "setup-host-tests-final.log").open("w", encoding="utf-8") as log:
        result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    after = snapshot()
    receipt = {"scope": "Host tests; temporary state and fake providers. No target, HDL, vendor, physical or paid-model qualification.",
               "finished_utc": datetime.now(timezone.utc).isoformat(), "tests_run": result.testsRun,
               "failures": len(result.failures), "errors": len(result.errors), "skips": len(result.skipped),
               "source_unchanged_during_tests": before == after, "source_sha256": after}
    (report / "setup-host-tests-final.json").write_text(json.dumps(receipt, indent=2), encoding="utf-8")
    print(json.dumps({k: v for k, v in receipt.items() if k != "source_sha256"}, indent=2))
    return int(not result.wasSuccessful() or before != after)

if __name__ == "__main__":
    sys.exit(main())
