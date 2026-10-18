"""Recheck current evidence and previously existing bytes without executing devices."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
EXTERNAL = Path("C:/Users/Gluis/claude-worktrees/controller-interface-spec")
REPORT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def read(name):
    return json.loads((ROOT / name).read_text(encoding="utf-8"))


def write(path, data):
    with path.open("x", encoding="utf-8") as file:
        json.dump(data, file, indent=2, allow_nan=False)
        file.write("\n")


def main():
    baseline_path = ROOT / "reports/rev-a-integration-20261004/baseline.json"
    baseline = json.loads(baseline_path.read_text())
    groups = {}
    for group in ("feature_sha256", "protected_source_sha256", "external_archive_sha256", "existing_settings_sha256", "regression_test_sha256"):
        folder = EXTERNAL if group == "external_archive_sha256" else ROOT
        changes = []
        for name, expected in baseline[group].items():
            path = folder / name
            actual = sha(path) if path.is_file() else None
            if actual != expected:
                changes.append({"path": name, "expected": expected, "actual": actual})
        groups[group] = {"checked": len(baseline[group]), "unchanged": len(baseline[group]) - len(changes), "changes": changes}
    preservation = {"schema_version": 1, "utc": datetime.now(timezone.utc).isoformat(),
        "scope": "Previously existing bytes only; new runtime, shell and OS sources are separate additions",
        "baseline_sha256": sha(baseline_path), "groups": groups,
        "status": "PASS" if not any(row["changes"] for row in groups.values()) else "FAIL",
        "physical_measurements": 0, "device_connections": 0, "paid_api_calls": 0}
    evidence_paths = [
        "reports/deeper-runtime-20261004/setup/run-r06/receipt.json",
        "reports/deeper-runtime-20261004/providers/receipt-r03.json",
        "reports/deeper-runtime-20261004/rtl/receipt.json",
        "reports/deeper-runtime-20261004/host/nml-r07/receipt.json",
        "reports/deeper-runtime-20261004/host/nml-eight-r02/receipt.json",
        "reports/deeper-runtime-20261004/host/receipt.json",
        "reports/deeper-runtime-20261004/host/sanitizer-r02/receipt.json",
        "reports/deeper-runtime-20261004/review/final-runtime-r01/receipt.json",
        "reports/deeper-runtime-20261004/review/source-closure-control-r02.json",
        "reports/deeper-runtime-20261004/rtl/shell-review-r02/receipt.json",
        "reports/os-experience-20261004/http-r03/receipt.json",
        "reports/os-experience-20261004/os/run-r03/receipt.json",
        "reports/os-experience-20261004/os/receipt.json",
        "reports/os-experience-20261004/browser-r03/receipt.json",
        "reports/os-experience-20261004/review/shell-review-r01.json",
        "reports/deeper-runtime-20261004/review/host-boundary-review-r01.json"]
    sources, conflicts = {}, []
    receipts = {}
    for name in evidence_paths:
        value = read(name)
        receipts[name] = {"sha256": sha(ROOT / name), "status": value.get("status"), "kind": value.get("kind", value.get("scope"))}
        inventory = value.get("source_sha256", {})
        if "source_inventory" in value:
            inventory = {row["path"]: row["sha256"] for row in value["source_inventory"]}
        for source, expected in inventory.items():
            path = Path(source)
            if not path.is_absolute():
                path = ROOT / source
            key = path.relative_to(ROOT).as_posix() if path.is_relative_to(ROOT) else str(path)
            if key in sources and sources[key] != expected:
                conflicts.append({"source": key, "first": sources[key], "later": expected, "receipt": name})
            sources[key] = expected
    mismatches = [{"source": name, "expected": expected, "actual": sha(ROOT / name) if (ROOT / name).is_file() else None}
                  for name, expected in sources.items() if not (ROOT / name).is_file() or sha(ROOT / name) != expected]
    nml = []
    for motors, path in ((12, "reports/deeper-runtime-20261004/host/nml-r07/linuxcnc.json"), (8, "reports/deeper-runtime-20261004/host/nml-eight-r02/linuxcnc.json")):
        value = read(path)
        if value["status"] != "PASS" or not all(check["status"] == "PASS" for check in value["checks"]):
            raise ValueError("A canonical LinuxCNC run failed")
        nml.append({"active_joints": motors, "fitted_channels": value["fitted_channels"], "checks": len(value["checks"]),
                    "receipt": path, "sha256": sha(ROOT / path), "scope": value["scope"]})
    write(REPORT / "preservation-r03.json", preservation)
    gaps = {"schema_version": 1, "utc": datetime.now(timezone.utc).isoformat(),
        "status": "SCOPED_SOFTWARE_AND_SIMULATION_PASS" if preservation["status"] == "PASS" and not mismatches and not conflicts else "EVIDENCE_RECHECK_FAILED",
        "evidence": receipts, "source_sha256": sources, "source_mismatches": mismatches, "source_conflicts": conflicts,
        "actual_linuxcnc_runs": nml,
        "software": {"status": "PASS_WITHIN_DECLARED_SCOPE", "configuration_binding": "full reviewed store/epoch/revision/generation/configuration/draft digests",
                     "runtime_identity": "explicit disconnected SIM2; frozen 96/176 byte transport", "os_scope": "application overlay and local shell, not bootable base image"},
        "host_sanitizer": {"status": "PASS", "scope": "Actual standalone C driver, serial SPI, compiled RTL and independent virtual plant; ASan, UBSan and leak detection",
                           "driver_spi_assertions": 374, "compiled_manifest_controls": 18, "full_linuxcnc_process_sanitized": False},
        "simulation": {"status": "PASS_WITHIN_FREE_JOINT_SCOPE", "cartesian_machining_qualified": False, "physical_homing_qualified": False,
                       "motion_and_io_model": "independent STEP/DIR mechanics, 4 ABZ, 24 DI, 16 DO, 2 probes, virtual alarms/limits/watchdogs",
                       "cross_nml_hal_snapshot_atomic": False, "loaded_realtime_deadlines_qualified": False},
        "fpga": {"status": "BLOCKED", "generic_unified_sim2": {"EFX_LUT4": 34493, "EFX_ADD": 7776, "EFX_FF": 9900, "EFX_RAM5K": 64},
                 "vendor_fit_timing_demonstrated": False, "serialized_ram_candidate_adopted": False,
                 "blockers": ["Current functional mapping exceeds the coarse T20 resource screen", "Efinity installation/entitlement/adopted target top and vendor constraints unqualified"]},
        "os_image": {"status": "DEVELOPMENT_OVERLAY_PASS_TARGET_IMAGE_BLOCKED", "signed_release": False, "bootable_target_image_qualified": False,
                     "base_kernel_bootloader_selected": False, "compressed_packages_on_retained_linux_python313": "unavailable; required base dependency remains open",
                     "target_boot_touch_frame_pacing_memory_thermal_and_rt_measured": False},
        "physical": {"status": "PHYSICAL_VALIDATION_REQUIRED", "measurements": 0,
                     "gates": ["Live physical CNC3/IOL1/acquisition and target firmware execution", "Watchdog/inhibit 20 ms, current limits, analog accuracy, thermals", "Brownout, power-fail, storage/replacement/recovery", "Real machine commissioning, homing, coordinate/kinematics validation", "Target OS boot/graphics/loaded real-time qualification"]},
        "physical_authority": False, "physical_commissioning_complete": False, "manufacturing_ready": False,
        "device_connections": 0, "paid_api_calls": 0, "routing_modified": False, "full_requested_milestone_complete": False}
    write(REPORT / "gaps.json", gaps)
    print(json.dumps({"status": gaps["status"], "sources": len(sources), "mismatches": len(mismatches), "conflicts": len(conflicts), "preservation": preservation["status"]}))
    return 0 if gaps["status"] == "SCOPED_SOFTWARE_AND_SIMULATION_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
