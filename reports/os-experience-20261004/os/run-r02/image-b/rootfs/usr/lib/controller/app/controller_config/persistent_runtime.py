"""Durable step-scale authority for the explicitly isolated LinuxCNC RTL profile.

This is a separate schema for the implemented XYZ calibration subset, not a
cartridge containing the complete machine profile. No motion permission is saved.
"""
from copy import deepcopy
import json
import os
from pathlib import Path
import re
import tempfile
import time
import uuid

from .model import ConfigurationError
from .service import canonical, digest, read_json, export_json
from .runtime import (LinuxCNCRTLAdapter, RuntimeConfigurationService, binding,
                      require_stopped, validate_scales)


def _sealed(payload):
    return {**deepcopy(payload), "sha256": digest(payload)}


def _opened(value, keys, schema):
    if type(value) is not dict or set(value) != set(keys) | {"sha256"} or value.get("schema") != schema:
        raise ConfigurationError("PERSISTENCE_FORMAT", "Unsupported persistent record shape")
    payload = {key: item for key, item in value.items() if key != "sha256"}
    try:
        expected_digest = digest(payload)
    except (ValueError, TypeError, RecursionError) as error:
        raise ConfigurationError('PERSISTENCE_FORMAT', 'Persistent payload cannot be encoded as finite bounded JSON') from error
    if type(value["sha256"]) is not str or value["sha256"] != expected_digest:
        raise ConfigurationError("PERSISTENCE_CHECKSUM", "Persistent record checksum does not match")
    return payload


def _generation(value):
    if type(value) is not int or not 1 <= value <= 4294967295:
        raise ConfigurationError("PERSISTENCE_GENERATION", "Invalid or exhausted persistent generation")


def _sync_directory(path):
    if os.name == 'posix':
        directory = os.open(path, os.O_RDONLY | os.O_DIRECTORY)
        try:
            os.fsync(directory)
        finally:
            os.close(directory)


def _mkdir_durable(path):
    missing=[]
    current=Path(path)
    while not current.exists():
        missing.append(current)
        current=current.parent
    for directory in reversed(missing):
        directory.mkdir(exist_ok=True)
        # Persist the new name in its parent before building descendants.
        _sync_directory(directory.parent)
        _sync_directory(directory)


def _write(path, value):
    """Same-directory replacement, file fsync and Linux parent-directory fsync."""
    path = Path(path)
    if path.is_symlink() or path.parent.is_symlink():
        raise ConfigurationError("PERSISTENCE_PATH", "Symlink authority paths are not supported")
    temporary = None
    try:
        _mkdir_durable(path.parent)
        with tempfile.NamedTemporaryFile(dir=path.parent, prefix=".write-", suffix=".tmp", delete=False) as stream:
            temporary = Path(stream.name)
            stream.write(canonical(value) + b"\n")
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
        temporary = None
        _sync_directory(path.parent)
    except OSError as error:
        raise ConfigurationError("PERSISTENCE_IO", str(error)) from error
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


