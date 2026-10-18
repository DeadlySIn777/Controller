"""Run the release checker tests only, with report-local results and no bytecode."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
paths = [
    "tests/test_release.py", "tools/check_release.py",
    "manufacturing/release-manifest.json", "hardware/motherboard/design.json",
    "hardware/motherboard/bom.csv", "hardware/board_review/board-view.json",
    "hardware/board_review/revisions/20261002-30/motherboard-native-candidate.kicad_pcb",
]

def snapshot():
    return {path: hashlib.sha256((ROOT / path).read_bytes()).hexdigest() for path in paths}

before = snapshot()
command = [sys.executable, "-B", "-m", "unittest", "discover", "-s", "tests", "-p", "test_release.py", "-v"]
started = datetime.now(timezone.utc).isoformat()
result = subprocess.run(command, cwd=ROOT, capture_output=True, text=True)
after = snapshot()
(OUT / "hardware-release-tests-r02.log").write_text(result.stdout + result.stderr, encoding="utf-8", newline="\n")
report = dict(command=command, started_utc=started,
              finished_utc=datetime.now(timezone.utc).isoformat(), returncode=result.returncode,
              hashes_before=before, hashes_after=after, checked_files_unchanged=before == after,
              scope="Release-manifest host tests only; no native or electrical or target or physical qualification.")
(OUT / "hardware-release-tests-r02.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8", newline="\n")
print(result.stdout + result.stderr, end="")
print(json.dumps(dict(returncode=result.returncode, checked_files_unchanged=before == after)))
raise SystemExit(result.returncode)
