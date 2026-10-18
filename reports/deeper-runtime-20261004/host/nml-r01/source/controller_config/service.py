"""Shared configuration service with no physical transport or motion API.

The default runtime is an explicitly disconnected fixture, not an observation of a
real machine. A future production adapter requires an authoritative state/ownership
contract; editing these fixture flags does not prove that real equipment is stopped.
"""

from contextlib import contextmanager
from copy import deepcopy
from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import tempfile
import time
import uuid

from .model import (ConfigurationError, PROFILES, capabilities, configuration_schema,
                    profile, validate_configuration, wiring_plan)

MAX_BYTES = 2_000_000
HISTORY_LIMIT = 20
AUDIT_LIMIT = 100
# Configuration-changing audit actions advance the revision. Event actions record
# a same-revision fact (for example a module swap) without changing configuration.
CHANGE_ACTIONS = ("initialize", "apply", "restore")
EVENT_ACTIONS = ("replace_module",)
# Windows refuses os.replace while any process (a concurrent `config show`
# reader, OneDrive or an antivirus scanner) holds the target open without
# FILE_SHARE_DELETE. Retry only that transient refusal, with the writer lock
# still held; the final failure propagates and the old document is kept.
REPLACE_RETRY_DELAYS_S = (0.01, 0.02, 0.05, 0.1, 0.2)


def canonical(value):
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False, allow_nan=False).encode("utf-8")


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def _now():
    return datetime.now(timezone.utc).isoformat()


def _unique_pairs(pairs):
    value = {}
    for key, item in pairs:
        if key in value:
            raise ConfigurationError("DUPLICATE_KEY", f"Duplicate JSON key: {key}")
        value[key] = item
    return value


def read_json(path):
    try:
        with Path(path).open("rb") as stream:
            raw = stream.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES:
            raise ConfigurationError("DOCUMENT_SIZE", "Document exceeds prototype size limit")
        return json.loads(raw.decode("utf-8-sig"), object_pairs_hook=_unique_pairs,
                          parse_constant=lambda value: (_ for _ in ()).throw(ConfigurationError("NONFINITE", f"Nonfinite JSON number: {value}")))
    except ConfigurationError:
        raise
    except (UnicodeError, ValueError, RecursionError) as error:
        raise ConfigurationError("INVALID_JSON", "Invalid or excessively nested JSON document") from error
    except OSError as error:
        raise ConfigurationError("IO_ERROR", str(error)) from error


def _keys(value, expected, code):
    if type(value) is not dict or set(value) != set(expected):
        raise ConfigurationError(code, "Unexpected document structure")


def _nonnegative_int(value, code):
    if type(value) is not int or value < 0:
        raise ConfigurationError(code, "Expected a nonnegative integer")


def _actor(value):
    if type(value) is not str or not value.strip() or len(value) > 120 or any(ord(c) < 32 for c in value):
        raise ConfigurationError("ACTOR", "Actor must be a nonempty printable label of at most 120 characters")
    return value


@contextmanager
def _exclusive_lock(path):
    lock = Path(str(path) + ".lock")
    try:
        handle = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
    except FileExistsError as error:
        raise ConfigurationError("STORE_BUSY", "Exclusive lock exists; inspect an interrupted writer before removing a stale lock") from error
    try:
        os.write(handle, str(os.getpid()).encode("ascii"))
        os.close(handle)
        handle = None
        yield
    finally:
        if handle is not None:
            os.close(handle)
        lock.unlink(missing_ok=True)


def _replace(source, destination):
    for delay in REPLACE_RETRY_DELAYS_S:
        try:
            os.replace(source, destination)
            return
        except PermissionError:
            time.sleep(delay)
    os.replace(source, destination)


def _same(before, after):
    """Equality of the stored JSON representation, not Python equality.

    Python treats 5 == 5.0 and True == 1, but canonical JSON (and therefore every
    digest) distinguishes them, so a representation change must appear in a diff.
    """
    return type(before) is type(after) and canonical(before) == canonical(after)


