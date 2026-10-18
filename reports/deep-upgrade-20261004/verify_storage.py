"""Focused host verification; explicit temporary simulation fixtures only."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import platform
import sys
import unittest

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

FILES = ["controller_config/diagnostic_recorder.py", "controller_config/machine_state.py",
         "controller_config/diagnostic_explanations.py", "controller_config/package_archive.py",
         "tests/test_diagnostic_recorder.py", "tests/test_machine_state.py",
         "tests/test_diagnostic_explanations.py", "tests/test_package_archive.py"]


def hashes(files):
    return {str(path): hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in files}


def main():
    before = hashes(FILES)
    log = io.StringIO()
    suite = unittest.TestSuite()
    for pattern in ("test_diagnostic_recorder.py", "test_machine_state.py",
                    "test_diagnostic_explanations.py", "test_package_archive.py"):
        suite.addTests(unittest.defaultTestLoader.discover(str(ROOT / "tests"), pattern=pattern))
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    from controller_config.diagnostic_recorder import DiagnosticRecorder
    preservation = []
    base = ROOT / "reports/diagnostics-zstd-20261004/ui-preview"
    for folder in (base / "diagnostics", base / "diagnostic-example", base / "diagnostic-example-v2"):
        files = [path.relative_to(ROOT) for path in folder.iterdir() if path.is_file()]
        old = hashes(files)
        recorder = DiagnosticRecorder(folder)
        status, report = recorder.status(), recorder.report()
        preservation.append({"directory": str(folder.relative_to(ROOT)), "file_count": len(files),
                             "record_count": status["record_count"], "report_record_count": report["record_count"],
                             "unchanged": old == hashes(files), "sha256": old})
    receipt = {"schema_version": 1, "scope": "host_simulation_and_temp_file_verification_only",
               "completed_utc": datetime.now(timezone.utc).isoformat(), "python": sys.version,
               "platform": platform.platform(), "tests_reported": result.testsRun,
               "tests_passed": result.testsRun - len(result.skipped) - len(result.failures) - len(result.errors),
               "failures": [(case.id(), detail) for case, detail in result.failures],
               "errors": [(case.id(), detail) for case, detail in result.errors],
               "skips": [(case.id(), reason) for case, reason in result.skipped],
               "source_sha256": before, "source_unchanged_during_tests": before == hashes(FILES),
               "existing_recording_preservation": preservation, "paid_calls": 0,
               "physical_commands": 0, "target_power_loss_qualified": False,
               "hardware_qualification": False}
    (REPORT / "storage-verification.log").write_text(log.getvalue(), encoding="utf-8")
    (REPORT / "storage-verification.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
    print(json.dumps({key: receipt[key] for key in ("tests_reported", "tests_passed", "skips",
          "source_unchanged_during_tests", "paid_calls", "physical_commands")}))
    return 0 if result.wasSuccessful() and receipt["source_unchanged_during_tests"] and all(item["unchanged"] for item in preservation) else 1


if __name__ == "__main__":
    raise SystemExit(main())
