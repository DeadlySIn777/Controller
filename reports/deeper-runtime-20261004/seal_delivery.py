"""Final read-only source/preservation check and new delivery-document ledger."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[2]
REPORT = Path(__file__).resolve().parent


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    gap_path = REPORT / "gaps.json"
    gaps = json.loads(gap_path.read_text())
    if gaps["status"] != "SCOPED_SOFTWARE_AND_SIMULATION_PASS":
        raise ValueError("Canonical gap recheck did not pass")
    for name, expected in gaps["source_sha256"].items():
        if sha(ROOT / name) != expected:
            raise ValueError("Source drift: " + name)
    for name, expected in gaps["evidence"].items():
        if sha(ROOT / name) != expected["sha256"]:
            raise ValueError("Evidence drift: " + name)
    baseline_path = ROOT / "reports/rev-a-integration-20261004/baseline.json"
    baseline = json.loads(baseline_path.read_text())
    preservation = {}
    for group in ("feature_sha256", "protected_source_sha256", "external_archive_sha256", "existing_settings_sha256", "regression_test_sha256"):
        folder = Path("C:/Users/Gluis/claude-worktrees/controller-interface-spec") if group == "external_archive_sha256" else ROOT
        for name, expected in baseline[group].items():
            if sha(folder / name) != expected:
                raise ValueError("Preserved baseline drift: " + name)
        preservation[group] = len(baseline[group])
    names = ["PROJECT_MEMORY.md", "docs/BUILD_PLAN.md", "docs/PLATFORM_ROADMAP.md",
             "docs/REV_A_QUALIFICATION.md", "docs/CONTROLLER_OS.md", "reports/ENGINEERING_STATUS.md",
             "reports/deeper-runtime-20261004/README.md", "reports/deeper-runtime-20261004/gaps.json",
             "reports/deeper-runtime-20261004/preservation-r03.json", "reports/deeper-runtime-20261004/finalize_report.py",
             "reports/deeper-runtime-20261004/seal_delivery.py",
             "reports/os-experience-20261004/README.md", "reports/os-experience-20261004/capture_ledger.py",
             "reports/os-experience-20261004/presentation-r01/home.jpg",
             "reports/os-experience-20261004/browser-r03/receipt.json"]
    link_checks = 0
    for name in ("reports/deeper-runtime-20261004/README.md", "reports/os-experience-20261004/README.md", "docs/CONTROLLER_OS.md"):
        page = ROOT / name
        for link in re.findall(r"\[[^\]]*\]\(([^)]+)\)", page.read_text(encoding="utf-8")):
            if "://" in link or link.startswith("#"):
                continue
            if not (page.parent / link.split("#")[0]).is_file():
                raise ValueError("Missing local report link: " + link)
            link_checks += 1
    data = {"schema_version": 1, "utc": datetime.now(timezone.utc).isoformat(),
            "status": "PASS_WITHIN_DOCUMENTED_SOURCE_AND_DELIVERY_SCOPE",
            "source_files_rechecked": len(gaps["source_sha256"]), "evidence_receipts_rechecked": len(gaps["evidence"]),
            "preserved_baseline_files": preservation, "local_report_links_verified": link_checks,
            "artifacts_sha256": {name: sha(ROOT / name) for name in names},
            "scope": "Hash and report closure check; no additional test executions",
            "bootable_image_qualified": False, "physical_authority": False, "physical_measurements": 0,
            "manufacturing_ready": False, "full_requested_milestone_complete": False,
            "routing_modified": False, "paid_api_calls": 0}
    with (REPORT / "delivery.json").open("x", encoding="utf-8") as stream:
        json.dump(data, stream, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({key: data[key] for key in ("status", "source_files_rechecked", "evidence_receipts_rechecked", "local_report_links_verified")}))


if __name__ == "__main__":
    main()
