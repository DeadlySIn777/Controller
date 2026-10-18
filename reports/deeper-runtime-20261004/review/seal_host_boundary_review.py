"""Read-only final SIM2 host evidence check, then one new review receipt."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "reports/deeper-runtime-20261004"
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(mapping, base=ROOT):
    for name, expected in mapping.items():
        assert sha(base / name) == expected, name
    return len(mapping)


def main():
    host = BASE / "host"
    canonical = json.loads((host / "receipt.json").read_text())
    assert canonical["status"] == "PASS" and canonical["full_requested_milestone_complete"] is False
    checks = verify(canonical["source_sha256"])
    checks += verify(canonical["artifact_sha256"], host)
    assert sha(ROOT / "cnc3_runtime/README.md") == canonical["runtime_readme_sha256"]
    runs = []
    for selected in canonical["runs"]:
        directory = host / selected["run"]
        raw = json.loads((directory / "receipt.json").read_text())
        assert raw["status"] == "PASS" and raw["source_inputs_unchanged"] is True
        assert raw["source_sha256"] == canonical["source_sha256"]
        checks += verify(raw["source_sha256"], directory / "source")
        assert raw["settings_preserved"] and raw["installed_existing_rootfs_modules_preserved"]
        assert sha(directory / "configuration/setup.json") == raw["settings_sha256"]
        before = json.loads((directory / "installed-modules-before.json").read_text())
        after = json.loads((directory / "installed-modules-after.json").read_text())
        assert before == after and len(before) == 183
        for execution in raw["executions"]:
            assert execution["exit_code"] == 0
            assert sha(directory / (execution["stage"] + ".log")) == execution["log_sha256"]
            checks += 1
        observed = json.loads((directory / "linuxcnc.json").read_text())
        assert observed == raw["observations"] and observed["status"] == "PASS"
        assert len(observed["checks"]) == selected["actual_LinuxCNC_NML_checks"]
        assert all(check["status"] == "PASS" for check in observed["checks"])
        assert observed["configuration_binding"] == selected["configuration_binding"]
        assert selected["motion_session_after"] != selected["motion_session_before"]
        assert selected["provider_sequence_after"] > selected["provider_sequence_before"]
        assert selected["deliberate_inhibited_unhomed_restart"] is True
        runs.append({"path": directory.relative_to(ROOT).as_posix(),
                     "receipt_sha256": sha(directory / "receipt.json"),
                     "source_count": len(raw["source_sha256"]),
                     "observed_checks": len(observed["checks"]),
                     "active_joints": selected["active_joints"], "fitted_channels": 12,
                     "saved_binding": selected["configuration_binding"],
                     "copied_sources_match_current": True, "recorded_183_modules_preserved": True})
    references = ["host/receipt.json", "host/README.md", "providers/receipt-r03.json",
                  "review/setup-review-r01.json", "review/event-session-control-r02/receipt.json",
                  "review/final-runtime-r01/receipt.json", "review/host-boundary-review-r01.md",
                  "review/seal_host_boundary_review.py"]
    artifacts = {"reports/deeper-runtime-20261004/" + name: sha(BASE / name) for name in references}
    output = BASE / "review/host-boundary-review-r01.json"
    value = {"schema_version": 1, "kind": "independent_final_SIM2_host_boundary_review",
        "utc": datetime.now(timezone.utc).isoformat(), "status": "SCOPED_PASS",
        "reviewer": "evidence_storage_audit", "remaining_actionable_findings": [],
        "current_sources_edited": False, "runtime_tests_repeated": False,
        "hash_bindings_rechecked": checks, "source_sha256": canonical["source_sha256"],
        "canonical_execution_artifact_sha256": canonical["artifact_sha256"],
        "execution_artifact_base": "reports/deeper-runtime-20261004/host",
        "reviewed_runs": runs, "artifact_sha256": artifacts,
        "reviewed_boundaries": ["Explicit SIM opt-in and complete-source/saved-binding preflight",
                                "Strict C manifest types/masks/timing and authored encoder mapping",
                                "Real NML FREE planners -> HAL -> C driver -> shifted RTL SPI -> independent mechanics",
                                "Local period/rate/velocity/DDS limits; first fault latched",
                                "Stopped new motion session preserves provider lineage and historical events",
                                "Current successful SYNC clears per-session event ACK/dedup only after command",
                                "Atomic unique module publication and recorded existing-module preservation",
                                "Simulation derivative and historical/archive/physical boundaries"],
        "scope_caveats": ["Positive execution belongs to expert host agent; this reviewer rechecked recorded evidence",
                          "Live module inventory independently checked by hardware reviewer, not reread here",
                          "Historical event regression uses its earlier exact C source; final source inspected for retained fix",
                          "No combined atomic NML/HAL-command snapshot or customer Cartesian/G-code qualification",
                          "Short ideal low-rate trajectories and virtual HAL sensors do not qualify physical links or deadlines"],
        "physical_authority": False, "production_profile_complete": False,
        "physical_measurements": 0, "hardware_connections": 0, "paid_calls": 0,
        "FPGA_vendor_fit": False, "signed_release": False, "manufacturing_ready": False,
        "full_requested_milestone_complete": False}
    with output.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write("\n")
    print(json.dumps({"receipt_sha256": sha(output), "hash_bindings_rechecked": checks}))


if __name__ == "__main__":
    main()
