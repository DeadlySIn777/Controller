"""Seal one exclusive current-source Motion X12 OS overlay evidence receipt."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
HERE = Path(__file__).resolve().parent
sha = lambda path: hashlib.sha256(Path(path).read_bytes()).hexdigest()


def verify(mapping, directory):
    for name, expected in mapping.items():
        assert sha(directory / name) == expected, name
    return len(mapping)


def main():
    parser = argparse.ArgumentParser(); parser.add_argument("--run", default="run-r01")
    args = parser.parse_args(); directory = HERE / args.run
    assert directory.parent == HERE and directory.is_dir()
    raw = json.loads((directory / "receipt.json").read_text())
    assert raw["status"] == "PASS_WITHIN_OFFLINE_OVERLAY_SCOPE"
    assert raw["source_inputs_unchanged"] and raw["protected_runtime_sources_unchanged"]
    bindings = verify(raw["source_sha256"], ROOT)
    bindings += verify(raw["protected_runtime_source_sha256"], ROOT)
    bindings += verify(raw["runner_sha256"], HERE)
    bindings += verify(raw["artifact_sha256"], directory)
    for execution in raw["executions"]:
        assert sha(directory / (execution["stage"] + ".log")) == execution["log_sha256"]
        if execution["expected_exit_code"] is not None:
            assert execution["exit_code"] == execution["expected_exit_code"]
        bindings += 1
    observations = raw["linux_observations"]
    assert observations["status"] == "PASS" and len(observations["checks"]) == 17
    assert all(check["passed"] for check in observations["checks"])
    assert raw["adversarial_tests"] == 25
    assert sha(directory / "image-a/controller-overlay.tar") == sha(directory / "image-b/controller-overlay.tar")
    assert raw["actual_physical_boot"] is False and raw["services_installed_or_enabled"] is False
    probe_path = HERE / "user-unit-probe-r01/receipt.json"
    probe = json.loads(probe_path.read_text())
    assert probe["status"] == "PASS_USER_RECOVERY_UNIT_SYNTAX" and probe["units_unchanged"]
    assert probe["base_receipt_sha256"] == sha(directory / "receipt.json")
    assert probe["runner_sha256"] == sha(HERE / "probe_user_units.py")
    bindings += verify(probe["staged_user_unit_sha256"], directory)
    for execution in probe["executions"]:
        assert execution["exit_code"] == 0
        assert sha(HERE / "user-unit-probe-r01" / (execution["stage"] + ".log")) == execution["log_sha256"]
        bindings += 1
    lifecycle_path = ROOT / "reports/appliance-os-20261004/review/lifecycle-r01/receipt.json"
    lifecycle = json.loads(lifecycle_path.read_text())
    assert lifecycle["status"] == "SCOPED_PASS" and len(lifecycle["checks"]) == 27
    assert all(check["passed"] for check in lifecycle["checks"])
    assert lifecycle["source_manifest_sha256"] == sha(directory / "image-a/rootfs/usr/share/controller/image-manifest.json")
    assert lifecycle["fixture_sha256"] == sha(directory / "workspace/setup.json")
    lifecycle_harness = ROOT / "reports/appliance-os-20261004/review/lifecycle_control.py"
    assert lifecycle["harness_sha256"] == sha(lifecycle_harness)
    references = [directory / "receipt.json", HERE / "README.md", ROOT / "controller_os/README.md",
                  Path(__file__), ROOT / "reports/appliance-os-20261004/service/run-r04/receipt.json",
                  ROOT / "reports/appliance-os-20261004/service/receipt.json",
                  probe_path, HERE / "probe_user_units.py", lifecycle_path, lifecycle_harness]
    artifact = {path.relative_to(ROOT).as_posix(): sha(path) for path in references}
    value = {"schema_version": 1, "kind": "motion_x12_development_appliance_overlay_evidence",
        "utc": datetime.now(timezone.utc).isoformat(), "status": "PASS_WITHIN_OFFLINE_OVERLAY_SCOPE",
        "scope": "Deterministic branded application overlay, read-only non-root startup and local HTTP, staged unit syntax/lifecycle contracts; no bootable appliance or actual motion continuity",
        "execution_path": directory.relative_to(ROOT).as_posix(),
        "source_sha256": raw["source_sha256"], "runner_sha256": raw["runner_sha256"],
        "protected_runtime_source_sha256": raw["protected_runtime_source_sha256"],
        "protected_runtime_sources_unchanged": True, "hash_bindings_rechecked": bindings,
        "execution_artifact_sha256": raw["artifact_sha256"], "artifact_sha256": artifact,
        "adversarial_tests": 25, "actual_nonroot_Linux_checks": 17,
        "systemd_system_unit_syntax_checks": 5,
        "initial_systemd_user_recovery_syntax_status": raw["systemd_user_recovery_syntax_status"],
        "systemd_user_recovery_syntax_status": probe["status"], "systemd_user_recovery_unit_syntax_checks": 2,
        "independent_process_lifecycle_checks": 27,
        "kiosk_browser_executable_present": raw["kiosk_browser_executable_present"],
        "kiosk_browser_qualified": False, "actual_systemd_unit_startup_executed": False,
        "kiosk_browser_or_splash_renderer_executed": False,
        "linux_compressed_packages": observations["preflight"]["compressed_packages"],
        "deterministic_overlay": raw["deterministic_overlay"],
        "implemented_corrections": ["Every application launch rechecks image/settings via non-ignored ExecStartPre",
                                  "Browser and application use explicit total-three-start limits with manual recovery",
                                  "User-only kiosk failure graph never controls application or motion runtime",
                                  "Kiosk opens guarded /launch to honor startup-page preference",
                                  "Recovery reports unobserved output state as unknown and never restores settings",
                                  "Local inert Motion X12/GarciaMech brand/recovery assets plus unapplied boot/update recipe",
                                  "Explicit three-module appliance service shipping closure without preferences/data"],
        "simulation_only": True, "physical_authority": False, "motion_authorized": False,
        "physical_commissioning_complete": False, "runtime_continuity_measured": False,
        "runtime_unit_installed": False, "bootable_image_qualified": False, "signed_release": False,
        "cold_boot_seconds": None, "physical_boot_executed": False,
        "bootloader_or_partition_modified": False, "services_installed_or_enabled": False,
        "desktop_or_network_config_modified": False, "physical_device_connections": 0, "paid_api_calls": 0,
        "remaining_requirements": ["Exact approved compute/carrier/base/kernel/device-tree/boot/graphics selection",
                                   "Installed qualified splash renderer/browser and actual system/user service execution",
                                   "Independent qualified motion supervisor and loaded continuity/deadline tests",
                                   "Measured startup/touch/frame pacing/storage/thermal behavior",
                                   "Authenticated signed updates, measured slot/recovery headroom, interrupted-power recovery",
                                   "Physical commissioning and manufacturing gates"]}
    with (HERE / "receipt.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True); stream.write("\n")
    print(json.dumps({"receipt_sha256": sha(HERE / "receipt.json"), "hash_bindings_rechecked": bindings}))


if __name__ == "__main__":
    main()
