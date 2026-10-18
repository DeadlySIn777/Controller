"""Disconnected configuration-cartridge and replacement demonstration.

All module observations are authored Python fixtures. This module never opens a
device, flashes firmware, grants motion permission or changes a physical output.
It wraps ConfigurationService rather than weakening store-bound backup restore.
"""

from copy import deepcopy
import json
from pathlib import Path
import uuid

from .model import ConfigurationError, validate_configuration
from .service import (ConfigurationService, _exclusive_lock, _keys, _unique_pairs,
                      atomic_write, canonical, digest, read_json)


# Two records including JSON envelopes fit within this *modeled* 32 KiB budget.
# No EEPROM part, address layout, endurance or power-loss behavior is qualified.
RECORD_BYTES = 16_384
CARTRIDGE_BYTES = 2 * RECORD_BYTES
MAX_GENERATION = 0xFFFFFFFF
SLOT = "SIM.INPUT_BANK0"


def _machine_id(value):
    try:
        if type(value) is not str or str(uuid.UUID(value)) != value:
            raise ValueError()
    except (ValueError, TypeError, AttributeError) as error:
        raise ConfigurationError("MACHINE_ID", "Expected a canonical machine UUID, independent of compute identity") from error
    return value


def _sealed(payload):
    return {**payload, "integrity_sha256": digest(payload)}


def _unseal(value, code):
    if type(value) is not dict or type(value.get("integrity_sha256")) is not str:
        raise ConfigurationError(code, "Missing integrity digest")
    payload = {key: item for key, item in value.items() if key != "integrity_sha256"}
    try:
        valid = digest(payload) == value["integrity_sha256"]
    except (TypeError, ValueError, RecursionError) as error:
        raise ConfigurationError(code, "Invalid data in checksummed record") from error
    if not valid:
        raise ConfigurationError(code, "Digest mismatch; checksums detect corruption, not malicious changes")
    return payload


def _bounded_raw(value):
    try:
        raw = canonical(value) + b"\n"
    except (ValueError, TypeError, RecursionError) as error:
        raise ConfigurationError("CARTRIDGE_FORMAT", "Invalid JSON value") from error
    if len(raw) > RECORD_BYTES:
        raise ConfigurationError("CARTRIDGE_SIZE", "Encoded record exceeds its 16 KiB modeled slot")
    return raw


