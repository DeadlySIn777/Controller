"""Bind current OS execution and independent shell review; never overwrite."""
import datetime
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
BASE = ROOT / "reports/os-experience-20261004"


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def read(relative):
    return json.loads((ROOT / relative).read_text(encoding="utf-8"))


def verify(mapping, base=ROOT):
    for name, expected in mapping.items():
        assert sha(base / name) == expected, name
    return len(mapping)


def write(path, value):
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2, sort_keys=True)
        stream.write("\n")


def reference(relative):
    return {"path": relative, "sha256": sha(ROOT / relative)}


def main():
    raw_path = "reports/os-experience-20261004/os/run-r03/receipt.json"
    raw = read(raw_path)
    assert raw["status"] == "PASS_WITHIN_OFFLINE_OVERLAY_SCOPE"
    assert raw["source_inputs_unchanged"] is True
    count = verify(raw["source_sha256"])
    count += verify(raw["runner_sha256"], BASE / "os")
    count += verify(raw["artifact_sha256"], BASE / "os/run-r03")
    assert len(raw["linux_observations"]["checks"]) == 15
    assert all(item["passed"] is True for item in raw["linux_observations"]["checks"])
    assert all(item["exit_code"] == 0 for item in raw["executions"])
    for item in raw["executions"]:
        assert sha(BASE / "os/run-r03" / (item["stage"] + ".log")) == item["log_sha256"]
    assert sha(BASE / "os/run-r03/image-a/controller-overlay.tar") == sha(BASE / "os/run-r03/image-b/controller-overlay.tar")
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    guards = {"simulation_only": True, "physical_authority": False,
              "motion_authorized": False, "outputs_inhibited": True,
              "physical_commissioning_complete": False, "bootable_image_qualified": False,
              "signed_release": False, "actual_physical_boot": False,
              "services_installed_or_enabled": False, "desktop_or_network_config_modified": False,
              "paid_api_calls": 0, "physical_device_connections": 0}
    os_receipt = {
        "schema_version": 1, "kind": "controller_appliance_offline_overlay_evidence",
        "utc": now, "status": "PASS_WITHIN_OFFLINE_OVERLAY_SCOPE",
        "scope": "Deterministic application/rootfs overlay, actual non-root existing-settings preflight and staged local HTTP; no bootable OS or physical qualification",
        "execution": reference(raw_path), "source_sha256": raw["source_sha256"],
        "runner_sha256": raw["runner_sha256"], "artifact_sha256": raw["artifact_sha256"],
        "execution_artifact_base": "reports/os-experience-20261004/os/run-r03",
        "current_binding_hashes_rechecked": count,
        "adversarial_python_tests": 18, "actual_linux_checks": 15,
        "systemd_system_unit_syntax_checks": 5, "linux_euid": raw["linux_observations"]["euid"],
        "deterministic_overlay": raw["deterministic_overlay"],
        "linux_compressed_packages": raw["linux_observations"]["preflight"]["compressed_packages"],
        "report": reference("reports/os-experience-20261004/os/README.md"),
        "subsystem_document": reference("controller_os/README.md"),
        "seal_runner": reference("reports/os-experience-20261004/os/seal_receipts.py"),
        "historical_runs": [reference("reports/os-experience-20261004/os/" + name + "/receipt.json") for name in ("run-r01", "run-r02")],
        "release_blockers": ["Pinned offline base image and dependency closure absent",
                             "Exact compute/carrier/boot/storage/kernel/device-tree/transport not approved",
                             "Browser/graphical session and physical display performance not qualified",
                             "Signed updates, interrupted updates and physical power-loss recovery not qualified",
                             "Loaded real-time motion and physical commissioning not measured"], **guards}
    write(BASE / "os/receipt.json", os_receipt)

    http_path = "reports/os-experience-20261004/http-r03/receipt.json"
    http = read(http_path)
    assert http["status"] == "PASS" and http["tests_run"] == 5 and http["source_stable"] is True
    shell_count = verify(http["source_sha256"])
    assert http["source_sha256"] == http["source_sha256_after"]
    assert sha(BASE / "http-r03/tests.log") == http["log_sha256"]
    js_path = "reports/deeper-runtime-20261004/rtl/shell-review-r02/receipt.json"
    js = read(js_path)
    assert js["status"] == "PASS" and js["checks"] == 6
    shell_count += verify(js["source_sha256"])
    shell_count += verify(js["artifacts"], ROOT / "reports/deeper-runtime-20261004/rtl/shell-review-r02")
    browser = BASE / "browser-r02"
    browser_evidence = {path.relative_to(ROOT).as_posix(): sha(path) for path in browser.iterdir() if path.is_file()}
    observation = json.loads((browser / "observations.json").read_text())
    assert len([item for item in observation["observations"] if "viewport" in item]) == 4
    review = {
        "schema_version": 1, "kind": "independent_controller_shell_source_evidence_review",
        "utc": now, "status": "PASS_WITHIN_REVIEWED_DEVELOPMENT_BOUNDARIES",
        "reviewer": "evidence_storage_audit", "source_edits": 0,
        "remaining_actionable_findings": [],
        "source_sha256": http["source_sha256"], "binding_hashes_rechecked": shell_count,
        "reviewed_boundaries": ["Original handler retains Host/origin/token/CSP/API contracts",
                                "Homepage checks disconnected guards and complete six-field settings binding",
                                "Service loss invalidates current evidence and aborts sibling fetch",
                                "Genuine edits use shared guarded flush; stale errors preserve answers",
                                "Exact untouched provisional fallback Home does not initialize settings or allowance",
                                "Initial route selection waits for shared context; no alternate setup state",
                                "No machine qualification or physical authority from inventory/illustration"],
        "execution_attribution": {"root_http_tests": {"checks": 5, **reference(http_path)},
                                  "hardware_reviewer_inert_Node_controls": {"checks": 6, **reference(js_path)},
                                  "root_actual_browser": {"viewports": 4, "artifact_sha256": browser_evidence,
                                                          "source_binding_limit": "Browser observation file contains no independent executable source ledger; exact files are retained alongside root HTTP and reviewer JS source-bound receipts"},
                                  "this_reviewer_actual_staged_Linux_checks": {"checks": 15, **reference(raw_path)}},
        "report": reference("reports/os-experience-20261004/review/shell-review-r01.md"),
        "seal_runner": reference("reports/os-experience-20261004/os/seal_receipts.py"),
        "limitations": ["No repeated browser exercise by this reviewer", "Inert Node VM is not layout or actual network proof",
                        "systemd syntax is not boot execution", "No OS boot, graphics performance or physical commissioning"], **guards}
    write(BASE / "review/shell-review-r01.json", review)
    print(json.dumps({"os_receipt_sha256": sha(BASE / "os/receipt.json"),
                      "shell_review_sha256": sha(BASE / "review/shell-review-r01.json"),
                      "os_hashes_rechecked": count, "shell_hashes_rechecked": shell_count}))


if __name__ == "__main__":
    main()
