"""Execute exact-source setup/runtime checks and write exclusive lab evidence."""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))


def source_inventory():
    paths = list((ROOT / "controller_config").glob("*.py")) + [
        ROOT / "controller_lab/cnc3_configuration.py", ROOT / "tests/test_cnc3_configuration.py",
        ROOT / "tools/prepare_cnc3_sim2.py", ROOT / "tools/create_cnc3_qualification_fixture.py",
        Path(__file__)]
    return {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
            for path in sorted(set(paths))}


class Result(unittest.TextTestResult):
    def __init__(self, *args):
        super().__init__(*args)
        self.observations = []

    def addSuccess(self, test):
        super().addSuccess(test)
        self.observations.append({"test": test.id(), "status": "PASS"})

    def addSubTest(self, test, subtest, error):
        super().addSubTest(test, subtest, error)
        self.observations.append({"test": subtest.id(), "status": "FAIL" if error else "PASS"})


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to((ROOT / "reports").resolve()) or output.exists():
        parser.error("Evidence must use a new directory in this workspace's reports")
    output.mkdir(parents=True, exist_ok=False)
    before = source_inventory()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_cnc3_configuration.py")
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2, resultclass=Result).run(suite)
    after = source_inventory()
    stable = before == after
    status = "PASS" if result.wasSuccessful() and stable else "FAIL"
    receipt = {"schema_version": 1, "utc": datetime.now(timezone.utc).isoformat(),
        "kind": "cnc3_sim2_configuration_tests", "status": status, "python": platform.python_version(),
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "skipped": len(result.skipped), "observations": result.observations,
        "source_sha256": before, "source_stable": stable, "source_sha256_after": after,
        "physical_measurements": 0, "paid_api_calls": 0, "device_connections": 0,
        "physical_commissioning_complete": False, "manufacturing_ready": False}
    with (output / "tests.log").open("x", encoding="utf-8") as handle:
        handle.write(stream.getvalue())
    receipt["log_sha256"] = hashlib.sha256((output / "tests.log").read_bytes()).hexdigest()
    with (output / "receipt.json").open("x", encoding="utf-8") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"status": status, "tests_run": result.testsRun, "observations": len(result.observations), "source_stable": stable}))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