def _read_record(path):
    try:
        with path.open("rb") as stream:
            raw = stream.read(RECORD_BYTES + 1)
        if len(raw) > RECORD_BYTES:
            raise ConfigurationError("CARTRIDGE_SIZE", "Slot exceeds its modeled capacity")
        value = json.loads(raw.decode("utf-8"), object_pairs_hook=_unique_pairs,
                           parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except ConfigurationError:
        raise
    except (UnicodeError, ValueError, RecursionError) as error:
        raise ConfigurationError("CARTRIDGE_FORMAT", "Incomplete or invalid slot JSON") from error
    except OSError as error:
        raise ConfigurationError("CARTRIDGE_IO", str(error)) from error
    validated = _validate_record(value)
    if raw != _bounded_raw(validated):
        raise ConfigurationError("CARTRIDGE_FRAMING", "Slot must contain its exact complete canonical record and final newline")
    return validated


def _validate_record(value):
    _bounded_raw(value)
    data = _unseal(value, "CARTRIDGE_DIGEST")
    if type(data.get("schema_version")) is not int or data.get("schema_version") != 1 or data.get("kind") != "virtual_machine_cartridge":
        raise ConfigurationError("CARTRIDGE_VERSION", "Unsupported cartridge format")
    _keys(data, ("schema_version", "kind", "generation", "machine_id", "configuration"), "CARTRIDGE_FORMAT")
    generation = data["generation"]
    if type(generation) is not int or not 1 <= generation <= MAX_GENERATION:
        raise ConfigurationError("CARTRIDGE_GENERATION", "Generation must be an unsigned nonzero 32-bit integer")
    _machine_id(data["machine_id"])
    configuration = data["configuration"]
    if type(configuration) is dict and (type(configuration.get("schema_version")) is not int or configuration.get("schema_version") != 1 or configuration.get("kind") != "disconnected_simulation_configuration"):
        raise ConfigurationError("CARTRIDGE_VERSION", "Unsupported embedded configuration format")
    validate_configuration(data["configuration"])
    _assigned_inputs(data["configuration"])
    return deepcopy(value)


def _assigned_inputs(configuration):
    assignments = []
    supported = {f"SIM.DI{i}" for i in range(8)}
    for device in configuration["devices"]:
        for connection in device["required_connections"]:
            if connection["role"] == "home_input":
                if connection["resource"] not in supported:
                    raise ConfigurationError("RECOVERY_TOPOLOGY", "Recovery fixture covers only the first eight virtual inputs")
                assignments.append({"device": device["identity"]["instance_id"], **deepcopy(connection)})
    return assignments


class Cartridge:
    """Two file-backed slots; normal writes touch only the older/invalid slot.

    Interrupted writes deliberately truncate the target *virtual* slot. The
    other slot survives. This is a fault model, not an EEPROM driver or proof of
    filesystem/device durability. A single cooperative lock serializes writers.
    """
    def __init__(self, directory):
        self.directory = Path(directory).resolve()

    @property
    def lock_path(self):
        return self.directory / "cartridge-operation"

    def slot_path(self, index):
        if type(index) is not int or index not in (0, 1):
            raise ConfigurationError("CARTRIDGE_SLOT", "Only slots zero and one exist")
        return self.directory / f"record-{index}.json"

    def _scan(self):
        records, failures = [], []
        for index in (0, 1):
            path = self.slot_path(index)
            if not path.exists():
                failures.append({"slot": index, "code": "MISSING"})
                continue
            try:
                records.append((index, _read_record(path)))
            except ConfigurationError as error:
                if error.code == "CARTRIDGE_VERSION":
                    raise  # A valid future-format record is not a torn write.
                failures.append({"slot": index, "code": error.code})
        return records, failures

    def load(self, expected_machine_id):
        _machine_id(expected_machine_id)
        records, failures = self._scan()
        if not records:
            raise ConfigurationError("CARTRIDGE_NO_VALID_RECORD", "Neither cartridge slot has a valid record")
        # A fully valid foreign record is not silently ignored as corrupt.
        if any(record["machine_id"] != expected_machine_id for _, record in records):
            raise ConfigurationError("CARTRIDGE_MACHINE", "Cartridge records do not all match the expected machine")
        if len(records) == 2 and records[0][1]["generation"] == records[1][1]["generation"] and records[0][1] != records[1][1]:
            raise ConfigurationError("CARTRIDGE_AMBIGUOUS", "Equal generations contain different valid settings")
        index, record = max(records, key=lambda pair: pair[1]["generation"])
        return {"slot": index, "record": record, "record_sha256": digest(record),
                "encoded_bytes": len(_bounded_raw(record)), "invalid_slots": failures,
                "modeled_capacity_bytes": CARTRIDGE_BYTES, "simulation_only": True}

    def save(self, machine_id, configuration, expected_generation, interrupt_after_bytes=None):
        """Compare-and-save; a non-None interruption is explicit fault injection."""
        configuration = deepcopy(configuration)
        _machine_id(machine_id)
        if type(expected_generation) is not int or not 0 <= expected_generation <= MAX_GENERATION:
            raise ConfigurationError("CARTRIDGE_GENERATION", "Invalid expected generation")
        if interrupt_after_bytes is not None and (type(interrupt_after_bytes) is not int or interrupt_after_bytes < 0):
            raise ConfigurationError("CARTRIDGE_INTERRUPTION", "Interruption position must be a nonnegative integer")
        validate_configuration(configuration)
        _assigned_inputs(configuration)
        self.directory.mkdir(parents=True, exist_ok=True)
        with _exclusive_lock(self.lock_path):
            records, _ = self._scan()
            if records:
                current = self.load(machine_id)
                generation, target = current["record"]["generation"], 1 - current["slot"]
            else:
                if any(self.slot_path(i).exists() for i in (0, 1)):
                    raise ConfigurationError("CARTRIDGE_NO_VALID_RECORD", "Refusing to overwrite a cartridge with no readable record")
                generation, target = 0, 0
            if generation != expected_generation:
                raise ConfigurationError("CARTRIDGE_STALE", "Configuration generation changed; inspect and retry")
            if generation == MAX_GENERATION:
                raise ConfigurationError("CARTRIDGE_GENERATION", "Generation exhausted; no wrap is permitted")
            record = _sealed({"schema_version": 1, "kind": "virtual_machine_cartridge",
                              "generation": generation + 1, "machine_id": machine_id,
                              "configuration": deepcopy(configuration)})
            raw = _bounded_raw(record)
            if interrupt_after_bytes is not None:
                if interrupt_after_bytes >= len(raw):
                    raise ConfigurationError("CARTRIDGE_INTERRUPTION", "Fault injection must stop before the complete record")
                self.slot_path(target).write_bytes(raw[:interrupt_after_bytes])
                return {"committed": False, "target_slot": target, "generation_attempted": generation + 1,
                        "injected_partial_bytes": interrupt_after_bytes, "simulation_only": True}
            atomic_write(self.slot_path(target), record)
            return {"committed": True, "generation": generation + 1, "slot": target,
                    "encoded_bytes": len(raw), "record_sha256": digest(record), "simulation_only": True}


def module_fixture(identity):
    """Authoritative only within this disconnected fixture, never imported caps."""
    base = {"slot": SLOT, "model": "virtual-input-bank-8", "hardware_revision": "virtual-r1",
            "interface_abi": 1, "firmware_revision": "none-passive-fixture",
            "simulation_only": True, "resources": [f"SIM.DI{i}" for i in range(8)],
            "signal_type": "contact_to_24v", "voltage_v": 24, "maximum_current_a": 0.005,
            "maximum_rate_hz": 100,
            "factory_calibration": {"input_filter_clock_correction_ppm": 15,
                                    "evidence": "illustrative_fixture_not_measured"}}
    modules = {}
    for name, serial in (("input-original", "SIM-IN-001"), ("input-replacement", "SIM-IN-002"),
                         ("input-wrong-voltage", "SIM-IN-003"), ("input-wrong-abi", "SIM-IN-004"),
                         ("input-short-bank", "SIM-IN-005")):
        modules[name] = {**deepcopy(base), "fixture_id": name, "serial": serial}
    modules["input-replacement"]["factory_calibration"]["input_filter_clock_correction_ppm"] = -22
    modules["input-wrong-voltage"]["voltage_v"] = 3.3
    modules["input-wrong-voltage"]["signal_type"] = "logic_3v3"
    modules["input-wrong-abi"]["interface_abi"] = 2
    modules["input-short-bank"]["resources"] = ["SIM.DI0"]
    if type(identity) is not str or identity not in modules:
        raise ConfigurationError("MODULE_UNKNOWN", "Module must come from the built-in virtual inventory")
    return deepcopy(modules[identity])


def _inventory(value, configuration):
    _keys(value, (SLOT,), "MODULE_INVENTORY")
    module = module_fixture(value[SLOT])
    if module["interface_abi"] != 1 or module["hardware_revision"] != "virtual-r1":
        raise ConfigurationError("MODULE_INCOMPATIBLE", "Unsupported input-bank interface/revision")
    for assignment in _assigned_inputs(configuration):
        if (assignment["resource"] not in module["resources"] or
                assignment["signal_type"] != module["signal_type"] or
                assignment["voltage_v"] != module["voltage_v"] or
                assignment["current_a"] > module["maximum_current_a"] or
                assignment["rate_hz"] > module["maximum_rate_hz"]):
            raise ConfigurationError("MODULE_INCOMPATIBLE", "Replacement cannot meet the retained input assignments")
    return {SLOT: module}


class RecoveryService:
    """Common file-only recovery API, delegating configuration writes to the service.

    A sidecar binds a machine UUID to this new compute store. `reserved` survives
    an interrupted bootstrap; retry is allowed only for its identical cartridge
    record/configuration. Inventories and stopped state are fixture observations.
    """
    def __init__(self, service, cartridge, expected_machine_id, inventory_provider):
        if not isinstance(service, ConfigurationService) or not isinstance(cartridge, Cartridge):
            raise ConfigurationError("RECOVERY_SERVICE", "Expected shared configuration service and cartridge")
        if not callable(inventory_provider):
            raise ConfigurationError("MODULE_INVENTORY", "Expected a fixture inventory provider")
        self.service, self.cartridge = service, cartridge
        self.machine_id = _machine_id(expected_machine_id)
        self.inventory_provider = inventory_provider
        self.binding_path = Path(str(service.path) + ".machine-binding.json")

    def _binding(self, store):
        if not self.binding_path.exists():
            return None
        sealed = read_json(self.binding_path)
        binding = _unseal(sealed, "BINDING_CORRUPT")
        _keys(binding, ("schema_version", "kind", "machine_id", "store_id", "stage",
                        "cartridge_generation", "cartridge_sha256", "configuration_sha256", "inventory",
                        "base_revision", "committed_revision"), "BINDING_CORRUPT")
        if type(binding["schema_version"]) is not int or binding["schema_version"] != 1 or binding["kind"] != "virtual_machine_store_binding" or binding["stage"] not in ("reserved", "applied"):
            raise ConfigurationError("BINDING_CORRUPT", "Invalid binding format")
        if binding["machine_id"] != self.machine_id or binding["store_id"] != store["store_id"]:
            raise ConfigurationError("BINDING_IDENTITY", "Machine or compute store does not match its persistent binding")
        if type(binding["cartridge_generation"]) is not int or not 1 <= binding["cartridge_generation"] <= MAX_GENERATION:
            raise ConfigurationError("BINDING_CORRUPT", "Invalid bound generation")
        if any(type(binding[key]) is not int or binding[key] < 0 for key in ("base_revision", "committed_revision")) or binding["committed_revision"] not in (binding["base_revision"], binding["base_revision"] + 1):
            raise ConfigurationError("BINDING_CORRUPT", "Invalid bound store revisions")
        for key in ("cartridge_sha256", "configuration_sha256"):
            if type(binding[key]) is not str or len(binding[key]) != 64 or any(c not in "0123456789abcdef" for c in binding[key]):
                raise ConfigurationError("BINDING_CORRUPT", "Invalid bound digest")
        _keys(binding["inventory"], (SLOT,), "BINDING_CORRUPT")
        fixture = module_fixture(binding["inventory"][SLOT].get("fixture_id") if type(binding["inventory"][SLOT]) is dict else None)
        if binding["inventory"][SLOT] != fixture:
            raise ConfigurationError("BINDING_CORRUPT", "Saved inventory does not match the authored module fixture")
        return binding

    def preview(self, operation):
        if operation not in ("bootstrap", "replace_input_bank"):
            raise ConfigurationError("RECOVERY_OPERATION", "Only bootstrap and replace_input_bank are modeled")
        selected = self.cartridge.load(self.machine_id)
        record = selected["record"]
        config = record["configuration"]
        store = self.service.show()
        binding = self._binding(store)
        inventory = _inventory(deepcopy(self.inventory_provider()), config)
        if operation == "bootstrap":
            if binding is not None and binding["stage"] != "reserved":
                raise ConfigurationError("RECOVERY_NOT_BLANK", "Compute store has already completed recovery")
            if binding is None and (store["revision"] != 0 or store["configuration"] is not None):
                raise ConfigurationError("RECOVERY_NOT_BLANK", "Bootstrap requires a new empty compute store")
            if binding is not None:
                blank_reserved = store["revision"] == binding["base_revision"] == 0 and store["configuration"] is None
                applied_reserved = store["revision"] == binding["committed_revision"] == 1 and store["configuration_sha256"] == binding["configuration_sha256"]
                if (binding["cartridge_sha256"] != selected["record_sha256"] or binding["inventory"] != inventory or
                        not (blank_reserved or applied_reserved)):
                    raise ConfigurationError("RECOVERY_RESERVATION", "Interrupted bootstrap must resume with its identical configuration and module inventory")
        else:
            if binding is None or binding["stage"] != "applied":
                raise ConfigurationError("RECOVERY_UNBOUND", "Input replacement requires a previously bound machine store")
            if binding["cartridge_generation"] != record["generation"] or binding["cartridge_sha256"] != selected["record_sha256"]:
                raise ConfigurationError("RECOVERY_RECONCILE", "Cartridge differs from the bound generation; explicit reconciliation is not yet implemented")
            if store["revision"] != binding["committed_revision"] or store["configuration_sha256"] != binding["configuration_sha256"]:
                raise ConfigurationError("RECOVERY_RECONCILE", "Shared-service edits changed the store since binding; reconciliation is required")
            if store["configuration"] != config:
                raise ConfigurationError("RECOVERY_CONFIG_MISMATCH", "Cartridge and current machine settings differ; reconcile explicitly")
            if binding["inventory"] == inventory:
                raise ConfigurationError("RECOVERY_NO_REPLACEMENT", "No different input-bank identity was observed")
        configuration_plan = self.service.preview(config)
        affected = _assigned_inputs(config)
        checks = ([{"device": row["device"], "resource": row["resource"], "checks": ["wiring", "polarity"], "status": "pending"}
                   for row in affected] if operation == "replace_input_bank" else
                  [{"device": device["identity"]["instance_id"], "checks": [check["id"] for check in device["commissioning_checks"]], "status": "pending"}
                   for device in config["devices"]])
        return {"schema_version": 1, "kind": "disconnected_recovery_plan", "operation": operation,
                "machine_id": self.machine_id, "cartridge_generation": record["generation"],
                "cartridge_sha256": selected["record_sha256"], "binding_sha256": digest(binding),
                "inventory": inventory, "configuration_plan": configuration_plan,
                "verification_required": checks, "outputs_inhibited": True,
                "homed": False, "run_permission": False, "simulation_only": True}

    def apply(self, plan):
        if type(plan) is not dict or type(plan.get("operation")) is not str:
            raise ConfigurationError("RECOVERY_PLAN", "Invalid recovery plan")
        # A preview itself has no writes. On apply all dependencies are observed
        # again while cartridge writers and other recovery writers are excluded.
        with _exclusive_lock(Path(str(self.binding_path) + ".operation")):
            with _exclusive_lock(self.cartridge.lock_path):
                fresh = self.preview(plan["operation"])
                if plan != fresh:
                    raise ConfigurationError("RECOVERY_STALE", "Cartridge, inventory, binding, store, runtime epoch or plan changed")
                config_plan = fresh["configuration_plan"]
                binding = {"schema_version": 1, "kind": "virtual_machine_store_binding",
                           "machine_id": self.machine_id, "store_id": config_plan["store_id"], "stage": "reserved",
                           "cartridge_generation": fresh["cartridge_generation"],
                           "cartridge_sha256": fresh["cartridge_sha256"],
                           "configuration_sha256": config_plan["candidate_sha256"], "inventory": fresh["inventory"],
                           "base_revision": config_plan["base_revision"],
                           "committed_revision": config_plan["base_revision"] + int(bool(config_plan["changes"]))}
                if plan["operation"] == "bootstrap" and not self.binding_path.exists():
                    atomic_write(self.binding_path, _sealed(binding))
                # Recheck the virtual module observations immediately before
                # delegating the sole configuration write to the shared service.
                if _inventory(deepcopy(self.inventory_provider()), config_plan["configuration"]) != fresh["inventory"]:
                    raise ConfigurationError("RECOVERY_STALE", "Module inventory changed before commit")
                result = self.service.apply(config_plan, actor=f"cartridge-recovery:{self.machine_id}:g{fresh['cartridge_generation']}")
                # The ordinary service releases its store lock after commit.
                # Reacquire it and detect any intervening writer before receipt
                # finalization; this is not a multi-file atomic transaction.
                with _exclusive_lock(self.service.path):
                    committed = self.service.show()
                    runtime = self.service._safe_state()
                    if (committed["store_id"] != binding["store_id"] or committed["revision"] != binding["committed_revision"] or
                            committed["configuration_sha256"] != binding["configuration_sha256"] or
                            committed["configuration"] != config_plan["configuration"] or runtime.epoch != config_plan["runtime_epoch"] or
                            _inventory(deepcopy(self.inventory_provider()), config_plan["configuration"]) != fresh["inventory"]):
                        raise ConfigurationError("RECOVERY_STALE", "Store, runtime or inventory changed before receipt finalization")
                    if fresh["operation"] == "replace_input_bank":
                        # The configuration is unchanged, so the shared apply
                        # wrote no audit entry. Record the swap durably in the
                        # shared store before the binding forgets the old serial.
                        previous = self._binding(committed)["inventory"][SLOT]["serial"]
                        self.service._record_event_locked(
                            "replace_module",
                            f"cartridge-recovery:{self.machine_id}:g{fresh['cartridge_generation']}:"
                            f"{SLOT}:{previous}->{fresh['inventory'][SLOT]['serial']}",
                            committed["revision"], committed["configuration_sha256"])
                    binding["stage"] = "applied"
                    atomic_write(self.binding_path, _sealed(binding))
                return {"operation": fresh["operation"], "machine_id": self.machine_id,
                        "configuration_result": result, "cartridge_generation": fresh["cartridge_generation"],
                        "assignments_retained": True, "machine_calibration_values_retained": True,
                        "replacement_module": deepcopy(fresh["inventory"][SLOT]),
                        "verification_required": fresh["verification_required"], "outputs_inhibited": True,
                        "homed": False, "run_permission": False, "physical_commands": 0,
                        "simulation_only": True}
