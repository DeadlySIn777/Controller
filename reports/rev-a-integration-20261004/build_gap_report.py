"""Consolidate scoped evidence; never infer a full machine from component passes."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
EXTERNAL = Path("C:/Users/Gluis/claude-worktrees/controller-interface-spec")


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((HERE / name).read_text(encoding="utf-8"))


def main():
    host, rtl, vendor = (read(name + "/receipt.json") for name in ("host", "rtl", "vendor"))
    preservation = read("preservation-final.json")
    controls = read("baseline-negative-controls.json")
    baseline = read("baseline.json")
    retained_host_path = ROOT / "reports/deep-upgrade-20261004/host-tests.json"
    retained_host = json.loads(retained_host_path.read_text(encoding="utf-8"))
    verified = {}
    problems = []

    def verify(path, expected, base=ROOT):
        path = Path(path)
        if not path.is_absolute():
            path = base / path
        path = path.resolve()
        if not (path.is_relative_to(ROOT) or path.is_relative_to(EXTERNAL)):
            problems.append({"path": str(path), "error": "outside scoped source/evidence roots"})
            return
        if not path.is_file() or sha(path) != expected:
            problems.append({"path": str(path), "error": "missing or hash mismatch", "expected": expected})
            return
        verified[str(path)] = expected

    for row in rtl["source_and_evidence_hash_rechecks"]:
        verify(row["path"], row["sha256"])
    for row in rtl["runs"]:
        for item in [row["receipt"], *row["artifacts"]]:
            verify(item["path"], item["sha256"])
    verify(rtl["summary_generator"]["path"], rtl["summary_generator"]["sha256"])
    for path, expected in vendor["source_ledger_hashes"].items():
        verify(path, expected)
    for path, expected in vendor["evidence_artifact_sha256"].items():
        verify(path, expected, HERE / "vendor")
    for path, expected in host["source_sha256"].items():
        verify(path, expected)
    for path, expected in host["artifact_sha256"].items():
        verify(path, expected, HERE / "host")
    for row in (host["runtime_receipt"], host["cleanup_negative_control"]):
        verify(row["path"], row["sha256"], HERE / "host")
    verify(HERE / "baseline.json", controls["baseline_sha256"])
    verify(ROOT / "tools/check_rev_a_baseline.py", controls["tool_sha256"])
    same_feature_sources = all(retained_host["source_sha256"].get(path) == expected
                               and sha(ROOT / path) == expected
                               for path, expected in baseline["feature_sha256"].items())

    # These are deliberately separate predicates. Missing providers/adoption or
    # missing vendor execution cannot be repaired by an unrelated passing run.
    required = {
        "preservation_pass": preservation["status"] == "PASS",
        "negative_controls_pass": controls["all_passed"] is True,
        "retained_regression_same_feature_source": same_feature_sources
            and retained_host["failures"] == 0 and retained_host["errors"] == 0,
        "HAL_refusal_qualification_pass": host["status"] == "PASS",
        "HAL_source_stable": host["source_inputs_unchanged"] is True,
        "HAL_six_cases_pass": len(host["observations"]) == 6 and all(
            row["status"] == "PASS" for row in host["observations"]),
        "HAL_milestone_limit_preserved": host["full_requested_milestone_complete"] is False
            and host["scope"]["actual_LinuxCNC_motion_controller_trajectory"] is False
            and host["scope"]["all12_HAL_to_STEP_and_feedback_ACTIVE"] is False
            and host["scope"]["complete_IOL1_limits_probe_providers"] is False,
        "HAL_frozen_wire_lengths": host["scope"]["frozen_command_bytes"] == 96
            and host["scope"]["frozen_feedback_bytes"] == 176,
        "original_IS1_copies_match_archive": len(host["original_IS1_copies_match_current_preserved_archive"]) == 7
            and all(host["original_IS1_copies_match_current_preserved_archive"].values()),
        "cleanup_failure_controls_pass": host["cleanup_negative_control"]["receipt"]["status"] == "PASS"
            and len(host["cleanup_negative_control"]["receipt"]["cases"]) == 4
            and all(row["status"] == "PASS" for row in host["cleanup_negative_control"]["receipt"]["cases"]),
        "existing_rootfs_modules_preserved": host["installed_existing_rootfs_modules_preserved"] is True,
        "RTL_six_scoped_runs_pass": len(rtl["runs"]) == 6 and all(
            run["status"] == "PASS_WITHIN_DECLARED_SCOPE" for run in rtl["runs"]),
        "RTL_candidate_not_adopted": rtl["candidate_adopted"] is False,
        "full_machine_not_claimed": rtl["full_machine_milestone"] is False,
        "vendor_block_remains_explicit": vendor["status"] == "BLOCKED" and vendor["FPGA_PASS"] is False
            and vendor["executed_vendor_flow"] is False,
        "no_physical_promotion": rtl["physical_measurements"] == 0 and rtl["manufacturing_ready"] is False
            and vendor["physical_qualification"] is False and vendor["manufacturing_ready"] is False,
    }
    for name, passed in required.items():
        if not passed:
            problems.append({"predicate": name, "error": "qualification receipt contradicts declared scope"})
    artifacts = {name: {"path": "reports/rev-a-integration-20261004/" + name,
                         "sha256": sha(HERE / name)} for name in (
        "baseline.json", "preservation-final.json", "baseline-negative-controls.json",
        "host/receipt.json", "rtl/receipt.json", "vendor/receipt.json")}
    gaps = [
        {"id": "Q01", "status": "BLOCKED", "required": "One adopted complete versioned IS-2 CNC3 motherboard runtime",
         "gap": "Motion, CAP3 identity/qualification, current IOL1 acquisition and output authority exist as separate incomplete candidates."},
        {"id": "Q02", "status": "BLOCKED", "required": "Twelve-channel moving LinuxCNC task/HAL/host/serial-RTL virtual-machine execution",
         "gap": "Actual HAL callbacks and serial profile refusal are qualified; the complete moving trajectory and all feedback/providers are not."},
        {"id": "Q03", "status": "BLOCKED", "required": "24 DI, 16 smart DO, probes/limits/index/events and complete output authority in that same execution",
         "gap": "Unavailable/stale inputs and unsupported-output refusal pass; functional integrated provider/event paths remain missing."},
        {"id": "Q04", "status": "BLOCKED", "required": "Actual T20F256I4 Efinity synthesis/place/route/static timing",
         "gap": "No discoverable vendor installation or qualified complete-top project/pad-bank/clock/I/O constraints; entitlement not demonstrated."},
        {"id": "Q05", "status": "PHYSICAL_VALIDATION_REQUIRED", "required": "Actual target execution, live acquisition, loaded servo/SPI, watchdog/current/analog/thermal/brownout/power-fail measurements",
         "gap": "No physical device execution or measurements. Simulation does not close commissioning, safety or manufacturing."},
        {"id": "Q06", "status": "EXTERNAL_ROUTING_WORK", "required": "Finish and independently verify ROOT105/routing before hardware release",
         "gap": "Claude owns routing; this audit neither edits nor adopts it. Source26/ROOT104/CAD30 remains the last verified adopted baseline."},
    ]
    report = {
        "schema": 1, "finished_utc": datetime.now(timezone.utc).isoformat(),
        "evidence_integrity_status": "FAIL" if problems else "PASS",
        "full_requested_milestone_status": "BLOCKED", "full_requested_milestone_complete": False,
        "user_facing_feature_baseline_frozen": True, "frontend_features_added": 0,
        "api_calls": 0, "device_connections": 0, "physical_measurements": 0,
        "commissioning_promoted": False, "safety_qualification_promoted": False,
        "manufacturing_readiness_promoted": False, "vendor_FPGA_PASS": False,
        "classes": [
            {"label": "SOFTWARE PASS", "status": "FAIL" if problems else "PASS_WITHIN_SCOPE", "scope": "Actual host C, HAL refusal integration and source/settings preservation; ARM compile/link is separately identified."},
            {"label": "FPGA PASS", "status": "BLOCKED", "scope": "Actual-target Efinity flow not executed. Generic family mapping is a separate screen."},
            {"label": "SIMULATION PASS", "status": "FAIL" if problems else "PASS_WITHIN_SCOPE", "scope": "Compiled transport/motion/encoder/fault and current-C diagnostic replay; separate incomplete candidates, not one completed machine."},
            {"label": "PHYSICAL VALIDATION REQUIRED", "status": "NOT_RUN", "scope": "Live board/firmware/machine, loaded timing and electrical/environmental validation."}],
        "required_receipt_predicates": required, "independently_verified_hash_count": len(verified),
        "hash_or_predicate_problems": problems, "verified_sha256": verified,
        "canonical_evidence": artifacts, "gaps": gaps,
        "retained_software_regression": {"path": retained_host_path.relative_to(ROOT).as_posix(),
            "sha256": sha(retained_host_path), "reported": retained_host["tests_run"],
            "skips": len(retained_host["skips"]), "failures": retained_host["failures"],
            "errors": retained_host["errors"], "feature_source_matches": same_feature_sources,
            "reexecuted_this_qualification_pass": False},
        "interpretation": "Counts overlap and are not additive. Hashes attest retained bytes, not correct physical assumptions or signed provenance.",
        "generator_sha256": sha(Path(__file__)),
    }
    with (HERE / "gaps.json").open("x", encoding="utf-8") as handle:
        json.dump(report, handle, indent=2)
        handle.write("\n")
    print(json.dumps({key: report[key] for key in ("evidence_integrity_status", "full_requested_milestone_status",
                     "independently_verified_hash_count", "hash_or_predicate_problems")}))
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
