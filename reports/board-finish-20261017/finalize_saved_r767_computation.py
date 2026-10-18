"""Recover final receipt after a stale prepare-receipt path stopped serialization.

The completed original run and its exit1 stay untouched. Recompute the result
counts from every saved check and bind each saved gain witness and actual input.
This does not rerun geometry, erase raw errors or qualify manufacture.
"""
import datetime as dt
import hashlib
import json
from pathlib import Path

H = Path(__file__).resolve().parent
P = H / "actual-full-audit-repaired-r1/r763"
SAVED = H / "actual-full-audit-repaired-r1/r767"
OUT = H / "actual-full-audit-repaired-r1/r767-finalization-r1"
BEFORE = H.parent / "board-finish-20261011/continuation-r2/field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763"
NF = H.parent / "board-finish-20261011/continuation-r2/combined-R753-one-full-native-fill-cached-DRC-r299/native-full"
GUARD = H / "resumed-full-native-host-audits-repaired-r1"
SCRIPT = H / "actual-full-audit-repaired-r1/audit_source_gains_rebound_r767.py"


def sha(p):
    with Path(p).open("rb") as stream:
        return hashlib.file_digest(stream, "sha256").hexdigest()


def read(p):
    return json.loads(Path(p).read_bytes())


def main():
    assert not OUT.exists()
    parent = read(P / "receipt.json")
    prep = read(BEFORE / "prepare-receipt.json")
    status = read(GUARD / "status.json")
    assert status["phase"] == "FAILED_RESULTS_PRESERVED"
    failed = status["results"][1]
    assert failed["step"] == 2 and failed["exit_code"] == 1
    log = GUARD / "step-2.log"
    assert sha(log) == failed["log_sha256"]
    logged = log.read_text(encoding="utf-8")
    assert "FileNotFoundError" in logged and "prepare-receipt.json" in logged
    assert "'input_SHA256':{str(p):sha(p)for p in files}" in logged
    text = SCRIPT.read_text(encoding="utf-8")
    assert text.count("P/'prepare-receipt.json'") == 1
    assert not (P / "prepare-receipt.json").exists()
    assert sha(P / "actual-combined-full-after-model.pkl") == parent["after_actual_model_SHA256"]
    assert sha(P / "actual-combined-full-after-all-net-groups.pkl") == parent["after_actual_groups_SHA256"]
    assert sha(BEFORE / "actual-full-R157-before-model.pkl") == prep["actual_before_model_SHA256"]
    assert sha(BEFORE / "actual-full-R157-before-all-net-groups.pkl") == prep["actual_before_groups_SHA256"]
    native = read(NF / "receipt.json")
    assert sha(NF / "partitions.json") == native["partitions_SHA256"]
    checks = read(SAVED / "all-actual-source-gain-guard-checks.json")
    gains = read(SAVED / "all-actual-source-gains.json")
    cpp = read(SAVED / "nine-source-actual-CPP-versus-drilled-native-pad-partitions.json")
    roots = {r["net"] for r in parent["all_nine_source_banks"]}
    assert len(cpp) == len(roots) == 9 and {r["net"] for r in cpp} == roots
    assert {r["net"] for r in gains} <= roots
    assert len([line for line in logged.splitlines() if line.startswith("R767 /")]) == 9
    errors = [r for r in checks if r["gap_mm"] < r["native_required_mm"]]
    planning = [r for r in checks if r["gap_mm"] < r["planner_required_mm"]]
    near = [{**r, "true_nominal_curved_pad_clearance": "OPEN; ERROR_INSIDE polygon does not prove nominal outer boundary"}
            for r in checks if r["kind"] == "ACTUAL_DISCRETE_pad" and r["gap_mm"] < r["native_required_mm"] + .005]
    assert errors == read(SAVED / "source-gain-native-clearance-errors.json")
    assert planning == read(SAVED / "source-gain-extra025-planning-margin-deficits.json")
    assert near == read(SAVED / "source-gain-foreign-pad-nominal-boundary-uncertainty.json")
    checkpoint = read(SAVED / "checkpoint-source-gain-guard-counts.json")
    assert checkpoint == {"finished_source": "/motherboard_motors/AUX_5V_B", "checks": len(checks),
                          "native_errors": len(errors), "planner_errors": len(planning)}
    pins = {str(p): sha(p) for p in [Path(__file__), SCRIPT, log, GUARD / "status.json", P / "receipt.json",
            BEFORE / "prepare-receipt.json", NF / "receipt.json", NF / "partitions.json",
            P / "actual-combined-full-after-model.pkl", P / "actual-combined-full-after-all-net-groups.pkl",
            BEFORE / "actual-full-R157-before-model.pkl", BEFORE / "actual-full-R157-before-all-net-groups.pkl",
            *SAVED.glob("*.json")]}
    for row in gains:
        witness = row["gain"]
        if witness["EMPTY"]:
            continue
        path = Path(witness["file"])
        assert path.resolve().is_relative_to(SAVED.resolve())
        assert sha(path) == witness["WKB_SHA256"]
        pins[str(path)] = sha(path)
    padfile = P / "after-all-9971-native-pad-binding.json"
    pads = {r["UUID"]: r for r in read(padfile)}
    error_pads = [{"raw_error": r, "actual_native_pad": pads[r["foreign_UUID"]],
                   "conductor_vs_NPTH_hole_and_washer_clearance": "SEPARATE_INDEPENDENT_REVIEW_PENDING_RAW_ERROR_RETAINED"}
                  for r in errors if r["kind"] == "ACTUAL_DISCRETE_pad"]
    pins[str(padfile)] = sha(padfile)
    counts = {"CPP_vs_drilled_source_partition_mismatches": sum(bool(r["CPP_source_pads_absent_drilled_polygon_source"] or r["drilled_polygon_source_pads_absent_CPP_source"]) for r in cpp),
              "actual_source_gain_raw_native_guard_errors": len(errors), "actual_source_gain_extra025_planner_deficits": len(planning),
              "source_gain_nominal_curved_pad_boundary_open_cases": len(near)}
    OUT.mkdir()
    result = {"status": "SAVED_COMPLETE_R767_COMPUTATION_FINALIZED_RAW_FAILURES_AND_NPTH_SCOPE_REVIEW_RETAINED",
              "utc": dt.datetime.now(dt.timezone.utc).isoformat(), "counts": counts,
              "source_gain_checks": len(checks), "saved_actual_gain_witnesses": len(gains),
              "original_process_exit_code": 1, "original_error": "Final input hash list incorrectly looked for prepare-receipt under rebound AFTER folder",
              "actual_prepare_receipt_used_for_final_binding": str(BEFORE / "prepare-receipt.json"),
              "original_failed_script_log_outputs_preserved": True, "saved_count_calculations_independently_recomputed": True,
              "all_saved_gain_WKB_hashes_verified": True, "actual_native_error_pad_classifications": error_pads,
              "parent_R763_status": parent["status"], "parent_R763_counts": parent["counts"],
              "inherited_failures_not_promoted": True, "source_current_voltage_thermal_SI_assembly": "OPEN",
              "input_SHA256": pins, "native_jobs": 0, "geometry_or_masks_changed": False,
              "adopted": False, "manufacturing_ready": False}
    (OUT / "receipt.json").write_text(json.dumps(result, indent=1) + "\n", encoding="utf-8")
    print(json.dumps({"status": result["status"], "counts": counts, "checks": len(checks), "gains": len(gains)}))


if __name__ == "__main__":
    main()