class PersistentRuntimeService:
    def __init__(self, adapter, directory, *, clock=time.monotonic_ns, checkpoint=None):
        self.adapter, self.clock = adapter, clock
        self.core = RuntimeConfigurationService(adapter, clock=clock)
        self.directory = Path(directory)
        self.journal = self.directory / "authority.json"
        self.witness = self.directory / "generation-witness.json"
        self.checkpoint = checkpoint or (lambda phase: None)

    def _state(self, *, locked=None):
        state = self.adapter.snapshot()
        if not state.get("persistence_required"):
            raise ConfigurationError("PERSISTENCE_NOT_REQUIRED", "The volatile-only laboratory profile cannot activate durable authority")
        if locked is not None:
            require_stopped(state, locked=locked)
        machine_id = state.get("machine_id")
        try:
            if str(uuid.UUID(machine_id)) != machine_id:
                raise ValueError()
        except (ValueError, TypeError, AttributeError) as error:
            raise ConfigurationError("MACHINE_IDENTITY", "A canonical profile machine UUID is required") from error
        if not re.fullmatch(r"[0-9a-f]{64}", state.get("profile_sha256", "")):
            raise ConfigurationError("PROFILE_IDENTITY", "A launch-bound profile fingerprint is required")
        return state

    @staticmethod
    def _record(scales, generation, state):
        _generation(generation)
        return _sealed({"schema": "cnc1-persistent-scales/1", "machine_id": state["machine_id"],
                        "profile_sha256": state["profile_sha256"], "capabilities": state["capabilities"],
                        "generation": generation, "scales": validate_scales(scales, state)})

    @staticmethod
    def _validate_record(record, state):
        data = _opened(record, {"schema", "machine_id", "profile_sha256", "capabilities", "generation", "scales"}, "cnc1-persistent-scales/1")
        _generation(data["generation"])
        for key in ("machine_id", "profile_sha256", "capabilities"):
            if data[key] != state[key]:
                raise ConfigurationError("PERSISTENCE_IDENTITY", "Saved " + key + " does not match the running profile/RTL")
        validate_scales(data["scales"], state)
        return data

    def _read(self, state):
        if not self.journal.exists():
            raise ConfigurationError("PERSISTENCE_MISSING", "No authority journal; explicit init is required for a new machine")
        journal = read_json(self.journal)
        data = _opened(journal, {"schema", "committed", "pending"}, "cnc1-scale-journal/1")
        committed, pending = data["committed"], data["pending"]
        if committed is None and pending is None:
            raise ConfigurationError("PERSISTENCE_FORMAT", "Journal contains no configuration")
        if committed is not None:
            self._validate_record(committed, state)
        if pending is not None:
            self._validate_record(pending, state)
            if pending["generation"] != (committed["generation"] if committed else 0) + 1:
                raise ConfigurationError("PERSISTENCE_GENERATION", "Pending record must advance committed generation exactly once")
        target = pending or committed
        if not self.witness.exists():
            if committed is not None or pending is None or pending["generation"] != 1:
                raise ConfigurationError("PERSISTENCE_WITNESS_MISSING", "Missing independent generation witness")
            witness = None  # recoverable init: first journal fsync happened first
        else:
            witness = read_json(self.witness)
            seen = _opened(witness, {"schema", "machine_id", "profile_sha256", "generation", "record_sha256"}, "cnc1-generation-witness/1")
            _generation(seen["generation"])
            if seen["machine_id"] != state["machine_id"] or seen["profile_sha256"] != state["profile_sha256"]:
                raise ConfigurationError("PERSISTENCE_IDENTITY", "Generation witness belongs to another machine/profile")
            matching = [item for item in (committed, pending) if item is not None and item["generation"] == seen["generation"] and item["sha256"] == seen["record_sha256"]]
            if not matching:
                raise ConfigurationError("PERSISTENCE_CONFLICT", "Authority and generation witness disagree; do not select a backup silently")
        if state["persistence_generation"] > target["generation"] or (
            state["persistence_generation"] == target["generation"] and state["persistence_hash"] != target["sha256"]):
            raise ConfigurationError("PERSISTENCE_ROLLBACK", "Saved generation/hash conflicts with already activated runtime authority")
        return journal, witness, target

    @staticmethod
    def _witness(record):
        return _sealed({"schema": "cnc1-generation-witness/1", "machine_id": record["machine_id"],
                        "profile_sha256": record["profile_sha256"], "generation": record["generation"],
                        "record_sha256": record["sha256"]})

    def status(self):
        state = self._state()
        journal, witness, target = self._read(state)
        return {"runtime": state, "committed": journal["committed"], "pending": journal["pending"],
                "witness": witness, "target": target, "requires_reconciliation":
                bool(journal["pending"] or state["persistence_pending"] or state["config_locked"] or
                     state["scales"] != target["scales"] or state["persistence_generation"] != target["generation"])}

    def preview(self, scales):
        state = self._state(locked=False)
        journal, witness, target = self._read(state)
        if journal["pending"] or state["persistence_pending"] or state["persistence_generation"] != target["generation"] or state["scales"] != target["scales"]:
            raise ConfigurationError("PERSISTENCE_PENDING", "Reconcile saved/runtime authority before another change")
        return {"schema": "cnc1-durable-scale-plan/1", "runtime": self.core.preview(scales),
                "journal_sha256": journal["sha256"], "witness_sha256": witness["sha256"],
                "generation": target["generation"]}

    def _bound_read(self, expected_target, *, deadline=None, expected_runtime=None):
        state = self._state(locked=True)
        if deadline is not None and self.clock() >= deadline:
            raise ConfigurationError("RUNTIME_EXPIRED", "Disk operation exceeded activation deadline; inhibit retained")
        if expected_runtime is not None and binding(state) != binding(expected_runtime):
            raise ConfigurationError("RUNTIME_STALE", "Runtime changed during persistent publication; inhibit retained")
        journal, witness, target = self._read(state)
        current = self._state(locked=True)
        if deadline is not None and self.clock() >= deadline:
            raise ConfigurationError('RUNTIME_EXPIRED', 'Durable read exceeded activation deadline; inhibit retained')
        if binding(current) != binding(state):
            raise ConfigurationError('RUNTIME_STALE', 'Runtime changed during durable readback; inhibit retained')
        if target != expected_target:
            raise ConfigurationError("PERSISTENCE_CONFLICT", "Durable target changed during activation")
        return current, journal, witness

    def _finish(self, target, deadline, expected_runtime):
        state, journal, witness = self._bound_read(target, deadline=deadline, expected_runtime=expected_runtime)
        if witness != self._witness(target):
            _write(self.witness, self._witness(target))
        self.checkpoint("witness_durable")
        state, journal, witness = self._bound_read(target, deadline=deadline, expected_runtime=state)
        committed = self.core._activate_locked(target["scales"], state,
            lambda current: self._bound_read(target, deadline=deadline, expected_runtime=current), deadline=deadline)
        self.checkpoint("runtime_activated")
        _write(self.journal, _sealed({"schema": "cnc1-scale-journal/1", "committed": target, "pending": None}))
        self.checkpoint("committed_durable")
        current, journal, witness = self._bound_read(target, deadline=deadline, expected_runtime=committed)
        if journal["pending"] is not None or witness != self._witness(target) or current["scales"] != target["scales"] or any(current["homed"]):
            raise ConfigurationError("PERSISTENCE_CONFLICT", "Readback/active calibration does not match committed authority")
        self.adapter.transaction(5, current, persistent={"generation": target["generation"], "sha256": target["sha256"]}, deadline=deadline)
        self.checkpoint("gate_committed")
        current, journal, witness = self._bound_read(target, deadline=deadline, expected_runtime=current)
        if current["persistence_pending"] or current["persistence_generation"] != target["generation"] or current["persistence_hash"] != target["sha256"] or current["scales"] != target["scales"] or witness != self._witness(target):
            raise ConfigurationError("PERSISTENCE_CONFLICT", "Compiled persistent acknowledgement does not match durable readback")
        self.adapter.transaction(3, current, deadline=deadline)
        self.checkpoint("released")
        result = self._state(locked=False)
        return {"activated": True, "generation": target["generation"], "record_sha256": target["sha256"],
                "runtime": result, "homing_required": True, "motion_started": False}

    def initialize(self, scales):
        scales = deepcopy(scales)
        with self.adapter.exclusive():
            state = self._state(locked=True)
            if self.journal.exists() or self.witness.exists() or state["persistence_generation"]:
                raise ConfigurationError("PERSISTENCE_EXISTS", "Init cannot overwrite existing or previously activated authority")
            target = self._record(scales, 1, state)
            deadline = self.clock() + 60_000_000_000
            self.adapter.transaction(4, state, deadline=deadline)
            _write(self.journal, _sealed({"schema": "cnc1-scale-journal/1", "committed": None, "pending": target}))
            self.checkpoint("journal_durable")
            return self._finish(target, deadline, state)

    def apply(self, plan):
        plan = deepcopy(plan)
        if type(plan) is not dict or set(plan) != {"schema", "runtime", "journal_sha256", "witness_sha256", "generation"} or plan["schema"] != "cnc1-durable-scale-plan/1":
            raise ConfigurationError("PERSISTENCE_PLAN", "Unsupported durable preview")
        with self.adapter.exclusive():
            state = self._state(locked=False)
            journal, witness, old = self._read(state)
            if journal["pending"] or witness is None or plan["journal_sha256"] != journal["sha256"] or plan["witness_sha256"] != witness["sha256"] or plan["generation"] != old["generation"]:
                raise ConfigurationError("PERSISTENCE_STALE", "Saved authority changed after preview")
            if state["persistence_pending"] or state["scales"] != old["scales"] or state["persistence_generation"] != old["generation"]:
                raise ConfigurationError("PERSISTENCE_PENDING", "Runtime does not match committed authority")
            after = self.core._validate_plan(plan["runtime"], state)
            target = self._record(after, old["generation"] + 1, state)
            self.adapter.transaction(4, state, deadline=plan['runtime']['expires_monotonic_ns'])
            _write(self.journal, _sealed({"schema": "cnc1-scale-journal/1", "committed": old, "pending": target}))
            self.checkpoint("journal_durable")
            return self._finish(target, plan["runtime"]["expires_monotonic_ns"], state)

    def reconcile(self):
        with self.adapter.exclusive():
            state = self._state()
            require_stopped(state, locked=state["config_locked"])
            journal, witness, target = self._read(state)
            deadline=self.clock()+60_000_000_000
            self.adapter.transaction(4, state, deadline=deadline)
            return self._finish(target, deadline, state)

    def recover(self):
        """Explicitly finish a valid journal; never choose a corrupt/older backup."""
        return self.reconcile()


