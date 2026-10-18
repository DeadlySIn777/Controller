"""Focused no-network setup intelligence and allowance verification."""
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
OUTPUT = Path(__file__).resolve().parent
FILES = ["controller_config/setup_ai.py", "controller_config/setup_budget.py",
         "controller_config/setup_assistant.py", "controller_config/setup_facts.py",
         "tests/test_setup_ai.py", "tests/test_setup_budget.py", "tests/test_setup_assistant.py"]


def hashes():
    return {name: hashlib.sha256((ROOT / name).read_bytes()).hexdigest() for name in FILES}


def main():
    before = hashes()
    started = datetime.now(timezone.utc).isoformat()
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()
    for name in ("test_setup_ai.py", "test_setup_budget.py", "test_setup_assistant.py"):
        suite.addTests(loader.discover(str(ROOT / "tests"), pattern=name))
    log = io.StringIO()
    timer = time.perf_counter()
    result = unittest.TextTestRunner(stream=log, verbosity=2).run(suite)
    after = hashes()
    receipt = {"schema_version": 1, "scope": "actual disconnected setup service, fake provider, native local process locks, no network or API keys",
               "started_utc": started, "finished_utc": datetime.now(timezone.utc).isoformat(),
               "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
               "skipped": len(result.skipped), "elapsed_seconds": round(time.perf_counter() - timer, 3),
               "python": sys.version, "passed": result.wasSuccessful(), "paid_provider_calls": 0,
               "source_sha256": after, "source_unchanged_during_tests": before == after,
               "not_evidence_for": ["paid-model expert quality", "physical commissioning", "target firmware", "electrical or motion qualification", "provider final billing authentication"]}
    (OUTPUT / "ai-verification.log").write_text(log.getvalue(), encoding="utf-8")
    (OUTPUT / "ai-verification.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(receipt, indent=2))
    return 0 if result.wasSuccessful() and before == after else 1


if __name__ == "__main__":
    sys.exit(main())