def atomic_write(path, value):
    """Replace one complete document on the same filesystem; never truncate live state."""
    path = Path(path)
    raw = canonical(value) + b"\n"
    if len(raw) > MAX_BYTES:
        raise ConfigurationError("DOCUMENT_SIZE", "Document exceeds prototype size limit")
    descriptor, temporary = tempfile.mkstemp(prefix=path.name + ".", suffix=".tmp", dir=path.parent)
    try:
        with os.fdopen(descriptor, "wb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
        _replace(temporary, path)
        if os.name != "nt":
            directory = os.open(path.parent, os.O_RDONLY)
            try:
                os.fsync(directory)
            finally:
                os.close(directory)
    finally:
        Path(temporary).unlink(missing_ok=True)


def export_json(path, value):
    """Explicit exports never overwrite a user file or an existing backup."""
    path = Path(path).resolve()
    if not path.parent.is_dir():
        raise ConfigurationError("IO_ERROR", "Export parent directory must already exist")
    with _exclusive_lock(path):
        if path.exists():
            raise ConfigurationError("FILE_EXISTS", "Export destination already exists")
        atomic_write(path, value)


def _seal(payload):
    return {**payload, "integrity_sha256": digest(payload)}


def _verify_seal(value, code):
    if type(value) is not dict or "integrity_sha256" not in value:
        raise ConfigurationError(code, "Missing integrity checksum")
    payload = {key: item for key, item in value.items() if key != "integrity_sha256"}
    try:
        matches = value["integrity_sha256"] == digest(payload)
    except (ValueError, TypeError, RecursionError) as error:
        raise ConfigurationError(code, "Invalid checksummed data") from error
    if not matches:
        raise ConfigurationError(code, "Integrity checksum mismatch; this is corruption detection, not authentication")
    return payload


def _diff(before, after, path=""):
    if _same(before, after):
        return []
    if type(before) is dict and type(after) is dict:
        changes = []
        for key in sorted(set(before) | set(after)):
            pointer = path + "/" + key.replace("~", "~0").replace("/", "~1")
            if key not in before:
                changes.append({"path": pointer, "before": None, "after": after[key]})
            elif key not in after:
                changes.append({"path": pointer, "before": before[key], "after": None})
            else:
                changes.extend(_diff(before[key], after[key], pointer))
        return changes
    if type(before) is list and type(after) is list and len(before) == len(after):
        changes = []
        for index, (old, new) in enumerate(zip(before, after)):
            changes.extend(_diff(old, new, path + f"/{index}"))
        return changes
    return [{"path": path or "/", "before": before, "after": after}]


@dataclass(frozen=True)
class RuntimeState:
    simulation_only: bool = True
    connected: bool = False
    armed: bool = False
    running: bool = False
    epoch: str = "disconnected-fixture-v1"


class ConfigurationService:
    """Common methods for CLI and future UI clients; all mutations are file-only."""
    def __init__(self, store_path, state_provider=None):
        self.path = Path(store_path).resolve()
        self.state_provider = state_provider or RuntimeState

    capabilities = staticmethod(capabilities)
    schema = staticmethod(configuration_schema)
    select_profile = staticmethod(profile)
    validate = staticmethod(validate_configuration)
    wiring = staticmethod(wiring_plan)

    def profiles(self):
        return deepcopy(PROFILES)

    def _safe_state(self):
        state = self.state_provider()
        if not isinstance(state, RuntimeState) or any(type(getattr(state, field)) is not bool for field in ("simulation_only", "connected", "armed", "running")):
            raise ConfigurationError("RUNTIME_STATE", "Malformed simulated runtime state")
        if not state.simulation_only or state.connected or state.armed or state.running:
            raise ConfigurationError("UNSAFE_SIMULATION_STATE", "Requires disconnected simulation, disarmed and stopped")
        if type(state.epoch) is not str or not state.epoch:
            raise ConfigurationError("RUNTIME_STATE", "Missing simulated runtime epoch")
        return state

    def initialize(self, actor="local-demo"):
        actor = _actor(actor)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with _exclusive_lock(self.path):
            self._safe_state()
            if self.path.exists():
                raise ConfigurationError("STORE_EXISTS", "Store already exists; initialization never overwrites it")
            payload = {"schema_version": 1, "kind": "disconnected_configuration_store",
                       "store_id": str(uuid.uuid4()), "revision": 0, "configuration": None,
                       "configuration_sha256": digest(None), "history": [],
                       "audit": [{"revision": 0, "action": "initialize", "actor": actor, "timestamp": _now(),
                                  "before_sha256": digest(None), "after_sha256": digest(None)}]}
            atomic_write(self.path, _seal(payload))
        return self.show()

    def _load(self):
        data = _verify_seal(read_json(self.path), "STORE_CORRUPT")
        _keys(data, ("schema_version", "kind", "store_id", "revision", "configuration", "configuration_sha256", "history", "audit"), "STORE_CORRUPT")
        if type(data["schema_version"]) is not int or data["schema_version"] != 1 or data["kind"] != "disconnected_configuration_store":
            raise ConfigurationError("STORE_VERSION", "Unsupported store kind/version")
        try:
            uuid.UUID(data["store_id"])
        except (ValueError, TypeError, AttributeError) as error:
            raise ConfigurationError("STORE_CORRUPT", "Invalid store identity") from error
        _nonnegative_int(data["revision"], "STORE_CORRUPT")
        if data["configuration"] is not None:
            validate_configuration(data["configuration"])
        elif data["revision"] != 0:
            raise ConfigurationError("STORE_CORRUPT", "Only initial store may have no configuration")
        if data["configuration_sha256"] != digest(data["configuration"]):
            raise ConfigurationError("STORE_CORRUPT", "Configuration checksum mismatch")
        if type(data["history"]) is not list or len(data["history"]) > HISTORY_LIMIT or type(data["audit"]) is not list or not 1 <= len(data["audit"]) <= AUDIT_LIMIT:
            raise ConfigurationError("STORE_CORRUPT", "Invalid history/audit length")
        for record in data["history"]:
            _keys(record, ("revision", "configuration", "sha256"), "STORE_CORRUPT")
            _nonnegative_int(record["revision"], "STORE_CORRUPT")
            if record["configuration"] is not None:
                validate_configuration(record["configuration"])
            if record["revision"] >= data["revision"] or record["sha256"] != digest(record["configuration"]):
                raise ConfigurationError("STORE_CORRUPT", "Invalid history revision/checksum")
        for entry in data["audit"]:
            _keys(entry, ("revision", "action", "actor", "timestamp", "before_sha256", "after_sha256"), "STORE_CORRUPT")
            _nonnegative_int(entry["revision"], "STORE_CORRUPT")
            _actor(entry["actor"])
            if entry["action"] not in CHANGE_ACTIONS + EVENT_ACTIONS or type(entry["timestamp"]) is not str:
                raise ConfigurationError("STORE_CORRUPT", "Invalid audit record")
            if entry["action"] in EVENT_ACTIONS and entry["before_sha256"] != entry["after_sha256"]:
                raise ConfigurationError("STORE_CORRUPT", "An audit event cannot change configuration")
        if data["audit"][-1]["revision"] != data["revision"] or data["audit"][-1]["after_sha256"] != data["configuration_sha256"]:
            raise ConfigurationError("STORE_CORRUPT", "Audit does not match current revision")
        return data

    def show(self):
        state = self._load()
        return {"schema_version": 1, "store_id": state["store_id"], "revision": state["revision"],
                "configuration_sha256": state["configuration_sha256"], "configuration": state["configuration"],
                "simulation_only": True, "physical_commissioning_complete": False}

    def audit(self):
        state = self._load()
        return {"revision": state["revision"], "entries": state["audit"], "retained_prior_configurations": len(state["history"])}

    def _plan(self, configuration, action, restore_source=None):
        configuration = deepcopy(configuration)
        validate_configuration(configuration)
        runtime = self._safe_state()
        state = self._load()
        return {"schema_version": 1, "kind": "disconnected_configuration_plan", "action": action,
                "store_id": state["store_id"], "base_revision": state["revision"],
                "base_sha256": state["configuration_sha256"], "runtime_epoch": runtime.epoch,
                "candidate_sha256": digest(configuration), "configuration": configuration,
                "changes": _diff(state["configuration"], configuration), "restore_source": restore_source,
                "simulation_only": True}

    def preview(self, configuration):
        return self._plan(configuration, "apply")

    def apply(self, plan, actor="local-demo"):
        plan, actor = deepcopy(plan), _actor(actor)
        _keys(plan, ("schema_version", "kind", "action", "store_id", "base_revision", "base_sha256", "runtime_epoch", "candidate_sha256", "configuration", "changes", "restore_source", "simulation_only"), "PLAN_INVALID")
        if type(plan["schema_version"]) is not int or plan["schema_version"] != 1 or plan["kind"] != "disconnected_configuration_plan" or plan["simulation_only"] is not True or plan["action"] not in ("apply", "restore"):
            raise ConfigurationError("PLAN_INVALID", "Unsupported plan identity/action")
        _nonnegative_int(plan["base_revision"], "PLAN_INVALID")
        validate_configuration(plan["configuration"])
        if digest(plan["configuration"]) != plan["candidate_sha256"]:
            raise ConfigurationError("PLAN_CHANGED", "Candidate changed after preview")
        if plan["action"] == "apply" and plan["restore_source"] is not None:
            raise ConfigurationError("PLAN_INVALID", "Apply plan must not claim a restore source")
        if plan["action"] == "restore":
            self._validate_backup(plan["restore_source"])
            if plan["restore_source"]["configuration"] != plan["configuration"]:
                raise ConfigurationError("PLAN_INVALID", "Restore candidate differs from validated backup")
        with _exclusive_lock(self.path):
            runtime = self._safe_state()
            state = self._load()
            if plan["store_id"] != state["store_id"] or plan["base_revision"] != state["revision"] or plan["base_sha256"] != state["configuration_sha256"] or plan["runtime_epoch"] != runtime.epoch:
                raise ConfigurationError("STALE_PLAN", "Store, revision, configuration or simulated runtime epoch changed; preview again")
            if plan["action"] == "restore" and plan["restore_source"]["store_id"] != state["store_id"]:
                raise ConfigurationError("BACKUP_IDENTITY", "Backup belongs to another virtual store")
            if plan["changes"] != _diff(state["configuration"], plan["configuration"]):
                raise ConfigurationError("PLAN_CHANGED", "Diff does not match current and proposed configurations")
            if not plan["changes"]:
                # Same result keys as a changing apply; nothing is written.
                return {"changed": False, "revision": state["revision"], "configuration_sha256": state["configuration_sha256"],
                        "simulation_only": True, "commissioning": "unchanged; no revision created"}
            before = state["configuration_sha256"]
            state["history"] = (state["history"] + [{"revision": state["revision"], "configuration": state["configuration"], "sha256": before}])[-HISTORY_LIMIT:]
            state["revision"] += 1
            state["configuration"] = plan["configuration"]
            state["configuration_sha256"] = plan["candidate_sha256"]
            state["audit"] = (state["audit"] + [{"revision": state["revision"], "action": plan["action"], "actor": actor,
                "timestamp": _now(), "before_sha256": before, "after_sha256": state["configuration_sha256"]}])[-AUDIT_LIMIT:]
            if self._safe_state() != runtime:
                raise ConfigurationError("RUNTIME_CHANGED", "Simulated state changed while preparing commit")
            atomic_write(self.path, _seal(state))
        return {"changed": True, "revision": state["revision"], "configuration_sha256": state["configuration_sha256"],
                "simulation_only": True, "commissioning": "pending; no permission or position restored"}

    def _record_event_locked(self, action, actor, expected_revision, expected_sha256):
        """Append one same-revision audit entry; configuration is never changed.

        Internal only, deliberately not part of the public service, CLI or UI
        contract: the entry is a label whose meaning rests on the caller's own
        checks. The only caller is RecoveryService.apply, which holds this
        store's exclusive lock and has already verified the replacement's
        binding, inventory, cartridge generation and stale state before it
        records "replace_module". Do not expose this as a free-standing event
        API; a future public event command needs its own verified contract.
        """
        actor = _actor(actor)
        if action not in EVENT_ACTIONS:
            raise ConfigurationError("AUDIT_ACTION", "Only named configuration-neutral audit events are accepted")
        runtime = self._safe_state()
        state = self._load()
        if state["revision"] != expected_revision or state["configuration_sha256"] != expected_sha256:
            raise ConfigurationError("STALE_PLAN", "Store revision or configuration changed before the audit event")
        entry = {"revision": state["revision"], "action": action, "actor": actor, "timestamp": _now(),
                 "before_sha256": state["configuration_sha256"], "after_sha256": state["configuration_sha256"]}
        state["audit"] = (state["audit"] + [entry])[-AUDIT_LIMIT:]
        if self._safe_state() != runtime:
            raise ConfigurationError("RUNTIME_CHANGED", "Simulated state changed while preparing audit event")
        atomic_write(self.path, _seal(state))
        return deepcopy(entry)

    def backup(self):
        state = self._load()
        if state["configuration"] is None:
            raise ConfigurationError("NO_CONFIGURATION", "Apply a simulated profile before exporting a backup")
        return _seal({"schema_version": 1, "kind": "disconnected_configuration_backup", "store_id": state["store_id"],
                      "source_revision": state["revision"], "created_at": _now(), "configuration": state["configuration"]})

    @staticmethod
    def _validate_backup(backup):
        data = _verify_seal(backup, "BACKUP_CORRUPT")
        _keys(data, ("schema_version", "kind", "store_id", "source_revision", "created_at", "configuration"), "BACKUP_CORRUPT")
        if type(data["schema_version"]) is not int or data["schema_version"] != 1 or data["kind"] != "disconnected_configuration_backup" or type(data["created_at"]) is not str:
            raise ConfigurationError("BACKUP_VERSION", "Unsupported backup version/identity")
        _nonnegative_int(data["source_revision"], "BACKUP_CORRUPT")
        validate_configuration(data["configuration"])
        return data

    def restore_preview(self, backup):
        backup = deepcopy(backup)
        data = self._validate_backup(backup)
        plan = self._plan(data["configuration"], "restore", backup)
        if data["store_id"] != plan["store_id"]:
            raise ConfigurationError("BACKUP_IDENTITY", "Backup belongs to another virtual store")
        return plan
