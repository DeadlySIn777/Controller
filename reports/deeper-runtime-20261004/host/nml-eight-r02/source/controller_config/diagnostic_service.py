"""One offline diagnostic/package contract for the CLI and setup workbench.

No transport, real-time hook, provider call or machine command exists here.
"""
from pathlib import Path
import tempfile
from copy import deepcopy

from .model import ConfigurationError
from .service import canonical, digest
from .setup_service import SetupService, GUARDS, example_draft, validate_draft

EXAMPLE_DIRECTORY = "diagnostic-example-v2"
MAX_BACKUP_UPLOAD = 8 * 1024 * 1024


def example_definition_snapshot():
    """Deterministic authored gantry definition, separate from customer settings."""
    draft = example_draft("sim-gantry-4motor")
    draft["machine_name"] = "Authored gantry fault example"
    checked = validate_draft(draft, require_complete=True)
    return {"schema_version": 1, "kind": "is2_disconnected_backup",
            "initialized": True, "store_id": "e0621974-e7dc-4f87-a622-0365d0bb7e51",
            "epoch": "c43bd747-2a67-4dbb-afd1-bd4f8eddd201",
            "revision": 0, "current_revision": 0, "generation": 1,
            "draft": deepcopy(draft), "history": [], "retained_profile_drafts": {},
            "active": {"generation": 1, "draft": draft, "calculations": checked["calculations"],
                       "wiring": checked["wiring"], "configuration_sha256": digest(draft)},
            "provenance": "authored_builtin_gantry_definition_v2", **deepcopy(GUARDS)}


def _convert_error(error):
    if isinstance(error, ConfigurationError):
        return error
    return ConfigurationError(getattr(error, "code", "DIAGNOSTIC_ERROR"), str(error))


