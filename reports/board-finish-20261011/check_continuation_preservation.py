"""Recheck installed tools and frozen continuation inputs without changing CAD."""
import datetime
import hashlib
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
EXTERNAL = Path("Z:/pcb-runs/claude-finish")


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    receipt_paths = [
        HERE / "gate-install-receipt.json",
        HERE / "stitch-margin-audit/guard-v2/installation-receipt.json",
        HERE / "power-audit/field-current-repair/installation-receipt.json",
    ]
    gate, stitch, field = [json.loads(p.read_text(encoding="utf-8")) for p in receipt_paths]
    frozen = field["active_combined_and_live_inputs_after"]
    assert frozen == field["active_combined_and_live_inputs_before"]
    assert len(frozen) == field["active_combined_and_live_input_count"] == 350
    expected = {}

    def bind(path, sha, role):
        key = str(Path(path).resolve())
        if key in expected and expected[key]["expected_sha256"] != sha:
            raise ValueError("Conflicting expected hashes for " + key)
        if key in expected:
            expected[key]["roles"].append(role)
        else:
            expected[key] = {"expected_sha256": sha, "roles": [role]}

    for path, sha in frozen.items():
        bind(path, sha, "frozen_native_and_live_input")
    for name, sha in gate["installed"].items():
        bind(EXTERNAL / "tools" / name, sha, "installed_routing_guard")
    for name, sha in gate["original_hashes"].items():
        bind(Path(gate["backup"]) / name, sha, "original_routing_tool_backup")
    for name, sha in gate["board_ledger_hashes_after"].items():
        bind(EXTERNAL / "integrate" / name, sha, "preserved_live_board_or_ledger")
    for receipt in (stitch, field):
        for path, sha in receipt["destination_after"].items():
            bind(path, sha, "installed_planner_guard")
        bind(receipt["backup"], receipt["backup_sha256"], "original_planner_backup")
    for key, row in expected.items():
        path = Path(key)
        row["observed_sha256"] = digest(path) if path.is_file() else None
        row["match"] = row["observed_sha256"] == row["expected_sha256"]
    failures = [key for key, row in expected.items() if not row["match"]]
    result = {
        "schema": "board-continuation-preservation-v1",
        "utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        "verdict": "PASS" if not failures else "FAIL",
        "frozen_input_count": len(frozen),
        "unique_checked_files": len(expected),
        "failures": failures,
        "files": expected,
        "installation_receipt_hashes": {str(p): digest(p) for p in receipt_paths},
        "script_sha256": digest(Path(__file__)),
        "scope": "Listed file preservation and installed-tool identity only; no routing, native DRC, electrical or manufacturing qualification",
        "board_written": False,
        "native_jobs": 0,
        "gpu_jobs": 0,
    }
    output = HERE / "continuation-preservation-r1.json"
    if output.exists():
        raise FileExistsError("Preserve the existing receipt; use a distinct revision")
    output.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({k: result[k] for k in ("verdict", "frozen_input_count", "unique_checked_files", "failures")}))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
