"""Read-only readiness/provenance audit; outputs only beside this script.

No KiCad import, PCB load/save, CAD generator, source recorder, or machine I/O.
"""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent

def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def read_json(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))

manifest_path = "manufacturing/release-manifest.json"
manifest = read_json(manifest_path)
records = []

def check(relative, expected, origin):
    path = ROOT / relative
    actual = digest(path) if path.is_file() else None
    records.append(dict(path=relative, expected_sha256=expected, actual_sha256=actual,
                        matches=actual == expected, origin=origin))

def walk(value, origin):
    if isinstance(value, dict):
        for key, entry in value.items():
            if key == "sha256" and "path" in value:
                check(value["path"], entry, origin)
            elif key.endswith("_sha256"):
                stem = key[:-7]
                for suffix in ("_path", "_file"):
                    other = stem + suffix
                    if other in value:
                        check(value[other], entry, origin + "/" + key)
                        break
            walk(entry, origin + "/" + key)
    elif isinstance(value, list):
        for index, entry in enumerate(value):
            walk(entry, origin + "/" + str(index))

walk(manifest, manifest_path)
stage_dir = "reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02/"
freeze = read_json(stage_dir + "freeze-receipt-r02.json")
for path, expected in freeze["before_source_sha256"].items():
    check("hardware/motherboard/" + path, expected, stage_dir + "freeze-receipt-r02.json/before_source_sha256")
for path, expected in freeze["candidate_source_sha256"].items():
    check(stage_dir + "candidate/motherboard/" + path, expected, stage_dir + "freeze-receipt-r02.json/candidate_source_sha256")
handoff_dir = "reports/argus-routing-handoff-20261002/ROOT104-CAD30/"
handoff = read_json(handoff_dir + "SHA256-MANIFEST.json")
for path, entry in handoff["files"].items():
    check(handoff_dir + path, entry["sha256"], handoff_dir + "SHA256-MANIFEST.json")

spec = importlib.util.spec_from_file_location("readiness_release_check", ROOT / "tools/check_release.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)
gate_results = {stage: module.check_release(manifest, ROOT, stage)
                for stage in ("prototype", "production")}

view = manifest["partial_candidate"]["published_viewer"]
board = ROOT / view["board_file"]
text = board.read_text(encoding="utf-8")
import re
text_counts = {
    "footprints": len(re.findall(r"^\t\(footprint\b", text, re.M)),
    "tracks": len(re.findall(r"^\t\(segment\b", text, re.M)),
    "vias": len(re.findall(r"^\t\(via\b", text, re.M)),
    "zones_and_ruleareas": len(re.findall(r"^\t\(zone\b", text, re.M)),
    "scope": "Text object counts only; not a fresh native KiCad/ERC/DRC/connectivity run.",
}

out = {
    "checked_utc": datetime.now(timezone.utc).isoformat(),
    "audit_script_sha256": digest(Path(__file__)),
    "manifest_sha256": digest(ROOT / manifest_path),
    "scope": "Read-only evidence and source hash comparison; no fresh electrical/native/physical qualification.",
    "hash_comparisons": records,
    "hash_comparison_count": len(records),
    "hash_mismatch_count": sum(not row["matches"] for row in records),
    "gate_results": gate_results,
    "published_board_text_counts": text_counts,
    "published_viewer_recorded_zone_or_rulearea_count": view["native_zone_or_rulearea_count"],
    "manufacturing_ready": False,
    "hardware_files_written": False,
}
(OUT / "hardware-release-readonly-evidence.json").write_text(json.dumps(out, indent=2) + "\n", encoding="utf-8", newline="\n")
print(json.dumps({key: out[key] for key in ("hash_comparison_count", "hash_mismatch_count", "published_board_text_counts", "published_viewer_recorded_zone_or_rulearea_count")}, indent=2))
print(json.dumps({stage: dict(ready=value["ready"], blocker_count=len(value["blockers"]))
                  for stage, value in gate_results.items()}, indent=2))
