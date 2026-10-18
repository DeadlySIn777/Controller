"""Record an additive documentation update without changing sealed execution evidence."""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


INSERTIONS = {
    "PROJECT_MEMORY.md": """**Latest appliance result — Motion X12/GarciaMech, 4 October 2026:** the [completed appliance pass](reports/appliance-os-20261004/README.md) adds five persistent destinations: Machine, Setup, Diagnostics, Files and Settings. Shared reviewed interface preferences, reversible interface reset/undo and deliberate service-detail presentation affect the interface only. Full machine reset remains blocked. Files validates and downloads bounded configuration/support packages from the designated folder without extraction or configuration activation. The dark/red interface has current-source browser QA; physical touchscreen performance and frame pacing remain unqualified.

The OS pass has 25 tests, 17 actual nonroot Linux checks, five system-unit and two user-recovery-unit syntax checks. Its deterministic development overlay contains 48 application files and 62 payload files. Every application launch gets fresh read-only image/settings preflight; application and optional kiosk each have a total three-start budget and separate recovery. No kiosk was launched, runtime unit installed or bootable image qualified. The tested Linux Python 3.13 base reports compressed packages unavailable. Physical boot, signed updates, loaded timing and motion continuity remain open. This pass spent $0 on APIs and preserved Claude's routing, all 71 frozen runtime inputs and all 24 original configuration sources. Earlier OS/runtime records below retain their own sources and scopes.""",
    "docs/BUILD_PLAN.md": """**Latest 4 October implementation — Motion X12 appliance pass:** [current results](../reports/appliance-os-20261004/README.md) implement persistent Machine, Setup, Diagnostics, Files and Settings destinations, reviewed shared-service interface preferences and reversible interface reset/undo. Deliberate service details are presentation only; full machine reset is blocked. Files is limited to read-only validation/download of approved-folder configuration/support packages, with no extraction or apply. Current-source browser QA covers the interface; physical display performance remains a qualification task.

The deterministic disconnected OS overlay has 48 application files/62 payload files and passes 25 tests, 17 actual nonroot Linux checks, five system-unit and two user-recovery-unit syntax checks. Fresh read-only preflight runs on every application launch. Application and optional kiosk have bounded three-start budgets and separate recovery. Next qualify the exact base/compute/kernel, actual kiosk and boot, independent runtime supervisor, graphics/frame pacing, loaded RT behavior, signed updates and protected recovery storage. No runtime unit or bootable image is supplied; compressed packages are unavailable in the tested Linux Python 3.13 base. $0 API expenditure, unchanged routing, 71 frozen runtime inputs and 24 original configuration sources preserve the previous baseline.""",
    "docs/PLATFORM_ROADMAP.md": """**Latest 4 October implemented appliance scope — Motion X12/GarciaMech:** [the appliance pass](../reports/appliance-os-20261004/README.md) supplies five persistent destinations: Machine, Setup, Diagnostics, Files and Settings. Reviewed interface preferences/reset/undo share one service contract. Service details grant presentation access only, and full machine reset remains blocked. Files only validates and downloads bounded configuration/support packages from the designated folder. Current-source browser QA does not establish physical display compatibility or frame pacing.

The deterministic development overlay contains 48 application files and 62 payload files. Verification passes 25 OS tests, 17 actual nonroot Linux checks, five system-unit and two user-recovery-unit syntax checks. Per-launch read-only preflight and separate recovery protect the application/kiosk lifecycle; each has a total three-start budget. Actual kiosk launch, a runtime unit, bootable/signed target image, physical boot, frame pacing and motion continuity are not qualified. The tested Linux Python 3.13 base reports compressed packages unavailable. Exact compute/base/kernel, signed updates and protected physical recovery remain roadmap work. $0 API expenditure; Claude's routing, 71 frozen runtime inputs and 24 original configuration sources remain unchanged.""",
    "reports/ENGINEERING_STATUS.md": """**Latest 4 October result — completed Motion X12 appliance pass:** [the source-bound appliance report](appliance-os-20261004/README.md) records persistent Machine, Setup, Diagnostics, Files and Settings navigation, reviewed shared-service interface preferences/reset/undo and deliberate service details. These changes have no motion authority; service details are presentation only and full machine reset remains blocked. Files performs bounded read-only package validation/download without extraction or apply. Current-source browser QA is separate from physical touch/frame-pacing acceptance.

The [OS receipt](appliance-os-20261004/os/receipt.json) records 25 tests, 17 actual nonroot Linux checks, five system-unit and two user-recovery-unit syntax checks, plus a deterministic 48-application-file/62-payload-file overlay. Fresh read-only preflight executes for every application launch; application and optional kiosk each have a total three-start budget and separate recovery. Independent process-survival controls use a non-motion sentinel and do not establish motion continuity. No actual kiosk launch, runtime unit, bootable image, physical boot, signed update or frame-pacing qualification is claimed. The tested Linux Python 3.13 base reports compressed packages unavailable. API cost is $0; routing, 71 frozen runtime inputs and 24 original configuration sources are unchanged. Earlier results below remain historical where their source/scope differs.""",
    "docs/CONTROLLER_OS.md": """**Latest implementation — Motion X12/GarciaMech appliance pass, 4 October 2026:** [current implementation and receipts](../reports/appliance-os-20261004/README.md) add five persistent destinations: Machine, Setup, Diagnostics, Files and Settings. Shared reviewed preferences control text size, reduced interface motion and starting screen. Interface reset and undo use exact reviewed transactions; full machine factory reset is blocked. Deliberate service details are presentation only, with no authentication, terminal, device or motion authority. Files validates/downloads bounded configuration/support archives from the designated folder without extracting or applying them. Current-source browser QA is interface evidence, not physical touchscreen or frame-pacing qualification.

The deterministic disconnected development overlay includes Motion X12 branding, inert recovery assets and unapplied quiet/splash and lifecycle recipes. It carries 48 application files and 62 payload files. Fresh evidence passes 25 OS tests, 17 actual nonroot Linux checks, five system-unit and two user-recovery-unit syntax checks. Every application launch repeats the same read-only image/settings preflight, including after earlier success. Application and optional kiosk each have a total three-start budget with deliberate retry after exhaustion. Kiosk recovery cannot signal or restart the application/runtime; application recovery is separate. Recovery reports external output state as unknown and grants no authority. Inhibited, unhomed restart is a required policy, not an observed motion guarantee.

No kiosk was launched and no motion-runtime unit is present. The overlay is not a bootable image or signed update. Actual boot/base/kernel/graphics/touch, loaded timing, frame pacing, independent runtime continuity, signed update/rollback and physical recovery partitions remain unqualified. The tested Linux Python 3.13 base reports compressed packages unavailable; the declared compression dependency still needs inclusion in a complete qualified base. No startup-time target was measured. This pass used $0 in API calls and changed no user desktop/network configuration, services, disk/partitions, routing, 71 frozen runtime inputs or 24 original configuration sources. The earlier OS contract below remains preserved as history and continuing acceptance requirements.""",
}


