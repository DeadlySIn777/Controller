"""Source-bound HTTP contract checks for the local appliance shell."""
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


def sources():
    files = [p for folder in ("controller_shell", "controller_config", "controller_appliance") for p in (ROOT / folder).rglob("*")
             if p.is_file() and p.suffix in (".py", ".js", ".css", ".html")]
    files += [ROOT / "tests/test_controller_shell.py", Path(__file__)]
    return {p.relative_to(ROOT).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(files)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    output = args.output.resolve()
    if not output.is_relative_to(ROOT / "reports") or output.exists():
        parser.error("Choose a new output directory inside reports")
    output.mkdir(parents=True, exist_ok=False)
    before = sources()
    log = io.StringIO()
    suite = unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern="test_controller_shell.py")
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    after = sources()
    receipt = {"schema_version": 1, "kind": "controller_os_shell_http_contract", "utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS" if result.wasSuccessful() and before == after else "FAIL", "python": platform.python_version(),
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "skipped": len(result.skipped),
        "source_sha256": before, "source_stable": before == after, "source_sha256_after": after,
        "bootable_os_image_tested": False, "physical_measurements": 0, "paid_api_calls": 0, "device_connections": 0,
        "physical_commissioning_complete": False, "manufacturing_ready": False}
    (output / "tests.log").write_text(log.getvalue(), encoding="utf-8")
    receipt["log_sha256"] = hashlib.sha256((output / "tests.log").read_bytes()).hexdigest()
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("status", "tests_run", "failures", "errors", "source_stable")}))
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
