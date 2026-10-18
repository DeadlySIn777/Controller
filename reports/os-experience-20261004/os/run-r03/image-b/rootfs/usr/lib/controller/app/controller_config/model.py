"""Strict versioned data contract and immutable-in-practice virtual capabilities.

Catalog values are authored fixtures, not discovery of fitted or qualified hardware.
No imported configuration can extend the catalog's electrical/resource limits.
"""

from copy import deepcopy
import math
import re


class ConfigurationError(ValueError):
    def __init__(self, code, message, path=""):
        super().__init__(message)
        self.code, self.path = code, path

    def as_dict(self):
        return {"code": self.code, "message": str(self), "path": self.path}


def _object(properties):
    return {"type": "object", "properties": properties,
            "required": list(properties), "additionalProperties": False}


def _string(**kwargs):
    return {"type": "string", "minLength": 1, "maxLength": 120, **kwargs}


def _number(low, high):
    return {"type": "number", "minimum": low, "maximum": high}


def configuration_schema():
    """JSON Schema document; the runtime implements this emitted subset strictly."""
    connection = _object({
        "role": _string(), "resource": _string(),
        "voltage_v": _number(0, 60), "current_a": _number(0, 10),
        "rate_hz": _number(0, 10000000), "signal_type": _string(),
    })
    calibration = _object({
        "steps_per_unit": _number(0.001, 1000000),
        "unit": _string(enum=["mm"]), "status": _string(const="unverified"),
    })
    check = _object({"id": _string(), "status": _string(const="pending"),
                     "evidence": _string(const="simulation_fixture_only")})
    device = _object({
        "identity": _object({
            "instance_id": _string(pattern=r"^[a-z][a-z0-9_-]{0,39}$"),
            "model": _string(enum=list(_device_definitions())),
            "hardware_revision": _string(const="virtual-r1"),
            "firmware_revision": _string(const="virtual-1.0"),
            "evidence": _string(const="selected_virtual_fixture"),
            "simulation_only": {"type": "boolean", "const": True},
        }),
        "electrical_capabilities": _object({
            "signal_type": _string(), "nominal_voltage_v": _number(0, 60),
            "maximum_current_a": _number(0, 10),
            "maximum_rate_hz": _number(0, 10000000),
        }),
        "available_functions": {"type": "array", "items": _string(), "minItems": 1, "maxItems": 4},
        "required_connections": {"type": "array", "items": connection, "minItems": 1, "maxItems": 4},
        "calibration": {"type": "array", "items": calibration, "maxItems": 1},
        "compatible_profiles": {"type": "array", "items": _string(), "minItems": 1, "maxItems": 2},
        "permitted_commands": {"type": "array", "items": _string(), "minItems": 1, "maxItems": 3},
        "startup_behavior": _string(const="outputs_disabled"),
        "communication_loss_behavior": _string(const="latch_fault_no_restart"),
        "output_owner": _string(const="none_simulation_only"),
        "readiness": _object({"requested": {"type": "boolean", "const": False},
                              "observed": _string(const="unverified")}),
        "commissioning_checks": {"type": "array", "items": check, "minItems": 1, "maxItems": 4},
    })
    result = _object({
        "schema_version": {"type": "integer", "const": 1},
        "kind": _string(const="disconnected_simulation_configuration"),
        "board_identity": _object({
            "id": _string(const="virtual-baseline-6j-2enc"),
            "revision": _string(const="virtual-r1"),
            "evidence": _string(const="built_in_virtual_fixture"),
            "simulation_only": {"type": "boolean", "const": True},
        }),
        "machine": _object({
            "name": _string(), "profile_id": _string(enum=list(PROFILES)),
            "units": _string(const="mm"),
            "simulation_only": {"type": "boolean", "const": True},
        }),
        "devices": {"type": "array", "items": device, "minItems": 1, "maxItems": 16},
    })
    result["$schema"] = "https://json-schema.org/draft/2020-12/schema"
    result["$id"] = "urn:controller:disconnected-config:1"
    result["title"] = "Disconnected virtual controller configuration v1"
    return result


PROFILES = {
    "sim-mill-3axis": {"title": "Virtual three-axis mill", "axes": ["x", "y", "z"]},
    "sim-lathe-2axis": {"title": "Virtual two-axis lathe", "axes": ["x", "z"]},
}


def _device_definitions():
    return {
        "virtual-step-drive": {
            "electrical_capabilities": {"signal_type": "differential_5v", "nominal_voltage_v": 5,
                                        "maximum_current_a": 0.02, "maximum_rate_hz": 200000},
            "available_functions": ["step_dir"], "checks": ["wiring", "direction", "scale"],
            "role": "step_dir", "calibration": True,
        },
        "virtual-home-switch": {
            "electrical_capabilities": {"signal_type": "contact_to_24v", "nominal_voltage_v": 24,
                                        "maximum_current_a": 0.005, "maximum_rate_hz": 100},
            "available_functions": ["home_input"], "checks": ["wiring", "polarity"],
            "role": "home_input", "calibration": False,
        },
    }


