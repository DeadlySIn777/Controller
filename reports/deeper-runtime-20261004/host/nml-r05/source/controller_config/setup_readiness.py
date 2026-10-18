"""Evidence-backed setup readiness and a disconnected configuration rehearsal.

Every check names its evidence and scope. Nothing here observes equipment,
grants authority, changes settings or contacts an AI provider.
"""
from copy import deepcopy
from pathlib import Path
import tempfile

from .model import ConfigurationError
from .service import canonical, digest
from .setup_service import SetupService, GUARDS, validate_draft
from .diagnostic_service import DiagnosticService


def _check(identifier, title, status, evidence, action, step, required=True):
    return {"id": identifier, "title": title, "status": status, "evidence": evidence,
            "action": action, "ui_step": step, "required_for_simulation": required}


class ReadinessService:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.setup = SetupService(self.directory / "setup.json")
        self.diagnostics = DiagnosticService(self.directory)

    def status(self):
        checks, error, snapshot = [], None, None
        try:
            snapshot = self.setup.status()
        except (ConfigurationError, OSError, ValueError) as exc:
            error = {"code": getattr(exc, "code", "SETUP_IO"), "message": str(exc)}
        initialized = snapshot is not None and snapshot["initialized"]
        checks.append(_check("store", "Local settings", "blocked" if error else "pass" if initialized else "pending",
                             error or ("Store integrity and derived settings verified" if initialized else "No settings store created"),
                             "Inspect the preserved settings file" if error else "Inspect your saved machine profile" if initialized else "Choose your machine profile", 0))
        validation = snapshot.get("validation") if snapshot else None
        missing = validation["missing_facts"] if validation else []
        blockers = validation["blockers"] if validation else []
        checks.append(_check("facts", "Known mechanics", "pass" if validation and not missing else "pending",
                             {"missing_count": len(missing), "missing_facts": missing, "provenance": "user_selections"},
                             "Inspect the saved mechanical selections" if validation and not missing else "Enter the missing mechanics; unknown values stay unanswered", 1))
        checks.append(_check("limits", "Timing, rates and electrical limits", "blocked" if blockers else "pass" if validation and validation["valid"] else "pending",
                             {"blockers": blockers, "calculations": validation["calculations"] if validation else [],
                              "output_groups": validation["output_groups"] if validation else []},
                             "Inspect calculated rates and retained limits" if validation and validation["valid"] else "Resolve the configuration checks before review", 1))
        active = snapshot.get("active") if snapshot else None
        matches = active is not None and canonical(snapshot["draft"]) == canonical(active["draft"])
        checks.append(_check("review", "Reviewed saved generation", "pass" if matches else "pending",
                             {"generation": snapshot["generation"] if snapshot else None, "draft_matches_active": matches},
                             "Inspect the reviewed configuration" if matches else "Review and save the current draft", 2))
        diagnostic = None
        if snapshot is not None:
            try:
                diagnostic = self.diagnostics.report(setup_snapshot=snapshot)
            except (ConfigurationError, OSError, ValueError) as exc:
                diagnostic = {"error": {"code": getattr(exc, "code", "DIAGNOSTIC_IO"), "message": str(exc)}}
        checks.append(_check("recorder", "Diagnostic evidence", "unavailable" if diagnostic is None or "error" in diagnostic else "pass" if diagnostic.get("record_count", 0) else "pending",
                             (diagnostic or {}).get("error") or {"record_count": (diagnostic or {}).get("record_count", 0),
                              "live_source_connected": False, "scope": "retained_simulation_records"},
                             "Inspect workspace recordings or try the separate fault example", 4, False))
        checks.append(_check("physical", "Physical commissioning", "unavailable",
                             "No qualified hardware observations, wiring checks or motion tests exist in this disconnected workspace",
                             "Independent hardware commissioning remains required", None, False))
        binding = None
        if initialized:
            binding = {"store_id": snapshot["store_id"], "epoch": snapshot["epoch"], "revision": snapshot["current_revision"],
                       "generation": snapshot["generation"], "configuration_sha256": active["configuration_sha256"] if active else None,
                       "draft_sha256": digest(snapshot["draft"])}
        required = [item for item in checks if item["required_for_simulation"]]
        ready = all(item["status"] == "pass" for item in required)
        next_check = next((item for item in required if item["status"] != "pass"), None)
        return {"schema_version": 1, "kind": "is2_setup_readiness", "scope": "disconnected_setup_configuration",
                "simulation_configuration_ready": ready, "configuration_binding": binding,
                "checks": checks, "next_step": deepcopy(next_check), "setup_error": error,
                "api_calls": 0, **deepcopy(GUARDS)}

    def rehearse(self, expected_revision):
        """Exercise this saved configuration and its backup, never a motion loop.

        Receipts bind to one revision. Private archive files are deleted after
        roundtrip verification; the user's settings and allowance stay untouched.
        """
        from .package_archive import create_archive, read_archive, ArchiveError
        snapshot = self.setup.backup_snapshot()
        if type(expected_revision) is not int or snapshot["revision"] != expected_revision:
            raise ConfigurationError("SETUP_STALE", "Settings changed; refresh readiness before running the self-check")
        active = snapshot["active"]
        if active is None or canonical(snapshot["draft"]) != canonical(active["draft"]):
            raise ConfigurationError("READINESS_REVIEW", "Review and save the current draft before its self-check")
        checked = validate_draft(active["draft"], require_complete=True)
        results = [{"id": "recomputed_configuration", "status": "pass", "evidence": "Independently validated saved mechanics, derived rates and assignments"}]
        for index, motor in enumerate(active["draft"]["motors"]):
            probe = deepcopy(active["draft"])
            probe["motors"][index]["dir_setup_ns"] = 1
            rejected = any(issue["code"] == "SETUP_TIMING" for issue in validate_draft(probe)["blockers"])
            results.append({"id": f"{motor['id']}_short_direction_timing", "status": "pass" if rejected else "fail",
                            "evidence": "Unsafe simulation direction timing rejected", "resource": motor["resource"]})
        probe = deepcopy(active["draft"])
        probe["outputs"] = [{"resource": "SIM.DO0", "role": "self-check only", "equipment_profile": "sim-smart-output-v1", "voltage_v": 24, "current_a": .6}]
        rejected = any(issue["code"] == "SETUP_CURRENT" for issue in validate_draft(probe)["blockers"])
        results.append({"id": "overcurrent_rejected", "status": "pass" if rejected else "fail", "evidence": "0.6 A selection rejected against the retained 0.5 A channel limit"})
        try:
            with tempfile.TemporaryDirectory(prefix="controller-rehearsal-") as folder:
                path = Path(folder) / "backup.tar.zst"
                create_archive(path, {"setup/snapshot.json": canonical(snapshot)}, kind="config")
                restored = read_archive(path, expected_kind="config")
                same = restored["entries"].get("setup/snapshot.json") == canonical(snapshot)
            results.append({"id": "backup_roundtrip", "status": "pass" if same else "fail", "evidence": "Actual bounded tar/Zstd archive, checksums and exact configuration bytes verified"})
        except (ArchiveError, OSError) as exc:
            results.append({"id": "backup_roundtrip", "status": "unavailable", "evidence": {"code": getattr(exc, "code", "BACKUP_IO"), "message": str(exc)}})
        binding = {key: snapshot[key] for key in ("store_id", "epoch", "revision", "generation")}
        binding.update(configuration_sha256=active["configuration_sha256"], draft_sha256=digest(snapshot["draft"]))
        latest = self.setup.status()
        latest_binding = {key: latest.get(key) for key in ("store_id", "epoch", "revision", "generation")}
        latest_binding.update(configuration_sha256=(latest.get("active") or {}).get("configuration_sha256"), draft_sha256=digest(latest.get("draft")))
        if latest_binding != binding:
            raise ConfigurationError("SETUP_STALE", "Settings changed during the self-check; run it again against the current revision")
        receipt = {"schema_version": 1, "kind": "is2_disconnected_configuration_self_check", "configuration_binding": binding,
                   "passed": all(item["status"] == "pass" for item in results), "checks": results,
                   "motor_count": len(checked["calculations"]), "scope": "configuration_validation_and_backup_only",
                   "motion_loop_tested": False, "physical_measurements": 0, "api_calls": 0, **deepcopy(GUARDS)}
        return {**receipt, "receipt_sha256": digest(receipt)}
