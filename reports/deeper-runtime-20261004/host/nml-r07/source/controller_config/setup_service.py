"""Versioned IS-2 setup laboratory. No transport, hardware observation or motion API.

SIM terminals and equipment below are authored examples, never physical pin guidance.
Saved user selections are not commissioning evidence. The historical six/two service
and its stores are deliberately separate. Checksums detect corruption, not authorship.
"""
from copy import deepcopy
from contextlib import contextmanager
from datetime import datetime, timezone
from decimal import Decimal, localcontext
import math
import errno
import os
from pathlib import Path
import uuid

from .model import ConfigurationError
from .service import (_actor, _diff, _seal, _verify_seal,
                      atomic_write, canonical, digest, read_json)


SCHEMA = "is2-disconnected-setup/1"
CATALOG_VERSION = "is2-simulation-catalog/1"
HISTORY_LIMIT = 20
REQUEST_LIMIT = 100
AUDIT_LIMIT = 200
MAX_REVISION = 2**53 - 1
GUARDS = {"simulation_only": True, "physical_commissioning_complete": False,
          "motion_authorized": False, "outputs_inhibited": True,
          "homed": False, "machine_commands": []}
PROFILES = {
    "sim-mill-3axis": {"title": "Simulation: three-axis mill", "motor_axes": ["x", "y", "z"]},
    "sim-gantry-4motor": {"title": "Simulation: dual-motor X gantry", "motor_axes": ["x", "x", "y", "z"]},
    "sim-machine-8motor": {"title": "Simulation: eight motor channels", "motor_axes": [f"j{i}" for i in range(8)]},
    "sim-machine-12motor": {"title": "Simulation: twelve motor channels", "motor_axes": [f"j{i}" for i in range(12)]},
}
FACTS = ("motor_steps_per_revolution", "microsteps", "gear_motor_revolutions",
         "gear_load_revolutions", "travel_per_load_revolution", "max_velocity_units_per_second")
TIMINGS = ("step_high_ns", "step_low_ns", "dir_setup_ns", "dir_hold_ns")
MOTOR_KEYS = {"id", "axis", "resource", "equipment_profile", "unit", *FACTS, *TIMINGS,
              "step_active_high", "dir_inverted"}
DRAFT_KEYS = {"schema_version", "kind", "simulation_only", "profile_id", "machine_name",
              "motors", "inputs", "outputs", "encoders"}
LIMITS = {
    "motor_steps_per_revolution": (1, 1000000), "microsteps": (1, 1024),
    "gear_motor_revolutions": (0.000001, 1000000), "gear_load_revolutions": (0.000001, 1000000),
    "travel_per_load_revolution": (0.000001, 1000000), "max_velocity_units_per_second": (0.000001, 1000000),
}


def _error(code, message, path=""):
    raise ConfigurationError(code, message, path)


