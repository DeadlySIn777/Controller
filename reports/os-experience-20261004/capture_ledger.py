"""Bind browser observations to source bytes; does not drive the browser."""
import hashlib
import json
from pathlib import Path
from datetime import datetime, timezone
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent / "browser-r03"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, data):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    raw = ROOT / "reports/os-experience-20261004/os/run-r03/receipt.json"
    source = json.loads(raw.read_text())['source_sha256']
    current = {name: digest(ROOT / name) for name in source}
    if current != source:
        raise ValueError("Current app source differs from tested OS closure")
    # Enumerate only this explicitly authored, report-local workspace.
    fixture_files = {p.relative_to(ROOT).as_posix(): digest(p)
                     for p in (ROOT / "reports/os-experience-20261004/preview-r02").rglob("*")
                     if p.is_file() and "__pycache__" not in p.parts}
    if sys.argv[1:] == ["prepare"]:
        OUT.mkdir(exist_ok=False)
        write(OUT / "before.json", {"utc": datetime.now(timezone.utc).isoformat(),
              "source_sha256": current, "fixture_sha256": fixture_files,
              "tested_os_receipt_sha256": digest(raw)})
        print("Source ledger prepared; browser observations not yet captured")
        return
    if sys.argv[1:] != ["finalize"]:
        raise ValueError("Use prepare or finalize")
    before = json.loads((OUT / "before.json").read_text())
    observations = json.loads((OUT / "observations.json").read_text())
    if before["source_sha256"] != current or before["fixture_sha256"] != fixture_files:
        raise ValueError("Sources or report-local settings changed during read-only capture")
    if len(observations) != 4 or not all(row["no_horizontal_overflow"] and row["primary_action_height"] >= 48 for row in observations):
        raise ValueError("Viewport observations failed")
    artifacts = {p.name: digest(p) for p in OUT.iterdir() if p.is_file()}
    write(OUT / "receipt.json", {"utc": datetime.now(timezone.utc).isoformat(),
          "status": "PASS_WITHIN_BROWSER_LAYOUT_SCOPE", "source_sha256": current,
          "sources_unchanged_during_capture": True, "fixture_unchanged": True,
          "before_sha256": digest(OUT / "before.json"), "artifacts_sha256": artifacts,
          "ledger_runner_sha256": digest(Path(__file__)),
          "observations": observations, "execution": "Root agent, actual in-app browser; page reloaded after before ledger",
          "limitations": ["Viewport layout checks, not physical touchscreen tests", "No measured frame pacing, input latency, boot speed, RT scheduling or target thermals"],
          "motion_requests": 0, "paid_api_calls": 0, "physical_measurements": 0})
    print(json.dumps({"status": "PASS_WITHIN_BROWSER_LAYOUT_SCOPE", "viewports": 4, "sources": len(current)}))


if __name__ == "__main__":
    main()
