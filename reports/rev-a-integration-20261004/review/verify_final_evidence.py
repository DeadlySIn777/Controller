"""Independent read-only evidence review; writes only a fresh review receipt.

It rechecks recorded bytes and observed assertions, not physical readiness.
It never reruns a provider, opens a device, changes source or edits sealed evidence.
"""
import argparse
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import re

HERE = Path(__file__).resolve().parent
QUAL = HERE.parent
ROOT = QUAL.parents[1]


def sha(path):
    h = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def read(path):
    return json.loads(path.read_text(encoding="utf8"))


def absolute(name, base=ROOT):
    if name.startswith("/mnt/"):
        return Path(name[5].upper() + ":/" + name[7:])
    item = Path(name)
    return item if item.is_absolute() else base / item


def path_rows(value):
    if isinstance(value, dict):
        if isinstance(value.get("path"), str) and isinstance(value.get("sha256"), str):
            yield value
        for item in value.values():
            yield from path_rows(item)
    elif isinstance(value, list):
        for item in value:
            yield from path_rows(item)


def main(out):
    if out.exists():
        raise RuntimeError("Fresh review receipt required")
    checked = {}
    def verify(path, expected):
        path = path.resolve()
        observed = sha(path)
        if observed != expected:
            raise AssertionError({"path": str(path), "expected": expected, "actual": observed})
        checked[str(path)] = observed

    host_path = QUAL / "host/receipt.json"
    rtl_path = QUAL / "rtl/receipt.json"
    vendor_path = QUAL / "vendor/receipt.json"
    host, rtl, vendor = read(host_path), read(rtl_path), read(vendor_path)
    gaps_path = QUAL / "gaps.json"
    gaps = read(gaps_path)
    assert gaps["evidence_integrity_status"] == "PASS"
    assert gaps["full_requested_milestone_status"] == "BLOCKED"
    assert not gaps["full_requested_milestone_complete"]
    assert gaps["user_facing_feature_baseline_frozen"]
    assert not gaps["hash_or_predicate_problems"]
    assert all(gaps["required_receipt_predicates"].values())
    for key in ["frontend_features_added", "api_calls", "device_connections", "physical_measurements", "commissioning_promoted", "safety_qualification_promoted", "manufacturing_readiness_promoted", "vendor_FPGA_PASS"]:
        assert not gaps[key]
    assert len(gaps["verified_sha256"]) == gaps["independently_verified_hash_count"] == 440
    for name, digest in gaps["verified_sha256"].items():
        verify(absolute(name), digest)
    for row in path_rows(gaps["canonical_evidence"]):
        verify(absolute(row["path"]), row["sha256"])
    for name, digest in host["source_sha256"].items():
        verify(absolute(name), digest)
    for name, digest in host["artifact_sha256"].items():
        verify(absolute(name, QUAL / "host"), digest)
    rtl_rows = list(path_rows(rtl))
    for row in rtl_rows:
        verify(absolute(row["path"]), row["sha256"])
    assert host["status"] == "PASS" and host["source_inputs_unchanged"]
    assert host["installed_existing_rootfs_modules_preserved"]
    assert all(host["original_IS1_copies_match_current_preserved_archive"].values())
    assert not host["full_requested_milestone_complete"]
    assert not host["scope"]["actual_LinuxCNC_motion_controller_trajectory"]
    assert not host["scope"]["successful_motion_discovery"]
    assert not host["scope"]["all12_HAL_to_STEP_and_feedback_ACTIVE"]
    assert not host["scope"]["target_realtime_or_physical_qualification"]
    assert host["scope"]["frozen_command_bytes"] == 96
    assert host["scope"]["frozen_feedback_bytes"] == 176
    assert vendor["status"] == "BLOCKED" and vendor["actual_device"] == "T20F256I4"
    assert not vendor["FPGA_PASS"] and not vendor["executed_vendor_flow"]
    assert not rtl["candidate_adopted"] and not rtl["full_machine_milestone"]
    for key in ["physical_measurements", "hardware_accessed", "target_execution", "actual_FPGA_device_execution", "vendor_Efinity_fit_or_STA", "manufacturing_ready", "production_ready", "routing_or_CAD_modified"]:
        assert not rtl[key]

    by_case = {row["case"]: row for row in host["observations"]}
    assert len(host["observations"]) == len(by_case) == 6
    assert set(by_case) == {"denied", "qualification", "crc", "encoder", "mpg", "IS1"}
    assert sum(row["checks"] for row in by_case.values()) == 124
    assert by_case["denied"]["status"] == "PASS" and not by_case["denied"]["snapshots"]
    for case, row in by_case.items():
        assert row["status"] == "PASS" and not row["full_requested_milestone_complete"]
        assert not row["actual_motion_controller_trajectory"]
        if case == "denied":
            continue
        assert row["actual_LinuxCNC_HAL_scheduler"]
        assert (row["HAL_command_pins"], row["HAL_feedback_pins"], row["HAL_encoder_pins"]) == (12, 12, 4)
        for observed in row["snapshots"]:
            assert observed["host-cycles"] > 0 and observed["state"] == 10 and observed["fault"]
            assert observed["command"] == [(index + 1) * .125 for index in range(12)]
            for key in ["discovered", "feedback-valid", "arm-frames", "update-frames", "configure-frames", "rtl-enabled-mask", "rtl-armed-mask", "rtl-session", "rtl-authority", "malformed-transactions"]:
                assert not observed[key], (case, key)
            assert observed["step_rises"] == [0] * 12
    nominal = by_case["qualification"]["snapshots"]
    assert len(nominal) == 4
    assert [(row["spi-transactions"], row["cap3-frames"], row["fault-code"]) for row in nominal] == [(128,64,11), (128,64,11), (256,128,11), (256,128,11)]
    assert all((row["supported-channels"],row["installed-channels"],row["supported-encoders"],row["installed-encoders"]) == (12,0,4,0) for row in nominal)
    for case, expected in [("crc",(2,1,0)),("encoder",(10,0,0)),("mpg",(10,0,0)),("IS1",(3,2,1))]:
        row = by_case[case]["snapshots"][0]
        assert (row["fault-code"], row["spi-transactions"], row["cap3-frames"]) == expected
    executions = {row["stage"]: row for row in host["executions"]}
    denied, positive = executions["HAL-denied"], executions["HAL-qualification"]
    assert denied["command"][-2] == positive["command"][-2]
    assert denied["exit_code"] == positive["exit_code"] == 0
    qualification_log = QUAL / "host/run-r06/HAL-commands-qualification.log"
    assert "Using POSIX non-realtime" in qualification_log.read_text(encoding="utf8")
    profile = ROOT / "reports/cnc3-is2-profile-20261002/profile-candidate-r02/rtl/cnc3_motion_spi.v"
    assert re.search(r"localparam\s+IS2_PROFILE_COMPLETE\s*=\s*1'b0\s*;", profile.read_text(encoding="utf8"))

    boundary = QUAL / "rtl/explicit-boundaries-r02"
    proof = read(boundary / "receipt.json")
    assert proof["status"] == "PASS" and proof["inputs_unchanged"]
    for name, digest in proof["source_sha256"].items():
        verify(absolute(name), digest)
    for name, digest in proof["copied_input_sha256"].items():
        verify(boundary / "inputs" / name, digest)
    expected_cases = {"DO_UPDATE", "PROBE_UPDATE", "INDEX_UPDATE", "PWM_UPDATE", "IO_ENABLE", "IO_WRITE"} | {"alarm_M" + str(i) for i in range(12)} | {"encoder_E" + str(i) for i in range(4)}
    assert len(proof["cases"]) == 22 and {row["case"] for row in proof["cases"]} == expected_cases
    assert sum(row["checks"] for row in proof["cases"]) == 684
    # Parse the actual final wire responses independently of stored decoded JSON.
    codec_path = boundary / "inputs/protocol_v3.py"
    spec = importlib.util.spec_from_file_location("independent_review_codec", codec_path)
    codec = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(codec)
    codec._SPEC = codec.Spec(str(boundary / "inputs/protocol.json"))
    decoded = {}
    for case in proof["cases"]:
        path = boundary / (case["case"] + "-responses.txt")
        final = next(row for row in path.read_text(encoding="utf8").splitlines() if row.startswith("boundary_feedback "))
        _, size, raw = final.split()
        data = bytes.fromhex(raw)
        assert len(data) == int(size) == 176
        response = codec.decode_response("CS_FB", data)
        assert response["armed_mask"] == response["pos_continuity"] == response["index_armed_mask"] == 0
        assert response["fault_word"] and response["din_age"] == response["ain_age"] == 255 and not response["ain_status"]
        if case["case"].startswith("alarm_"):
            assert response["alarm_levels"] & (1 << case["channel"])
            assert response["alarm_trip_latched"] & (1 << case["channel"])
        if case["case"].startswith("encoder_"):
            assert not response["encoder_valid_mask"] & (1 << case["channel"])
            assert response["encoder_fault_mask"] & (1 << case["channel"])
        decoded[case["case"]] = {key: response[key] for key in ["fault_word", "armed_mask", "din_age", "ain_age", "index_armed_mask"]}
    preserved = read(HERE / "preservation-r01.json")
    assert preserved["status"] == "PASS" and all(not group["differences"] for group in preserved["groups"].values())
    controls = read(HERE / "module-install-corrected-controls.json")
    assert controls["status"] == "PASS" and len(controls["cases"]) == 4
    for name, digest in controls["source_sha256"].items():
        verify(absolute(name), digest)
    negative = read(HERE / "module-install-negative-control.json")
    assert negative["status"] == "REPRODUCED" and not negative["rootfs_modules_accessed"]
    for name, digest in negative["source_sha256"].items():
        verify(QUAL / "host/run-r05" / absolute(name).name, digest)
    readmes = [QUAL / "README.md", QUAL / "host/README.md", QUAL / "rtl/README.md", HERE / "README.md"]
    documents = {str(path.relative_to(ROOT)): sha(path) for path in readmes}
    assert "physical-pin monitors" not in readmes[1].read_text(encoding="utf8")
    result = {
        "status": "INDEPENDENT_REVIEW_PASS_WITHIN_RECORDED_SCOPE",
        "utc": datetime.now(timezone.utc).isoformat(),
        "reviewer": "/root/evidence_storage_audit",
        "canonical_artifact_sha256": {str(path.relative_to(ROOT)): sha(path) for path in [host_path, rtl_path, vendor_path, gaps_path, QUAL / "preservation-final.json"]},
        "documents_reviewed_sha256": documents,
        "rechecked_source_and_evidence_sha256": checked,
        "unique_files_rechecked": len(checked),
        "scope": "Read-only source/evidence review and fresh independent wire-response decoding; no rerun of HAL, target execution, paid provider or device transport",
        "observed_HAL_refusal_cases": 6,
        "recorded_HAL_assertions": 124,
        "same_IS2_module_denied_without_opt_in_and_successfully_scheduled_with_opt_in": True,
        "actual_POSIX_non_realtime_HAL_callbacks": True,
        "actual_LinuxCNC_motion_controller_trajectory": False,
        "complete_continuous_12_4_DI_DO_probe_milestone": False,
        "CAP3_complete_guard_unchanged_false": True,
        "unsupported_IO_and_alarm_encoder_boundary_wire_responses_independently_decoded": decoded,
        "independent_preservation_receipt_sha256": sha(HERE / "preservation-r01.json"),
        "corrected_inert_cleanup_controls_sha256": sha(HERE / "module-install-corrected-controls.json"),
        "historical_cleanup_negative_control_sha256": sha(HERE / "module-install-negative-control.json"),
        "corrected_cleanup_control_script_sha256": sha(HERE / "probe_atomic_module_install.py"),
        "review_verifier_sha256": sha(Path(__file__)),
        "physical_evidence": False,
        "FPGA_PASS": False,
        "adoption_or_manufacturing_readiness_promoted": False,
        "findings": [{"issue": "Partial temporary-module installation skipped cleanup in previous runner", "status": "CORRECTED_AND_INDEPENDENTLY_VERIFIED", "before_control": "module-install-negative-control.json", "after_controls": "module-install-corrected-controls.json"}, {"issue": "Host report called simulated RTL pin monitors physical-pin monitors", "status": "CORRECTED_WORDING"}],
    }
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("x", encoding="utf8") as handle:
        json.dump(result, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"status": result["status"], "unique_files_rechecked": len(checked), "wire_cases": len(decoded), "receipt": str(out), "sha256": sha(out)}))


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    main(parser.parse_args().out.resolve())