def capabilities():
    resources = []
    for i in range(6):
        resources.append({"id": f"SIM.M{i}", "function": "step_dir", "signal_type": "differential_5v",
                          "voltage_v": 5, "maximum_current_a": 0.02, "maximum_rate_hz": 195312.5,
                          "virtual_terminals": [f"SIM.M{i}.STEP+", f"SIM.M{i}.STEP-",
                                                f"SIM.M{i}.DIR+", f"SIM.M{i}.DIR-", f"SIM.M{i}.REF"]})
    for i in range(16):
        resources.append({"id": f"SIM.DI{i}", "function": "home_input", "signal_type": "contact_to_24v",
                          "voltage_v": 24, "maximum_current_a": 0.005, "maximum_rate_hz": 100,
                          "virtual_terminals": [f"SIM.DI{i}.IN", f"SIM.DI{i}.FIELD+"]})
    return {"schema_version": 1, "identity": {"id": "virtual-baseline-6j-2enc", "revision": "virtual-r1",
            "evidence": "built_in_virtual_fixture", "simulation_only": True},
            "notice": "Illustrative resources only; no physical pinout, measured rating or device discovery.",
            "configuration_functions": ["profile_select", "validate", "diff", "wiring_plan", "apply", "backup", "restore"],
            "motion_commands": [], "resources": resources,
            "unallocated_reference_encoders": 2,
            "profiles": deepcopy(PROFILES), "device_models": _device_definitions()}


def _check_schema(value, schema, path="$"):
    kind = schema.get("type")
    types = {"object": dict, "array": list, "string": str, "integer": int, "boolean": bool}
    # Integers have no NaN/Infinity; avoid float conversion of enormous API integers.
    valid = (type(value) is int or (type(value) is float and math.isfinite(value))) if kind == "number" else type(value) is types[kind]
    if not valid:
        raise ConfigurationError("SCHEMA_TYPE", f"Expected {kind}", path)
    if "const" in schema and value != schema["const"]:
        raise ConfigurationError("SCHEMA_CONST", "Value does not match this simulation schema", path)
    if "enum" in schema and value not in schema["enum"]:
        raise ConfigurationError("SCHEMA_ENUM", "Unsupported value", path)
    if kind == "object":
        extra = set(value) - set(schema["properties"])
        missing = set(schema["required"]) - set(value)
        if extra or missing:
            raise ConfigurationError("SCHEMA_KEYS", f"Unknown keys {sorted(extra)}; missing keys {sorted(missing)}", path)
        for key, subschema in schema["properties"].items():
            _check_schema(value[key], subschema, f"{path}.{key}")
    elif kind == "array":
        if not schema.get("minItems", 0) <= len(value) <= schema.get("maxItems", 1000):
            raise ConfigurationError("SCHEMA_LENGTH", "Array length outside contract", path)
        for index, item in enumerate(value):
            _check_schema(item, schema["items"], f"{path}[{index}]")
    elif kind == "string":
        if not schema.get("minLength", 0) <= len(value) <= schema.get("maxLength", 1000):
            raise ConfigurationError("SCHEMA_LENGTH", "String length outside contract", path)
        if "pattern" in schema and not re.fullmatch(schema["pattern"], value):
            raise ConfigurationError("SCHEMA_PATTERN", "Invalid identifier", path)
    elif kind == "number" and not schema["minimum"] <= value <= schema["maximum"]:
        raise ConfigurationError("SCHEMA_RANGE", "Number outside schema range", path)