class DiagnosticService:
    def __init__(self, directory):
        self.directory = Path(directory).resolve()
        self.setup = SetupService(self.directory / "setup.json")

    def _recorder(self, example=False):
        from .diagnostic_recorder import DiagnosticRecorder
        return DiagnosticRecorder(self.directory / (EXAMPLE_DIRECTORY if example else "diagnostics"))

    def context(self, setup_snapshot=None):
        from .package_archive import capabilities
        result = {"capabilities": capabilities(), "simulation_only": True,
                  "live_source_connected": False, "api_calls": 0, "machine_commands": []}
        try:
            result["report"] = self.report(setup_snapshot=setup_snapshot)
            result["recorder"] = result["report"]["storage"]
            result["example_available"] = (self.directory / EXAMPLE_DIRECTORY).exists()
        except (ValueError, OSError, ConfigurationError) as error:
            result["error"] = {"code": getattr(error, "code", "DIAGNOSTIC_IO"),
                               "message": str(error)}
        return result

    def append(self, record):
        from .diagnostic_recorder import RecorderError
        from .package_archive import ArchiveError
        if type(record) is not dict:
            raise ConfigurationError("DIAGNOSTIC_RECORD", "Expected a declared simulation envelope")
        try:
            recorder = self._recorder()
            result = recorder.capture_fault(record) if record.get("kind") == "fault" else recorder.append(record)
            recorder.flush()
            return result
        except (RecorderError, ArchiveError) as error:
            raise _convert_error(error) from error

    def report(self, incident_id=None, example=False, setup_snapshot=None):
        from .diagnostic_explanations import explain_fault
        from .diagnostic_recorder import RecorderError
        from .package_archive import ArchiveError
        from .machine_state import build_machine_state
        try:
            report = self._recorder(example).report(incident_id=incident_id)
            report["machine_state"] = build_machine_state(
                (example_definition_snapshot() if example else self.setup.status())
                if setup_snapshot is None else setup_snapshot,
                report.get("records", []))
            report["explanations"], report["explanation_errors"] = [], []
            for record in report.get("records", []):
                if record.get("kind") != "fault":
                    continue
                try:
                    report["explanations"].append(explain_fault(record))
                except ConfigurationError as error:
                    report["explanation_errors"].append({"code": getattr(error, "code", "EXPLANATION_FORMAT"),
                        "message": str(error), "sequence": record.get("sequence"),
                        "raw_record_retained": True})
            return report
        except (RecorderError, ArchiveError) as error:
            raise _convert_error(error) from error

    def create_example(self):
        """A deterministic separate fixture: five minutes before, 30s after.

        Synthetic time is explicit. This does not record or observe a machine.
        Repeat clicks reuse the fixture; they never clear retained diagnostics.
        """
        from .diagnostic_explanations import example_fault
        from .diagnostic_recorder import RecorderError
        from .package_archive import ArchiveError
        try:
            recorder = self._recorder(example=True)
            motor = example_definition_snapshot()["active"]["draft"]["motors"][2]
            fault_data = example_fault()
            fault_data["resource"]["axis"] = motor["axis"].upper()
            fault_data["source"]["reference"] = "authored-gantry-diagnostic-example-v2"
            def expected(sequence):
                fault = sequence == 300
                return {"schema_version": 1, "simulation_only": True,
                        "timestamp_ns": sequence * 1_000_000_000,
                        "source": "authored-ui-simulation", "sequence": sequence,
                        "kind": "fault" if fault else "sample",
                        "data": deepcopy(fault_data) if fault else {
                            "motor": "M2", "axis": motor["axis"].upper(), "commanded_velocity": 82,
                            "unit": "mm/s", "physical_observation": False}}
            previous = recorder.report()
            records = previous.get("records", [])
            if (len(records) > 331 or previous.get("storage", {}).get("dropped_records", 0) or
                    any(canonical(record) != canonical(expected(i)) for i, record in enumerate(records))):
                raise ConfigurationError("EXAMPLE_CONFLICT", "The retained example differs from its authored fixture; preserve it and use a separate workspace")
            for sequence in range(len(records), 331):
                record = expected(sequence)
                if record["kind"] == "fault":
                    recorder.capture_fault(record)
                else:
                    recorder.append(record)
            recorder.flush()
            return self.report(example=True)
        except (RecorderError, ArchiveError) as error:
            raise _convert_error(error) from error

    def package(self, destination, kind="support", example=False):
        from .package_archive import create_archive, ArchiveError
        if kind not in ("support", "config") or type(example) is not bool:
            raise ConfigurationError("PACKAGE_KIND", "Choose a support or configuration snapshot")
        entries = {}
        snapshot = None
        if example:
            snapshot = example_definition_snapshot()
            entries["setup/snapshot.json"] = canonical(snapshot)
        elif self.setup.path.exists():
            snapshot = self.setup.backup_snapshot()
            entries["setup/snapshot.json"] = canonical(snapshot)
        elif kind == "config":
            raise ConfigurationError("SETUP_NOT_INITIALIZED", "Save a simulation setup before exporting its backup")
        if kind == "support":
            state_snapshot = None if snapshot is None else {**snapshot, "initialized": True,
                                                            "current_revision": snapshot["revision"]}
            entries["diagnostics/report.json"] = canonical(self.report(example=example, setup_snapshot=state_snapshot))
        metadata = {"scope": "disconnected_simulation", "authored_example": example,
                    "automatic_restore": False, "motion_authorized": False,
                    "contains": "Local setup facts and authored diagnostic records; review before sharing"}
        try:
            return create_archive(destination, entries, kind=kind, metadata=metadata)
        except ArchiveError as error:
            raise _convert_error(error) from error

    def package_bytes(self, kind="support", example=False):
        with tempfile.TemporaryDirectory(prefix="controller-export-") as folder:
            path = Path(folder) / "snapshot.tar.zst"
            self.package(path, kind, example)
            return path.read_bytes()

    def restore_preview(self, path, source="active"):
        from .package_archive import read_archive, ArchiveError
        from .setup_web import _request_json
        if source not in ("active", "draft"):
            raise ConfigurationError("BACKUP_SOURCE", "Choose the saved active setup or its unsaved draft")
        try:
            package = read_archive(path, expected_kind="config")
            raw = package["entries"].get("setup/snapshot.json")
            snapshot = _request_json(raw) if raw is not None else None
            if (type(snapshot) is not dict or type(snapshot.get("schema_version")) is not int or snapshot.get("schema_version") != 1 or
                    snapshot.get("kind") != "is2_disconnected_backup" or
                    snapshot.get("simulation_only") is not True or snapshot.get("motion_authorized") is not False):
                raise ConfigurationError("BACKUP_FORMAT", "Expected a disconnected configuration backup")
            candidate = snapshot.get("draft") if source == "draft" else (snapshot.get("active") or {}).get("draft")
            if candidate is None:
                raise ConfigurationError("BACKUP_EMPTY", "The selected backup has no configuration to review")
            return self.setup.preview(candidate)
        except ArchiveError as error:
            raise _convert_error(error) from error
        except (ValueError, UnicodeError, RecursionError, TypeError, AttributeError) as error:
            if isinstance(error, ConfigurationError):
                raise
            raise ConfigurationError("BACKUP_FORMAT", "The package does not contain a valid simulation snapshot") from error

    def restore_preview_bytes(self, raw, source="active"):
        """Bounded upload adapter; inspect privately and never extract or apply."""
        if type(raw) is not bytes or not 0 < len(raw) <= MAX_BACKUP_UPLOAD:
            raise ConfigurationError("BACKUP_SIZE", "Choose a nonempty backup within the compressed package limit")
        with tempfile.TemporaryDirectory(prefix="controller-import-") as folder:
            path = Path(folder) / "backup.tar.zst"
            path.write_bytes(raw)
            return self.restore_preview(path, source)
