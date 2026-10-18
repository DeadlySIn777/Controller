"""Verify this appliance pass's exact existing receipts without rerunning tests."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from controller_os.image import application_sources, verify_image

OUT = Path(__file__).resolve().parent
BINDINGS = {}


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def load(name):
    return json.loads((OUT / name).read_text())


def bind(path, expected):
    path = path.resolve()
    assert path.is_relative_to(ROOT), path
    name = path.relative_to(ROOT).as_posix()
    assert path.is_file() and sha(path) == expected, name
    assert name not in BINDINGS or BINDINGS[name] == expected, name
    BINDINGS[name] = expected


def mapping(values, base=ROOT):
    for name, digest in values.items():
        bind(base / name, digest)


def write(name, value):
    with (OUT / name).open("x", encoding="utf-8") as stream:
        json.dump(value, stream, indent=2, allow_nan=False)
        stream.write("\n")


def main():
    baseline = load("review/baseline-r01/receipt.json")
    mapping(baseline["current_runtime_71"])
    mapping(baseline["base_controller_config"])
    assert len(baseline["current_runtime_71"]) == 71
    assert len(baseline["base_controller_config"]) == 24
    os_receipt = load("os/receipt.json")
    service = load("service/receipt.json")
    review = load("review/final-r01/receipt.json")
    browser = load("browser-r01/receipt.json")
    shell = load("http-r04/receipt.json")
    docs = load("docs-r01/receipt.json")
    for key in ("source_sha256", "protected_runtime_source_sha256", "artifact_sha256"):
        mapping(os_receipt[key])
    mapping(os_receipt["execution_artifact_sha256"], OUT / "os/run-r01")
    mapping(os_receipt["runner_sha256"], OUT / "os/run-r01")
    for key in ("source_sha256", "artifact_sha256", "protected_source_and_setting_sha256"):
        mapping(service[key])
    mapping(review["reviewed_current_sources"])
    mapping(review["artifacts"])
    mapping(browser["source_sha256"])
    mapping(browser["artifacts_sha256"], OUT / "browser-r01")
    bind(OUT / "capture_browser.py", browser["runner_sha256"])
    mapping(shell["source_sha256"])
    mapping(shell["source_sha256_after"])
    bind(OUT / "http-r04/tests.log", shell["log_sha256"])
    mapping(docs["canonical_receipt_sha256"])
    mapping(docs["protected_source_and_setting_sha256"])
    for name, row in docs["documents"].items():
        bind(ROOT / name, row["after_sha256"])
        bind(ROOT / row["before_path"], row["before_sha256"])
        assert row["original_bytes_recovered_exactly"]
    current = {name: hashlib.sha256(raw).hexdigest() for name, raw in application_sources(ROOT).items()}
    assert current == browser["source_sha256"] and len(current) == 48
    for label in ("image-a", "image-b"):
        rootfs = OUT / "os/run-r01" / label / "rootfs"
        verified = verify_image(rootfs, allow_development=True, exact_overlay=True)
        assert verified["manifest_sha256"] == os_receipt["deterministic_overlay"]["manifest_sha256"]
        assert verified["source_sha256"] == current and not verified["physical_authority"]
        for name, digest in current.items():
            bind(rootfs / "usr/lib/controller/app" / name, digest)
    assert shell["status"] == "PASS" and shell["tests_run"] == 5 and shell["source_stable"]
    assert service["status"] == "SCOPED_PASS" and service["service_methods"] == 29
    assert service["actual_HTTP_check_count"] == 23
    assert review["status"] == "SCOPED_PASS" and not review["remaining_actionable_findings"]
    assert len(browser["observations"]) == 20 and all(row["passed"] for row in browser["observations"])
    controls = load("browser-r01/artifact-controls.json")
    assert controls["status"] == "PASS" and controls["protected_files_unchanged"]
    assert controls["paid_requests"] == 0 and controls["package_integrity_verified"]
    bind(OUT / "check_browser_artifacts.py", controls["runner_sha256"])
    selected = ("review/baseline-r01/receipt.json", "os/receipt.json", "service/receipt.json",
                "review/final-r01/receipt.json", "review/lifecycle-r01/receipt.json",
                "browser-r01/receipt.json", "browser-r01/artifact-controls.json",
                "http-r04/receipt.json", "docs-r01/receipt.json")
    receipts = {name: sha(OUT / name) for name in selected}
    for name, digest in receipts.items():
        bind(OUT / name, digest)
    local_links = []
    for target in re.findall(r"!?\[[^\]]*\]\(([^)]+)\)", (OUT / "README.md").read_text()):
        if "://" in target or target == "delivery-r02.json":
            continue
        path = (OUT / target.split("#", 1)[0]).resolve()
        assert path.is_file(), target
        local_links.append(target)
        bind(path, sha(path))
    bind(OUT / "README.md", sha(OUT / "README.md"))
    bind(Path(__file__), sha(Path(__file__)))
    qualification = {"schema_version": 1, "software_appliance": "PASS_WITHIN_DECLARED_SCOPE",
                     "deterministic_application_overlay": "PASS", "physical_measurements": 0,
                     "paid_api_calls": 0, "routing_modified_by_this_pass": False,
                     "motion_runtime_modified": False, "motion_continuity_qualified": False,
                     "bootable_target_image": "BLOCKED", "signed_release": "BLOCKED",
                     "fullscreen_kiosk_executed": False, "cold_boot_seconds": None,
                     "touch_response_ms": None, "frame_pacing_measured": False,
                     "manufacturing_ready": False, "physical_commissioning_complete": False,
                     "open_gates": ["Exact target compute/carrier/kernel/graphics/touch/transport profile",
                                    "Complete pinned preinstalled base including Chromium and Zstd backend",
                                    "Branded quiet boot and fullscreen kiosk execution on target",
                                    "Protected settings/recovery partitions, signed updates and power interruption",
                                    "Loaded boot/touch/frame/RAM/thermal and RT-motion measurements",
                                    "Real runtime continuity across browser/application failure",
                                    "Efinity device fit/place/route/static timing and ROOT105 completion",
                                    "Physical board bring-up and electrical/analog/watchdog/power validation"]}
    assert qualification == load("qualification.json")
    bind(OUT / "qualification.json", sha(OUT / "qualification.json"))
    result = {"schema_version": 1, "utc": datetime.now(timezone.utc).isoformat(),
              "status": "PASS_WITHIN_APPLIANCE_SOFTWARE_AND_OVERLAY_SCOPE",
              "qualification": qualification, "application_source_sha256": current,
              "protected_motion_source_count": 71, "protected_configuration_source_count": 24,
              "receipts_sha256": receipts, "bound_files_rechecked": len(BINDINGS),
              "source_artifact_and_document_sha256": dict(sorted(BINDINGS.items())),
              "local_report_links_checked": local_links,
              "counts_are_not_summed_as_unique_tests": True,
              "actual_browser_observations": 20, "service_test_methods": 29,
              "service_HTTP_checks": 23, "shell_contract_tests": 5,
              "OS_tests": 25, "actual_nonroot_Linux_checks": 17,
              "unit_parser_checks": {"system": 5, "user_recovery": 2},
              "independent_nonmotion_lifecycle_assertions": 27,
              "preview": "http://127.0.0.1:8771/", "existing_8770_preview_edited": False,
              "historical_receipts_restamped": False,
              "supersedes_root_delivery": {"path": "delivery.json", "sha256": sha(OUT / "delivery.json"),
                                          "reason": "Corrected root-summary tar-versus-payload wording; execution/image/source results unchanged"},
              "retained_previous_summary": {name: sha(OUT / "final-r01" / name)
                                            for name in ("README.md", "seal_delivery.py", "delivery.json")}}
    write("delivery-r02.json", result)
    print(json.dumps({"status": result["status"], "bound_files_rechecked": len(BINDINGS),
                      "application_files": len(current), "receipts": len(receipts),
                      "local_links": len(local_links)}))


if __name__ == "__main__":
    main()