def validate_configuration(config):
    _check_schema(config, configuration_schema())
    resources = {r["id"]: r for r in capabilities()["resources"]}
    definitions = _device_definitions()
    selected = config["machine"]["profile_id"]
    expected = {f"{axis}-drive": "virtual-step-drive" for axis in PROFILES[selected]["axes"]}
    expected.update({f"{axis}-home": "virtual-home-switch" for axis in PROFILES[selected]["axes"]})
    seen, assigned = {}, {}
    for index, device in enumerate(config["devices"]):
        path = f"$.devices[{index}]"
        identity = device["identity"]
        instance, model = identity["instance_id"], identity["model"]
        if instance in seen:
            raise ConfigurationError("DEVICE_CONFLICT", "Duplicate device instance", path)
        seen[instance] = model
        definition = definitions[model]
        for key in ("electrical_capabilities", "available_functions"):
            if device[key] != definition[key]:
                raise ConfigurationError("CAPABILITY_MISMATCH", "Imported data cannot redefine virtual device capabilities", f"{path}.{key}")
        if device["compatible_profiles"] != list(PROFILES) or device["permitted_commands"] != ["inspect", "validate", "wiring"]:
            raise ConfigurationError("CAPABILITY_MISMATCH", "Unsupported profile or command declaration", path)
        checks = [{"id": name, "status": "pending", "evidence": "simulation_fixture_only"} for name in definition["checks"]]
        if device["commissioning_checks"] != checks:
            raise ConfigurationError("COMMISSIONING_EVIDENCE", "This demo cannot import claims of completed commissioning", path)
        if len(device["calibration"]) != int(definition["calibration"]):
            raise ConfigurationError("CALIBRATION", "Wrong calibration record for device type", path)
        connections = device["required_connections"]
        if len(connections) != 1 or connections[0]["role"] != definition["role"]:
            raise ConfigurationError("CONNECTION_ROLE", "Device requires its declared connection role", path)
        connection = connections[0]
        rid = connection["resource"]
        if rid not in resources:
            raise ConfigurationError("UNKNOWN_RESOURCE", "Resource is absent from virtual board capabilities", path)
        if rid in assigned:
            raise ConfigurationError("RESOURCE_CONFLICT", f"{rid} already belongs to {assigned[rid]}", path)
        assigned[rid] = instance
        resource, electrical = resources[rid], device["electrical_capabilities"]
        if resource["function"] != connection["role"] or resource["signal_type"] != connection["signal_type"] or electrical["signal_type"] != connection["signal_type"]:
            raise ConfigurationError("ELECTRICAL_TYPE", "Function or signal type is incompatible", path)
        if connection["voltage_v"] != resource["voltage_v"] or connection["voltage_v"] != electrical["nominal_voltage_v"]:
            raise ConfigurationError("ELECTRICAL_VOLTAGE", "Connection voltage is incompatible", path)
        for requested, limit in (("current_a", "maximum_current_a"), ("rate_hz", "maximum_rate_hz")):
            if connection[requested] > min(resource[limit], electrical[limit]):
                raise ConfigurationError("ELECTRICAL_LIMIT", f"{requested} exceeds board or device limit", path)
    if seen != expected:
        raise ConfigurationError("PROFILE_TOPOLOGY", "Selected profile needs exactly its named drive and home devices", "$.devices")
    return {"valid": True, "schema_version": 1, "simulation_only": True,
            "assigned_resources": len(assigned), "physical_commissioning_complete": False,
            "warnings": ["Virtual illustrative wiring only; all calibration and commissioning remain unverified."]}


def profile(profile_id):
    if type(profile_id) is not str or profile_id not in PROFILES:
        raise ConfigurationError("UNKNOWN_PROFILE", "Unknown simulated machine profile")
    devices = []
    for index, axis in enumerate(PROFILES[profile_id]["axes"]):
        for model, suffix, resource in (("virtual-step-drive", "drive", f"SIM.M{index}"),
                                         ("virtual-home-switch", "home", f"SIM.DI{index}")):
            definition = _device_definitions()[model]
            electrical = definition["electrical_capabilities"]
            devices.append({
                "identity": {"instance_id": f"{axis}-{suffix}", "model": model, "hardware_revision": "virtual-r1",
                             "firmware_revision": "virtual-1.0", "evidence": "selected_virtual_fixture", "simulation_only": True},
                "electrical_capabilities": deepcopy(electrical),
                "available_functions": list(definition["available_functions"]),
                "required_connections": [{"role": definition["role"], "resource": resource,
                    "voltage_v": electrical["nominal_voltage_v"], "current_a": electrical["maximum_current_a"],
                    "rate_hz": 100000 if suffix == "drive" else 10, "signal_type": electrical["signal_type"]}],
                "calibration": [{"steps_per_unit": 200, "unit": "mm", "status": "unverified"}] if definition["calibration"] else [],
                "compatible_profiles": list(PROFILES), "permitted_commands": ["inspect", "validate", "wiring"],
                "startup_behavior": "outputs_disabled", "communication_loss_behavior": "latch_fault_no_restart",
                "output_owner": "none_simulation_only", "readiness": {"requested": False, "observed": "unverified"},
                "commissioning_checks": [{"id": check, "status": "pending", "evidence": "simulation_fixture_only"} for check in definition["checks"]],
            })
    result = {"schema_version": 1, "kind": "disconnected_simulation_configuration",
              "board_identity": capabilities()["identity"],
              "machine": {"name": PROFILES[profile_id]["title"], "profile_id": profile_id, "units": "mm", "simulation_only": True},
              "devices": devices}
    validate_configuration(result)
    return result


def wiring_plan(config):
    validate_configuration(config)
    resources = {r["id"]: r for r in capabilities()["resources"]}
    rows = []
    for device in config["devices"]:
        for connection in device["required_connections"]:
            rows.append({"device": device["identity"]["instance_id"], **deepcopy(connection),
                         "virtual_terminals": resources[connection["resource"]]["virtual_terminals"],
                         "physical_wiring_verified": False})
    return {"schema_version": 1, "simulation_only": True,
            "notice": "ILLUSTRATIVE VIRTUAL TERMINALS. Do not wire a physical device from this plan.", "connections": rows}