def main() -> None:
    receipts = [
        "reports/appliance-os-20261004/os/receipt.json",
        "reports/appliance-os-20261004/service/receipt.json",
    ]
    evidence_before = {path: digest((ROOT / path).read_bytes()) for path in receipts}
    protected: dict[str, str] = {}
    for relative in receipts:
        receipt = json.loads((ROOT / relative).read_text(encoding="utf-8"))
        for key in ("source_sha256", "protected_runtime_source_sha256", "protected_source_and_setting_sha256"):
            for path, expected in receipt.get(key, {}).items():
                previous = protected.setdefault(path, expected)
                if previous != expected:
                    raise RuntimeError(f"Conflicting canonical source binding: {path}")
    for path, expected in protected.items():
        if digest((ROOT / path).read_bytes()) != expected:
            raise RuntimeError(f"Canonical source mismatch before documentation update: {path}")

    before: dict[str, bytes] = {path: (ROOT / path).read_bytes() for path in INSERTIONS}
    prepared: dict[str, bytes] = {}
    for path, data in before.items():
        newline = b"\r\n" if b"\r\n" in data else b"\n"
        split = data.find(newline + newline)
        if split < 0 or not data.startswith(b"# "):
            raise RuntimeError(f"Unexpected document structure: {path}")
        addition = INSERTIONS[path].replace("\n", newline.decode()).encode("utf-8") + newline + newline
        prepared[path] = data[: split + len(newline) * 2] + addition + data[split + len(newline) * 2 :]

    # All original bytes are preserved exclusively before any authorized document edit.
    for path, data in before.items():
        snapshot = OUT / "before" / path
        snapshot.parent.mkdir(parents=True, exist_ok=True)
        with snapshot.open("xb") as stream:
            stream.write(data)
    for path, data in prepared.items():
        if (ROOT / path).read_bytes() != before[path]:
            raise RuntimeError(f"Concurrent document edit: {path}")
        (ROOT / path).write_bytes(data)

    docs = {}
    for path, original in before.items():
        current = (ROOT / path).read_bytes()
        newline = b"\r\n" if b"\r\n" in original else b"\n"
        addition = INSERTIONS[path].replace("\n", newline.decode()).encode("utf-8") + newline + newline
        split = original.find(newline + newline) + len(newline) * 2
        recovered = current[:split] + current[split + len(addition):]
        if current != prepared[path] or recovered != original:
            raise RuntimeError(f"Original history preservation failed: {path}")
        docs[path] = {"before_sha256": digest(original), "after_sha256": digest(current),
                      "before_path": f"reports/appliance-os-20261004/docs-r01/before/{path}",
                      "original_bytes_recovered_exactly": True}
    for path, expected in protected.items():
        if digest((ROOT / path).read_bytes()) != expected:
            raise RuntimeError(f"Protected source changed during documentation update: {path}")
    if {path: digest((ROOT / path).read_bytes()) for path in receipts} != evidence_before:
        raise RuntimeError("Sealed canonical receipt changed during documentation update")

    receipt = {
        "schema_version": 1, "kind": "additive_appliance_documentation_update",
        "utc": datetime.now(timezone.utc).isoformat(), "status": "PASS_DOCUMENTATION_HISTORY_AND_SOURCE_PRESERVATION",
        "documents": docs, "canonical_receipt_sha256": evidence_before,
        "protected_source_and_setting_sha256": protected, "protected_bindings_rechecked": len(protected),
        "updater_sha256": digest(Path(__file__).read_bytes()),
        "application_source_edits": 0, "sealed_receipt_edits": 0, "api_calls": 0,
        "scope": "Five project documents only; additive latest-result paragraphs, no new execution or physical qualification.",
        "root_summary_target": "reports/appliance-os-20261004/README.md",
        "root_summary_pending_at_edit": not (ROOT / "reports/appliance-os-20261004/README.md").exists(),
    }
    with (OUT / "receipt.json").open("x", encoding="utf-8", newline="\n") as stream:
        stream.write(json.dumps(receipt, indent=2, sort_keys=True) + "\n")
    print(json.dumps({"status": receipt["status"], "documents": list(docs),
                      "protected_bindings_rechecked": len(protected),
                      "receipt_sha256": digest((OUT / "receipt.json").read_bytes())}, indent=2))


if __name__ == "__main__":
    main()