def main(argv=None):
    from .__main__ import JsonArgumentParser
    parser = JsonArgumentParser(prog="python -m controller_config.persistent_runtime", description=__doc__)
    parser.add_argument('--directory', required=True)
    commands = parser.add_subparsers(dest='operation', required=True)
    commands.add_parser('status')
    commands.add_parser('reconcile')
    commands.add_parser('recover')
    initialize = commands.add_parser('init')
    initialize.add_argument('--scales', type=float, nargs=6, required=True)
    preview = commands.add_parser('preview')
    preview.add_argument('--scales', type=float, nargs=6, required=True)
    preview.add_argument('--output')
    apply = commands.add_parser('apply')
    apply.add_argument('plan')
    try:
        args = parser.parse_args(argv)
        service = PersistentRuntimeService(LinuxCNCRTLAdapter(), args.directory)
        if args.operation == 'init':
            value = service.initialize(args.scales)
        elif args.operation == 'preview':
            value = service.preview(args.scales)
            if args.output:
                export_json(args.output, value)
        elif args.operation == 'apply':
            value = service.apply(read_json(args.plan))
        else:
            value = getattr(service, args.operation)()
        print(json.dumps({'schema_version': 1, 'ok': True, 'result': value}, allow_nan=False))
        return 0
    except ConfigurationError as error:
        print(json.dumps({'schema_version': 1, 'ok': False, 'error': error.as_dict()}))
        return 2
    except OSError as error:
        print(json.dumps({'schema_version': 1, 'ok': False,
                          'error': {'code': 'IO_ERROR', 'message': str(error), 'path': ''}}))
        return 2


if __name__ == '__main__':
    raise SystemExit(main())
