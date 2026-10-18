"""Capture local HTTP regression evidence; never opens hardware or paid adapters."""
from datetime import datetime, timezone
import difflib
import hashlib
import json
from pathlib import Path
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
PATHS = (
    "controller_config/setup_web.py", "tests/test_setup_web.py",
    "controller_config/setup_service.py", "controller_config/setup_budget.py",
    "controller_config/setup_ai.py", "gateware/tools/record_evidence.py",
    "gateware/validation/manifest.json", "gateware/validation/simulation.log",
    "gateware/validation/status_encoder.hex",
)


def hashes():
    return {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in PATHS}


before = hashes()
command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_setup_web.py", "-v"]
started = datetime.now(timezone.utc).isoformat()
run = subprocess.run(command, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
finished = datetime.now(timezone.utc).isoformat()
(HERE / "setup-web-tests-r02.log").write_bytes(run.stdout)
after = hashes()
receipt = dict(command=command, started_utc=started, finished_utc=finished,
               returncode=run.returncode, log="setup-web-tests-r02.log",
               inputs_unchanged=before == after, before=before, after=after,
               prior_rtl_verification="rtl-web-verification.json",
               scope="15 HTTP host tests: temporary loopback simulation stores and mocked advisor; no hardware, real provider, HDL compilation or historical evidence regeneration.")
for source in ("controller_config/setup_web.py", "gateware/tools/record_evidence.py"):
    archive = HERE / "before" / source
    old, new = archive.read_text(encoding="utf-8").splitlines(True), (ROOT / source).read_text(encoding="utf-8").splitlines(True)
    target = source.replace("/", "__") + ".diff"
    (HERE / target).write_text("".join(difflib.unified_diff(old, new, fromfile="before/" + source, tofile=source)), encoding="utf-8")
(HERE / "setup-web-verification-r02.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8")
print(json.dumps({"returncode": run.returncode, "inputs_unchanged": before == after,
                  "receipt": str(HERE / "setup-web-verification-r02.json")}))
sys.exit(run.returncode if run.returncode else (0 if before == after else 1))