@contextmanager
def _exclusive_lock(path):
    """Local OS-owned lock; process death releases ownership, not the file.

    Never unlink the stable inode/path: replacing it could let a second writer
    lock a different file while a first writer still owns the original lock.
    Older setup builds used an O_EXCL sentinel; its presence fails closed so
    an interrupted or still-running older writer is not silently bypassed.
    """
    legacy = Path(str(path) + ".lock")
    lock_path = Path(str(path) + ".setup.lock")
    if legacy.exists():
        _error("STORE_BUSY", "A previous setup lock exists; inspect the older writer before migrating")
    descriptor = os.open(lock_path, os.O_CREAT | os.O_RDWR | getattr(os, "O_BINARY", 0), 0o600)
    locked = False
    try:
        try:
            if os.name == "nt":
                import msvcrt
                # Windows permits byte-range locks beyond EOF; initialize the
                # byte only after acquiring ownership, avoiding an init race.
                msvcrt.locking(descriptor, msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(descriptor, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as error:
            if error.errno in (errno.EACCES, errno.EAGAIN, errno.EDEADLK):
                _error("STORE_BUSY", "Another local setup writer holds the store lock")
            raise
        locked = True
        if legacy.exists():
            _error("STORE_BUSY", "A previous setup lock appeared; inspect the older writer before migrating")
        if os.fstat(descriptor).st_size == 0:
            os.write(descriptor, b"\0")
        yield
    finally:
        try:
            if locked:
                if os.name == "nt":
                    os.lseek(descriptor, 0, os.SEEK_SET)
                    msvcrt.locking(descriptor, msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(descriptor, fcntl.LOCK_UN)
        finally:
            os.close(descriptor)


def _object(value, keys, path):
    if type(value) is not dict or set(value) != set(keys):
        _error("SETUP_SCHEMA", "Unknown or missing fields", path)


def _text(value, path, maximum=120):
    if type(value) is not str or not value.strip() or len(value) > maximum or any(ord(c) < 32 for c in value):
        _error("SETUP_TEXT", "Expected a nonempty printable text label", path)
    return value


def _number(value, path, low, high, integer=False):
    if ((type(value) is not int if integer else type(value) not in (int, float)) or
            (type(value) is float and not math.isfinite(value)) or not low <= value <= high):
        _error("SETUP_NUMBER", f"Expected {'integer' if integer else 'finite number'} from {low} to {high}", path)
    return Decimal(str(value))


def _boolean(value, path):
    if type(value) is not bool:
        _error("SETUP_BOOLEAN", "Expected a Boolean", path)


def _array(value, path, maximum):
    if type(value) is not list or len(value) > maximum:
        _error("SETUP_ARRAY", f"Expected a list of at most {maximum} items", path)


def _issue(code, message, path):
    return {"code": code, "message": message, "path": path}


def equipment_profiles():
    common = {"simulation_only": True, "physical_qualified": False,
              "provenance": "authored_simulation_fixture", "revision": CATALOG_VERSION}
    return {
        "sim-step-drive-v1": {**common, "kind": "step_dir", "signal_type": "differential_5v",
            "minimum_step_high_ns": 2500, "minimum_step_low_ns": 2500,
            "minimum_dir_setup_ns": 5000, "minimum_dir_hold_ns": 5000,
            "maximum_rate_hz": 100000, "enable": "dedicated_simulation_signal",
            "alarm": "dedicated_simulation_signal"},
        "sim-24v-switch-v1": {**common, "kind": "digital_input", "voltage_v": 24},
        "sim-smart-output-v1": {**common, "kind": "digital_output", "voltage_v": 24,
            "maximum_current_a": 0.5, "maximum_group_current_a": 2},
        "sim-abz-5v-v1": {**common, "kind": "abz", "signal_type": "differential_5v"},
    }


def profiles():
    return {key: {**deepcopy(value), "simulation_only": True, "physical_qualified": False}
            for key, value in PROFILES.items()}


def capabilities():
    resources = []
    for i in range(12):
        resources.append({"id": f"SIM.M{i}", "kind": "step_dir", "label": f"M{i+1}",
            "terminals": [f"SIM.M{i}.{s}" for s in ("STEP+", "STEP-", "DIR+", "DIR-", "EN", "ALM")],
            "enable_resource": f"SIM.M{i}.EN", "alarm_resource": f"SIM.M{i}.ALM",
            "maximum_simulation_rate_hz": 100000})
    for i in range(4):
        resources.append({"id": f"SIM.ABZ{i}", "kind": "abz", "label": f"ABZ{i+1}",
            "terminals": [f"SIM.ABZ{i}.{s}" for s in ("A+", "A-", "B+", "B-", "Z+", "Z-")]})
    for i in range(24):
        resources.append({"id": f"SIM.DI{i}", "kind": "digital_input", "label": f"IN{i+1}",
            "terminals": [f"SIM.DI{i}.IN", f"SIM.DI{i}.REF"], "voltage_v": 24})
    for i in range(16):
        resources.append({"id": f"SIM.DO{i}", "kind": "digital_output", "label": f"OUT{i+1}",
            "terminals": [f"SIM.DO{i}.OUT", f"SIM.DO{i}.REF"], "group": i // 4,
            "maximum_current_a": 0.5, "maximum_group_current_a": 2, "voltage_v": 24})
    for resource in resources:
        resource.update(simulation_only=True, observed=False, physically_qualified=False)
    return {"schema_version": 1, "catalog_version": CATALOG_VERSION,
        "identity": {"id": "SIM.motherboard-12m-4enc", "required_topology": "motherboard-12m-4enc",
                     "simulation_only": True, "observed": False},
        "requirements": {"motor_channels": 12, "individual_motor_enables": 12,
            "individual_motor_alarms": 12, "abz_encoders": 4, "general_di": 24, "general_do": 16,
            "do_channel_current_a": 0.5, "do_four_channel_group_current_a": 2,
            "fault_to_inhibit_maximum_ms": 20,
            "additional_interfaces": ["fast_probe", "frequency_input", "mpg_pendant", "pwm",
                "process_contact", "analog_input", "analog_output", "rs485", "can",
                "watchdog_permission", "power_protection", "status_indicators", "compute",
                "esp", "protected_settings_storage", "accessory_expansion"]},
        "resources": resources, "additional_interface_status": "required_but_not_configurable_in_this_setup_fixture",
        "source_contract": "docs/MOTHERBOARD_IS2.md; source representation is not live observation or qualification",
        "physical_pin_guidance": False, "physical_equipment_discovered": False,
        "removable_units_required": ["qualified_compute", "qualified_esp", "qualified_settings_storage"],
        "soldered_region_service": "whole_motherboard_exchange",
        "notice": "SIM labels and 100 kHz model ceiling are authored fixture limits, not hardware ratings. No motion API.",
        **deepcopy(GUARDS)}


def _catalog_digest():
    return digest({"capabilities": capabilities(), "profiles": profiles(), "equipment": equipment_profiles()})


def draft_template(profile_id):
    if type(profile_id) is not str or profile_id not in PROFILES:
        _error("SETUP_UNSUPPORTED_PROFILE", "Choose an explicitly supported simulation machine profile", "$.profile_id")
    motors = []
    for i, axis in enumerate(PROFILES[profile_id]["motor_axes"]):
        motors.append({"id": f"m{i}", "axis": axis, "resource": f"SIM.M{i}",
            "equipment_profile": "sim-step-drive-v1", "unit": "mm", **{key: None for key in FACTS},
            **{key: 5000 for key in TIMINGS}, "step_active_high": True, "dir_inverted": False})
    return {"schema_version": 1, "kind": "is2_disconnected_setup_draft", "simulation_only": True,
        "profile_id": profile_id, "machine_name": PROFILES[profile_id]["title"],
        "motors": motors, "inputs": [], "outputs": [], "encoders": []}


def example_draft(profile_id):
    """Explicit opt-in demonstration values; never inferred from actual equipment."""
    draft = draft_template(profile_id)
    draft["machine_name"] = "SIMULATION EXAMPLE: " + PROFILES[profile_id]["title"]
    for motor in draft["motors"]:
        motor.update(motor_steps_per_revolution=200, microsteps=16,
                     gear_motor_revolutions=1, gear_load_revolutions=1,
                     travel_per_load_revolution=5, max_velocity_units_per_second=10)
    return draft


def schema():
    """The JSON schema and validator share field names and numeric bounds."""
    text = {"type": "string", "minLength": 1, "maxLength": 120}
    def obj(properties):
        return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}
    motor = {key: deepcopy(text) for key in ("id", "axis", "resource", "equipment_profile")}
    motor["unit"] = {"enum": ["mm", "in"]}
    for key, (low, high) in LIMITS.items():
        motor[key] = {"type": ["integer" if key in FACTS[:2] else "number", "null"], "minimum": low, "maximum": high}
    for key in TIMINGS:
        motor[key] = {"type": "integer", "minimum": 1, "maximum": 1000000000}
    motor.update(step_active_high={"type": "boolean"}, dir_inverted={"type": "boolean"})
    connections = {}
    for name, maximum in (("inputs", 24), ("outputs", 16), ("encoders", 4)):
        fields = {key: deepcopy(text) for key in ("resource", "role", "equipment_profile")}
        if name in ("inputs", "outputs"):
            fields["voltage_v"] = {"type": "number", "minimum": 0, "maximum": 60}
        if name == "outputs":
            fields["current_a"] = {"type": "number", "minimum": 0, "maximum": 10}
        if name == "encoders":
            fields["counts_per_revolution"] = {"type": ["integer", "null"], "minimum": 1, "maximum": 1000000000}
        connections[name] = {"type": "array", "maxItems": maximum, "items": obj(fields)}
    result = obj({"schema_version": {"type": "integer", "const": 1},
        "kind": {"const": "is2_disconnected_setup_draft"}, "simulation_only": {"const": True},
        "profile_id": deepcopy(text), "machine_name": deepcopy(text),
        "motors": {"type": "array", "minItems": 1, "maxItems": 12, "items": obj(motor)}, **connections})
    result.update({"$schema": "https://json-schema.org/draft/2020-12/schema", "$id": "urn:controller:is2-disconnected-setup:1"})
    return result


def validate_draft(draft, require_complete=False):
    """Malformed input raises; missing facts and unsupported selections are explicit blockers.

    Complete validation still means only a usable simulation configuration. It never
    accepts a caller's declaration of observed equipment or physical commissioning.
    """
    _object(draft, DRAFT_KEYS, "$")
    if type(draft["schema_version"]) is not int or draft["schema_version"] != 1 or draft["kind"] != "is2_disconnected_setup_draft" or draft["simulation_only"] is not True:
        _error("SETUP_VERSION", "Requires the explicit IS-2 disconnected simulation schema", "$")
    _text(draft["profile_id"], "$.profile_id")
    _text(draft["machine_name"], "$.machine_name")
    missing, blockers, calculations, wiring = [], [], [], []
    expected = PROFILES.get(draft["profile_id"])
    if expected is None:
        blockers.append(_issue("SETUP_UNSUPPORTED_PROFILE", "No approved simulation profile with this exact identifier", "$.profile_id"))
    _array(draft["motors"], "$.motors", 12)
    if not draft["motors"] or (expected and len(draft["motors"]) != len(expected["motor_axes"])):
        blockers.append(_issue("SETUP_TOPOLOGY", "Motor count does not match the selected profile", "$.motors"))
    resources = {r["id"]: r for r in capabilities()["resources"]}
    equipment = equipment_profiles()
    used, seen_ids = {}, set()

    def assign(resource_id, kind, path, owner):
        _text(resource_id, path)
        resource = resources.get(resource_id)
        if resource is None or resource["kind"] != kind:
            blockers.append(_issue("SETUP_RESOURCE", f"Select a {kind} resource from this simulation catalog", path))
            return None
        if resource_id in used:
            blockers.append(_issue("SETUP_RESOURCE_CONFLICT", f"Resource already assigned to {used[resource_id]}", path))
        used[resource_id] = owner
        wiring.append({"owner": owner, "resource": resource_id, "terminals": resource["terminals"],
                       "simulation_only": True, "physical_wiring_verified": False})
        return resource

    def select(identifier, kind, path):
        _text(identifier, path)
        item = equipment.get(identifier)
        if item is None or item["kind"] != kind:
            blockers.append(_issue("SETUP_UNSUPPORTED_EQUIPMENT", "Exact simulation equipment profile is unsupported; no substitute inferred", path))
            return None
        return item

    for i, motor in enumerate(draft["motors"]):
        path = f"$.motors[{i}]"
        _object(motor, MOTOR_KEYS, path)
        for key in ("id", "axis", "unit"):
            _text(motor[key], path + "." + key)
        if motor["id"] in seen_ids:
            blockers.append(_issue("SETUP_MOTOR_ID", "Motor identifiers must be unique", path + ".id"))
        seen_ids.add(motor["id"])
        if expected and (motor["id"] != f"m{i}" or i >= len(expected["motor_axes"]) or motor["axis"] != expected["motor_axes"][i]):
            blockers.append(_issue("SETUP_TOPOLOGY", "Motor identity/axis does not match the selected profile", path))
        if motor["unit"] not in ("mm", "in"):
            _error("SETUP_UNIT", "Specify mm or in explicitly", path + ".unit")
        resource = assign(motor["resource"], "step_dir", path + ".resource", motor["id"])
        selected = select(motor["equipment_profile"], "step_dir", path + ".equipment_profile")
        values = {}
        for key, bounds in LIMITS.items():
            if motor[key] is None:
                missing.append(_issue("SETUP_MISSING_FACT", f"Enter {key.replace('_', ' ')} for {motor['id']}; this is a selection, not measured evidence", path + "." + key))
            else:
                values[key] = _number(motor[key], path + "." + key, *bounds, integer=key in FACTS[:2])
        for key in TIMINGS:
            value = _number(motor[key], path + "." + key, 1, 1000000000, integer=True)
            if selected and value < selected["minimum_" + key]:
                blockers.append(_issue("SETUP_TIMING", "Timing is shorter than the selected simulation drive minimum", path + "." + key))
        _boolean(motor["step_active_high"], path + ".step_active_high")
        _boolean(motor["dir_inverted"], path + ".dir_inverted")
        if len(values) == len(FACTS) and selected and resource:
            with localcontext() as context:
                context.prec = 40
                pulses = values["motor_steps_per_revolution"] * values["microsteps"]
                ratio = values["gear_motor_revolutions"] / values["gear_load_revolutions"]
                scale = pulses * ratio / values["travel_per_load_revolution"]
                rate = scale * values["max_velocity_units_per_second"]
                timing_ceiling = Decimal(1000000000) / (motor["step_high_ns"] + motor["step_low_ns"])
                limit = min(timing_ceiling, Decimal(selected["maximum_rate_hz"]), Decimal(resource["maximum_simulation_rate_hz"]))
                if rate > limit:
                    blockers.append(_issue("SETUP_RATE_LIMIT", f"Required {rate} pulses/s exceeds simulation limit {limit}", path + ".max_velocity_units_per_second"))
                mm_per_unit = Decimal("25.4") if motor["unit"] == "in" else Decimal(1)
                calculations.append({"motor_id": motor["id"], "axis": motor["axis"], "resource": motor["resource"],
                    "unit": motor["unit"], "pulses_per_motor_revolution": float(pulses),
                    "motor_to_load_ratio": float(ratio), "steps_per_unit": float(scale),
                    "steps_per_mm": float(scale / mm_per_unit), "maximum_velocity_mm_per_second": float(values["max_velocity_units_per_second"] * mm_per_unit),
                    "required_step_rate_hz": float(rate), "timing_ceiling_hz": float(timing_ceiling),
                    "maximum_simulation_rate_hz": float(limit), "rate_margin_hz": float(limit-rate),
                    "enable_resource": resource["enable_resource"], "alarm_resource": resource["alarm_resource"],
                    "formula": "steps/rev * microsteps * motor_revs/load_revs / travel_per_load_rev",
                    "provenance": "derived_from_unverified_user_selections_and_simulation_profile",
                    "physical_qualified": False})

    group_current = {i: Decimal(0) for i in range(4)}
    for name, kind, maximum in (("inputs", "digital_input", 24), ("outputs", "digital_output", 16), ("encoders", "abz", 4)):
        _array(draft[name], "$." + name, maximum)
        for i, item in enumerate(draft[name]):
            path = f"$.{name}[{i}]"
            keys = {"resource", "role", "equipment_profile"}
            keys |= {"counts_per_revolution"} if name == "encoders" else {"voltage_v"}
            if name == "outputs":
                keys.add("current_a")
            _object(item, keys, path)
            _text(item["role"], path + ".role")
            resource = assign(item["resource"], kind, path + ".resource", item["role"])
            selected = select(item["equipment_profile"], kind, path + ".equipment_profile")
            if name != "encoders":
                voltage = _number(item["voltage_v"], path + ".voltage_v", 0, 60)
                if resource and selected and voltage != Decimal(selected["voltage_v"]):
                    blockers.append(_issue("SETUP_VOLTAGE", "Voltage differs from the explicit simulation equipment/resource profile", path + ".voltage_v"))
            else:
                if item["counts_per_revolution"] is None:
                    missing.append(_issue("SETUP_MISSING_FACT", "Enter decoded counts per revolution; do not confuse cycles with x4 counts", path + ".counts_per_revolution"))
                else:
                    _number(item["counts_per_revolution"], path + ".counts_per_revolution", 1, 1000000000, integer=True)
            if name == "outputs":
                current = _number(item["current_a"], path + ".current_a", 0, 10)
                if current > Decimal("0.5"):
                    blockers.append(_issue("SETUP_CURRENT", "The retained limit is 0.5 A per output", path + ".current_a"))
                if resource:
                    group_current[resource["group"]] += current
    for group, current in group_current.items():
        if current > Decimal(2):
            blockers.append(_issue("SETUP_GROUP_CURRENT", f"Output group {group} exceeds 2 A", "$.outputs"))
    result = {"valid": not missing and not blockers, "draft": deepcopy(draft), "missing_facts": missing,
        "blockers": blockers, "calculations": calculations, "wiring": wiring,
        "output_groups": [{"group": g, "selected_current_a": float(c), "limit_a": 2} for g, c in group_current.items()],
        "assigned_resources": deepcopy(used), "physical_checks": "unverified; this fixture cannot commission equipment",
        "fact_provenance": "user_selections_only_not_physical_evidence", **deepcopy(GUARDS)}
    if require_complete and not result["valid"]:
        issue = (blockers + missing)[0]
        _error(issue["code"], issue["message"], issue["path"])
    return result


def missing_facts(draft):
    return validate_draft(draft)["missing_facts"]


def _revision(value, path="revision"):
    _number(value, path, 0, MAX_REVISION, integer=True)


def _timestamp():
    return datetime.now(timezone.utc).isoformat()


class SetupService:
    """Shared local UI/CLI authority for a file-only, explicitly simulated setup."""
    capabilities = staticmethod(capabilities)
    profiles = staticmethod(profiles)
    equipment_profiles = staticmethod(equipment_profiles)
    draft_template = staticmethod(draft_template)
    example_draft = staticmethod(example_draft)
    schema = staticmethod(schema)
    validate_draft = staticmethod(validate_draft)
    missing_facts = staticmethod(missing_facts)

    def __init__(self, store_path):
        self.path = Path(store_path).resolve()

    def _load(self):
        if not self.path.exists():
            _error("SETUP_NOT_INITIALIZED", "Initialize a dedicated IS-2 simulation store first")
        state = _verify_seal(read_json(self.path), "SETUP_STORE_INTEGRITY")
        # The first schema-1 stores lacked retained drafts. Verify their raw seal
        # before allowing this additive field; reads never rewrite/migrate bytes.
        optional = {"retained_profile_drafts"} if "retained_profile_drafts" in state else set()
        _object(state, {"schema", "store_id", "epoch", "revision", "generation", "catalog_sha256",
                        "draft", "active", "history", "audit", "requests"} | optional, "store")
        if state["schema"] != SCHEMA:
            _error("SETUP_STORE_VERSION", "Store is not an IS-2 disconnected setup store; it was not changed")
        for key in ("store_id", "epoch"):
            try:
                if type(state[key]) is not str or str(uuid.UUID(state[key])) != state[key]:
                    raise ValueError()
            except (ValueError, TypeError, AttributeError):
                _error("SETUP_STORE_FORMAT", "Invalid store/session identity")
        _revision(state["revision"])
        _revision(state["generation"], "generation")
        if state["catalog_sha256"] != _catalog_digest():
            _error("SETUP_CATALOG_CHANGED", "Simulation catalog changed; explicit migration is required")
        _array(state["history"], "history", HISTORY_LIMIT)
        _array(state["audit"], "audit", AUDIT_LIMIT)
        _array(state["requests"], "requests", REQUEST_LIMIT)
        if state["draft"] is not None:
            validate_draft(state["draft"])
        retained = state.get("retained_profile_drafts", {})
        if type(retained) is not dict or not set(retained) <= set(PROFILES):
            _error("SETUP_STORE_FORMAT", "Retained drafts must use supported simulation profile IDs")
        for profile_id, draft in retained.items():
            validate_draft(draft)
            if draft["profile_id"] != profile_id:
                _error("SETUP_STORE_FORMAT", "Retained draft does not match its profile identity")
        previous = -1
        for record in state["history"] + ([state["active"]] if state["active"] else []):
            _object(record, {"generation", "draft", "calculations", "wiring", "configuration_sha256"}, "active")
            _revision(record["generation"], "active.generation")
            checked = validate_draft(record["draft"], require_complete=True)
            if (record["generation"] <= previous or record["generation"] > state["generation"] or
                    record["configuration_sha256"] != digest(record["draft"]) or
                    canonical(record["calculations"]) != canonical(checked["calculations"]) or
                    canonical(record["wiring"]) != canonical(checked["wiring"])):
                _error("SETUP_STORE_FORMAT", "Invalid stored configuration generation or derived values")
            previous = record["generation"]
        if (state["active"] is None) != (state["generation"] == 0) or (state["active"] and state["active"]["generation"] != state["generation"]):
            _error("SETUP_STORE_FORMAT", "Current generation does not agree with active configuration")
        seen = set()
        for item in state["requests"]:
            _object(item, {"request_id", "plan_sha256", "result"}, "requests")
            _text(item["request_id"], "request_id")
            if item["request_id"] in seen or type(item["plan_sha256"]) is not str or len(item["plan_sha256"]) != 64 or type(item["result"]) is not dict:
                _error("SETUP_STORE_FORMAT", "Invalid duplicate request record")
            for guard, expected in GUARDS.items():
                if guard not in item["result"] or canonical(item["result"][guard]) != canonical(expected):
                    _error("SETUP_STORE_FORMAT", "Retained request result cannot grant physical authority")
            seen.add(item["request_id"])
        return state

    def _write(self, state):
        state.setdefault("retained_profile_drafts", {})
        atomic_write(self.path, _seal(state))

    @staticmethod
    def _set_draft(state, draft):
        previous = state["draft"]
        if previous is not None and previous["profile_id"] != draft["profile_id"]:
            state.setdefault("retained_profile_drafts", {})[previous["profile_id"]] = deepcopy(previous)
        state["draft"] = deepcopy(draft)

    @staticmethod
    def _advance(state):
        if state["revision"] == MAX_REVISION:
            _error("SETUP_GENERATION_EXHAUSTED", "Revision exhausted; no wrap is permitted")
        state["revision"] += 1

    @staticmethod
    def _event(state, action, actor, **detail):
        state["audit"] = (state["audit"] + [{"action": action, "actor": _actor(actor), "timestamp": _timestamp(),
            "revision": state["revision"], "generation": state["generation"], **detail}])[-AUDIT_LIMIT:]

    def initialize(self, actor="local"):
        actor = _actor(actor)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        with _exclusive_lock(self.path):
            if self.path.exists():
                state = self._load()  # Never replace a foreign/corrupt/user store.
            else:
                state = {"schema": SCHEMA, "store_id": str(uuid.uuid4()), "epoch": str(uuid.uuid4()),
                    "revision": 0, "generation": 0, "catalog_sha256": _catalog_digest(),
                    "draft": None, "active": None, "history": [], "audit": [], "requests": []}
                self._event(state, "initialize", actor)
                self._write(state)
            return self._status_snapshot(state)

    def status(self):
        if not self.path.exists():
            return {"initialized": False, "revision": 0, "current_revision": 0, "generation": 0,
                "epoch": None, "draft": None, "active": None, "history": [], "validation": None,
                "draft_binding": None,
                "retained_profile_drafts": {},
                "capabilities": capabilities(), **deepcopy(GUARDS)}
        return self._status_snapshot(self._load())

    def backup_snapshot(self):
        """Export all retained simulation configurations from one locked state.

        This contains no AI requests, billing ledger or permission to restart.
        Restoring an exported draft still uses ordinary preview/commit checks.
        """
        if not self.path.exists():
            _error("SETUP_NOT_INITIALIZED", "Initialize and save a simulation setup before exporting a backup")
        with _exclusive_lock(self.path):
            state = self._load()
            keys = ("store_id", "epoch", "revision", "generation", "catalog_sha256",
                    "draft", "active", "history")
            return {"schema_version": 1, "kind": "is2_disconnected_backup",
                    **{key: deepcopy(state[key]) for key in keys},
                    "retained_profile_drafts": deepcopy(state.get("retained_profile_drafts", {})),
                    **deepcopy(GUARDS)}

    @staticmethod
    def _draft_binding(state):
        return {"store_id": state["store_id"], "epoch": state["epoch"], "revision": state["revision"],
                "draft_sha256": digest(state["draft"])}

    @staticmethod
    def _status_snapshot(state):
        """Return one detached state, never a later writer's revision/draft.

        Mutations call this while holding their write lock. Reading status again
        after releasing it would let an intervening writer's revision authorize
        the caller's next stale draft save.
        """
        return {"initialized": True, "store_id": state["store_id"], "revision": state["revision"],
            "current_revision": state["revision"], "generation": state["generation"], "epoch": state["epoch"],
            "draft_binding": SetupService._draft_binding(state),
            "draft": deepcopy(state["draft"]), "active": deepcopy(state["active"]),
            "retained_profile_drafts": deepcopy(state.get("retained_profile_drafts", {})),
            "history": [{"generation": r["generation"], "configuration_sha256": r["configuration_sha256"]} for r in state["history"]],
            "validation": validate_draft(state["draft"]) if state["draft"] else None,
            "capabilities": capabilities(), **deepcopy(GUARDS)}

    def save_draft(self, draft, expected_revision, actor="local", *, expected_binding=None):
        draft = deepcopy(draft)
        validate_draft(draft)
        _revision(expected_revision)
        expected_binding = deepcopy(expected_binding)
        if expected_binding is not None:
            _object(expected_binding, {"store_id", "epoch", "revision", "draft_sha256"}, "expected_binding")
            for key in ("store_id", "epoch", "draft_sha256"):
                _text(expected_binding[key], "expected_binding." + key)
            _revision(expected_binding["revision"], "expected_binding.revision")
        actor = _actor(actor)
        with _exclusive_lock(self.path):
            state = self._load()
            if expected_revision != state["revision"]:
                _error("SETUP_STALE", "Draft changed; refresh before saving")
            if expected_binding is not None:
                if type(expected_binding) is not dict or canonical(expected_binding) != canonical(self._draft_binding(state)):
                    _error("SETUP_STALE", "Settings identity, session or draft changed; inspect the current saved draft before editing it")
            if canonical(state["draft"]) != canonical(draft):
                before = digest(state["draft"])
                self._advance(state)
                self._set_draft(state, draft)
                self._event(state, "save_draft", actor, before_sha256=before, after_sha256=digest(draft))
                self._write(state)
            return self._status_snapshot(state)

    @staticmethod
    def _plan(state, candidate, operation="apply", restore_generation=None):
        validation = validate_draft(candidate, require_complete=True)
        previous = state["active"]["draft"] if state["active"] else None
        plan = {"schema_version": 1, "kind": "is2_disconnected_setup_plan", "operation": operation,
            "store_id": state["store_id"], "epoch": state["epoch"], "base_revision": state["revision"],
            "base_state_sha256": digest(state), "catalog_sha256": _catalog_digest(),
            "candidate": deepcopy(candidate), "candidate_sha256": digest(candidate),
            "restore_generation": restore_generation, "changes": _diff(previous, candidate),
            "validation": validation, "review_required": True, **deepcopy(GUARDS)}
        return {**plan, "plan_sha256": digest(plan)}

    def preview(self, draft=None):
        state = self._load()
        candidate = deepcopy(draft) if draft is not None else state["draft"]
        if candidate is None:
            _error("SETUP_NO_DRAFT", "Save or supply a simulation draft before preview")
        return self._plan(state, candidate)

    def restore_preview(self, generation):
        _revision(generation, "generation")
        state = self._load()
        for record in state["history"] + ([state["active"]] if state["active"] else []):
            if record["generation"] == generation:
                return self._plan(state, record["draft"], "restore", generation)
        _error("SETUP_GENERATION_UNKNOWN", "Requested configuration is outside retained generation history")

    def commit(self, plan, request_id, actor="local"):
        plan = deepcopy(plan)
        _text(request_id, "request_id")
        actor = _actor(actor)
        if type(plan) is not dict or type(plan.get("plan_sha256")) is not str:
            _error("SETUP_PLAN", "Expected a complete preview plan")
        payload = {key: value for key, value in plan.items() if key != "plan_sha256"}
        try:
            actual_digest = digest(payload)
        except (TypeError, ValueError, RecursionError):
            _error("SETUP_PLAN", "Invalid preview serialization")
        if actual_digest != plan["plan_sha256"]:
            _error("SETUP_PLAN_CHANGED", "Preview plan changed after review")
        with _exclusive_lock(self.path):
            state = self._load()
            for previous in state["requests"]:
                if previous["request_id"] == request_id:
                    if previous["plan_sha256"] != plan["plan_sha256"]:
                        _error("SETUP_IDEMPOTENCY_CONFLICT", "Request ID already belongs to a different preview")
                    return {**deepcopy(previous["result"]), "replayed": True, "current_revision": state["revision"]}
            for key, expected in (("store_id", state["store_id"]), ("epoch", state["epoch"]),
                                  ("base_revision", state["revision"]), ("base_state_sha256", digest(state))):
                if plan.get(key) != expected:
                    _error("SETUP_STALE", "Preview identity, epoch or revision changed; preview again", key)
            operation = plan.get("operation")
            if operation not in ("apply", "restore"):
                _error("SETUP_PLAN", "Unsupported configuration operation")
            candidate = plan.get("candidate")
            source_generation = plan.get("restore_generation")
            if operation == "restore":
                _revision(source_generation, "restore_generation")
                records = state["history"] + ([state["active"]] if state["active"] else [])
                if not any(r["generation"] == source_generation and canonical(r["draft"]) == canonical(candidate) for r in records):
                    _error("SETUP_PLAN", "Restore does not match a retained generation")
            elif source_generation is not None:
                _error("SETUP_PLAN", "Apply cannot impersonate a restore")
            if canonical(plan) != canonical(self._plan(state, candidate, operation, source_generation)):
                _error("SETUP_PLAN_CHANGED", "Preview differs from independently recomputed validation and diff")
            configuration_changed = state["active"] is None or canonical(state["active"]["draft"]) != canonical(candidate)
            draft_changed = canonical(state["draft"]) != canonical(candidate)
            before_configuration = state["active"]["configuration_sha256"] if state["active"] else None
            if configuration_changed:
                if state["generation"] == MAX_REVISION:
                    _error("SETUP_GENERATION_EXHAUSTED", "Generation exhausted; no wrap is permitted")
                if state["active"]:
                    state["history"] = (state["history"] + [state["active"]])[-HISTORY_LIMIT:]
                state["generation"] += 1
                state["active"] = {"generation": state["generation"], "draft": deepcopy(candidate),
                    "calculations": plan["validation"]["calculations"], "wiring": plan["validation"]["wiring"],
                    "configuration_sha256": digest(candidate)}
            if configuration_changed or draft_changed:
                self._advance(state)
                self._set_draft(state, candidate)
            changed = configuration_changed or draft_changed
            result = {"changed": changed, "revision": state["revision"], "current_revision": state["revision"],
                "generation": state["generation"], "configuration_sha256": digest(candidate),
                "request_id": request_id, "replayed": False, "configuration_changed": configuration_changed,
                "draft_changed": draft_changed, **deepcopy(GUARDS)}
            self._event(state, operation if changed else "unchanged", actor, request_id=request_id,
                        before_configuration_sha256=before_configuration, after_configuration_sha256=digest(candidate),
                        restore_generation=source_generation)
            state["requests"] = (state["requests"] + [{"request_id": request_id,
                "plan_sha256": plan["plan_sha256"], "result": deepcopy(result)}])[-REQUEST_LIMIT:]
            self._write(state)
            return result

    def request_result(self, request_id):
        _text(request_id, "request_id")
        state = self._load()
        for item in state["requests"]:
            if item["request_id"] == request_id:
                return {**deepcopy(item["result"]), "replayed": True, "current_revision": state["revision"]}
        _error("SETUP_REQUEST_UNKNOWN", "No retained result for this request ID; refresh state before deciding")

    def audit(self):
        state = self._load()
        return {"revision": state["revision"], "generation": state["generation"],
            "entries": deepcopy(state["audit"]), "retained_prior_generations": len(state["history"]),
            **deepcopy(GUARDS)}

    def restart_epoch(self, expected_revision, actor="local"):
        """Explicitly invalidate outstanding local previews; not a hardware reset."""
        _revision(expected_revision)
        actor = _actor(actor)
        with _exclusive_lock(self.path):
            state = self._load()
            if state["revision"] != expected_revision:
                _error("SETUP_STALE", "Store changed before session restart")
            self._advance(state)
            state["epoch"] = str(uuid.uuid4())
            self._event(state, "restart_simulation_epoch", actor)
            self._write(state)
            return self._status_snapshot(state)
