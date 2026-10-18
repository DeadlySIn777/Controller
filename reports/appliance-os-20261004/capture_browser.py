"""Source ledger for actual root browser actions; this script does not drive UI."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from controller_os.image import application_sources

OUT = Path(__file__).resolve().parent / "browser-r01"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    sources = {name: hashlib.sha256(raw).hexdigest() for name, raw in application_sources(ROOT).items()}
    if sys.argv[1:] == ["prepare"]:
        OUT.mkdir(exist_ok=False)
        write(OUT / "before.json", {"utc": datetime.now(timezone.utc).isoformat(), "source_sha256": sources})
        print(json.dumps({"sources": len(sources), "stage": "prepared; no browser observations yet"}))
        return
    if sys.argv[1:] != ["finalize"]:
        raise ValueError("Use prepare or finalize")
    before = json.loads((OUT / "before.json").read_text())
    if before["source_sha256"] != sources:
        raise ValueError("Source changed during browser execution; keep historical capture and use a new run")
    rows = json.loads((OUT / "observations.json").read_text())
    if not rows or not all(row["passed"] for row in rows):
        raise ValueError("Browser observation did not pass")
    artifacts = {p.name: sha(p) for p in OUT.iterdir() if p.is_file()}
    write(OUT / "receipt.json", {"schema_version": 1, "utc": datetime.now(timezone.utc).isoformat(),
          "status": "PASS_WITHIN_BROWSER_WORKFLOW_AND_LAYOUT_SCOPE", "source_sha256": sources,
          "source_stable": True, "observations": rows, "artifacts_sha256": artifacts,
          "runner_sha256": sha(Path(__file__)), "execution": "Root agent; actual in-app browser with explicit report-local fixture",
          "scope": "Navigation, guarded preferences/reset/undo/service entry, export availability and viewport layout",
          "target_boot_performance_measured": False, "physical_touch_measured": False,
          "frame_pacing_measured": False, "motion_continuity_tested": False,
          "physical_measurements": 0, "paid_api_calls": 0, "routing_modified": False})
    print(json.dumps({"status": "PASS_WITHIN_BROWSER_WORKFLOW_AND_LAYOUT_SCOPE", "observations": len(rows), "sources": len(sources)}))


if __name__ == "__main__":
    main()
