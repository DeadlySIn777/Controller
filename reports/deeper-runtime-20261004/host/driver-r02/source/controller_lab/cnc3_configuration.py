"""Bind reviewed setup settings to the disconnected CNC3 SIM2 runtime.

This is a lab adapter, not a configuration service or hardware backend. It never
writes a settings store. The frozen wire's 32-bit identifiers are accompanied by
full digests in the manifest; they are not authentication or physical evidence.
"""
from __future__ import annotations

from copy import deepcopy
from decimal import Decimal, localcontext, ROUND_CEILING
import hashlib
from pathlib import Path
import re
import uuid

from controller_config.model import ConfigurationError
from controller_config.service import canonical, digest
from controller_config.setup_service import GUARDS, SetupService, TIMINGS, validate_draft

CORE_HZ = 50_000_000
DDS_MODULUS = 1 << 32
MAX_RATE_WORD = 0x01000000
FITTED_MASK = 0x0FFF
SIM_GATEWARE_BUILD = 0xD3494D32
BINDING_KEYS = {"store_id", "epoch", "revision", "generation", "configuration_sha256", "draft_sha256"}


def _reject(code, message, path=""):
    raise ConfigurationError(code, message, path)


def configuration_binding(snapshot):
    """The same six-field binding exposed by setup readiness, from one snapshot."""
    active = snapshot.get("active")
    return {"store_id": snapshot["store_id"], "epoch": snapshot["epoch"],
            "revision": snapshot["revision"], "generation": snapshot["generation"],
            "configuration_sha256": active["configuration_sha256"] if active else None,
            "draft_sha256": digest(snapshot["draft"])}


def _source_inventory(root, sources):
    root = Path(root).resolve()
    if type(sources) not in (list, tuple) or not sources or len(sources) > 512:
        _reject("SIM2_SOURCE", "Supply a nonempty, bounded list of runtime source files")
    inventory = {}
    for name in sources:
        if type(name) is not str or not name or "\\" in name:
            _reject("SIM2_SOURCE", "Source names must be workspace-relative POSIX paths")
        relative = Path(name)
        if relative.is_absolute() or ":" in name or ".." in relative.parts or relative.as_posix() != name:
            _reject("SIM2_SOURCE", "Source path must be canonical and remain in the workspace", name)
        target = (root / relative).resolve()
        if not target.is_relative_to(root) or not target.is_file() or name in inventory:
            _reject("SIM2_SOURCE", "Source path is absent, duplicated or leaves the workspace", name)
        hasher = hashlib.sha256()
        with target.open("rb") as handle:
            for block in iter(lambda: handle.read(1 << 20), b""):
                hasher.update(block)
        inventory[name] = hasher.hexdigest()
    return dict(sorted(inventory.items()))


def _identifier(full_digest):
    return int(full_digest[:8], 16) or 1


def _resource_index(resource, prefix, limit):
    match = re.fullmatch(re.escape(prefix) + r"(0|[1-9][0-9]*)", resource)
    if not match or int(match[1]) >= limit:
        _reject("SIM2_RESOURCE", "Resource is not representable by this runtime", resource)
    return int(match[1])


def _motor_parameters(motor):
    if motor["step_active_high"] is not True or motor["dir_inverted"] is not False:
        _reject("SIM2_POLARITY", "This SIM2 endpoint requires active-high STEP and uninverted DIR; review the setting explicitly", motor["resource"])
    ticks = [(motor[field] * CORE_HZ + 999_999_999) // 1_000_000_000 for field in TIMINGS]
    if any(value < 100 or value > 1023 for value in ticks):
        _reject("SIM2_TIMING", "Saved timing is outside the endpoint's 100..1023 core-tick range", motor["resource"])
    with localcontext() as context:
        context.prec = 60
        number = lambda name: Decimal(str(motor[name]))
        pulses = number("motor_steps_per_revolution") * number("microsteps")
        ratio = number("gear_motor_revolutions") / number("gear_load_revolutions")
        scale = pulses * ratio / number("travel_per_load_revolution")
        mm_per_unit = Decimal("25.4") if motor["unit"] == "in" else Decimal(1)
        scale_mm = scale / mm_per_unit
        velocity_mm = number("max_velocity_units_per_second") * mm_per_unit
        required_rate = scale_mm * velocity_mm
        # Use a conservative word bound, including the real DDS carry guard.
        # A frontend's high+low timing ceiling alone is insufficient here.
        word_bound = int((required_rate * DDS_MODULUS / CORE_HZ).to_integral_value(rounding=ROUND_CEILING))
        period_ticks = ticks[0] + ticks[1] + 1
        if scale_mm < 1 or scale_mm > 1_000_000:
            _reject("SIM2_SCALE", "Saved mechanics exceed the CNC3 host's supported steps/mm range", motor["resource"])
        if word_bound > MAX_RATE_WORD or word_bound * period_ticks > DDS_MODULUS:
            _reject("SIM2_RATE", "Saved maximum velocity exceeds the representable DDS/timing limit", motor["resource"])
        return {"scale": float(scale_mm), "max_velocity": float(velocity_mm),
                "electrical_steps_per_revolution": int(pulses),
                "timing_ticks": ticks, "maximum_rate_word": word_bound,
                "required_step_rate_hz": float(required_rate),
                "timing_guard_period_ticks": period_ticks}


def _encoder_mapping(draft, supplied):
    encoders = {_resource_index(item["resource"], "SIM.ABZ", 4): item for item in draft["encoders"]}
    motors = {_resource_index(item["resource"], "SIM.M", 12): item for item in draft["motors"]}
    if supplied is None:
        supplied = []
    if type(supplied) is not list or len(supplied) != len(encoders):
        _reject("SIM2_ENCODER_MAPPING", "Supply an explicit lab mapping for each configured encoder")
    mapped = set()
    for item in supplied:
        if (type(item) is not dict or set(item) != {"encoder_channel", "motor_channel", "edges_per_step"} or
                any(type(value) is not int for value in item.values())):
            _reject("SIM2_ENCODER_MAPPING", "Each lab mapping requires integer encoder_channel, motor_channel and edges_per_step")
        channel, motor = item["encoder_channel"], item["motor_channel"]
        if (channel not in encoders or channel in mapped or motor not in motors or
                channel != motor or item["edges_per_step"] != 1):
            _reject("SIM2_ENCODER_MAPPING", "This plant supports explicit encoder N to motor N with one AB edge per STEP")
        pulses = motors[motor]["motor_steps_per_revolution"] * motors[motor]["microsteps"]
        if encoders[channel]["counts_per_revolution"] != pulses:
            _reject("SIM2_ENCODER_MAPPING", "Selected encoder counts do not match the explicitly authored one-edge-per-STEP lab mapping")
        mapped.add(channel)
    return sorted(deepcopy(supplied), key=lambda item: item["encoder_channel"])


def prepare_configuration(service: SetupService, expected_binding, *, run_id, source_root, source_files, encoder_mapping=None):
    """Produce a source-bound manifest from exactly one reviewed generation.

    Caller supplies the binding it reviewed. A later settings change is refused;
    the manifest records the captured revision, not a claim of ongoing validity.
    Runners must call verify_configuration immediately before constructing their
    isolated transport, and keep this immutable context through fault recovery.
    """
    if type(expected_binding) is not dict or set(expected_binding) != BINDING_KEYS:
        _reject("SIM2_BINDING", "Supply the complete reviewed configuration binding")
    if any(type(expected_binding[key]) is not int for key in ("revision", "generation")):
        _reject("SIM2_BINDING", "Binding revisions and generations must be integers")
    try:
        if type(run_id) is not str or str(uuid.UUID(run_id)) != run_id:
            raise ValueError()
    except (ValueError, AttributeError):
        _reject("SIM2_CONTEXT", "Supply an explicit canonical UUID for this disconnected run")
    snapshot = service.backup_snapshot()
    binding = configuration_binding(snapshot)
    if canonical(expected_binding) != canonical(binding):
        _reject("SIM2_STALE", "Settings identity, epoch, revision, generation or digest changed; review the current settings")
    for key, expected in GUARDS.items():
        if canonical(snapshot.get(key)) != canonical(expected):
            _reject("SIM2_AUTHORITY", "The setup snapshot must retain every disconnected guard", key)
    active = snapshot["active"]
    if active is None or canonical(snapshot["draft"]) != canonical(active["draft"]):
        _reject("SIM2_REVIEW", "Review and save the current draft before constructing a runtime")
    checked = validate_draft(active["draft"], require_complete=True)
    if (active["generation"] != binding["generation"] or active["configuration_sha256"] != digest(active["draft"]) or
            canonical(active["calculations"]) != canonical(checked["calculations"]) or
            canonical(active["wiring"]) != canonical(checked["wiring"])):
        _reject("SIM2_DERIVED", "Saved derived configuration does not match independent recomputation")
    mapping = _encoder_mapping(active["draft"], encoder_mapping)
    inventory = _source_inventory(source_root, source_files)
    source_digest = digest(inventory)
    config_digest = digest({"configuration_binding": binding, "virtual_encoder_mapping": mapping})
    context = {"schema_version": 1, "kind": "cnc3_sim2_context", "run_id": run_id,
               "configuration_binding": binding, "virtual_encoder_mapping": mapping, "config_digest": config_digest,
               "source_digest": source_digest, "gateware_build_id": SIM_GATEWARE_BUILD,
               "transport": "disconnected_compiled_rtl_spi", "physical_backend_allowed": False}
    context_sha = digest(context)
    host = {"active_mask": 0, "fitted_mask": FITTED_MASK, "config_hash": _identifier(config_digest),
            "provider_session": _identifier(context_sha), "source_id": _identifier(source_digest),
            "scale": [0.0] * 12, "max_velocity": [0.0] * 12,
            "timing_ticks": [[250] * 4 for _ in range(12)],
            "required_encoder_mask": 0, "dout_enable_mask": 0,
            "alarm_trip_mask": 0, "alarm_on_no_current": 0,
            "encoder_filter_ticks": 1, "encoder_expansion_class": 0, "mpg_config": 0}
    motors = []
    for motor in active["draft"]["motors"]:
        channel = _resource_index(motor["resource"], "SIM.M", 12)
        params = _motor_parameters(motor)
        host["active_mask"] |= 1 << channel
        for name in ("scale", "max_velocity", "timing_ticks"):
            host[name][channel] = params[name]
        motors.append({"channel": channel, "motor_id": motor["id"], "axis": motor["axis"],
                       "resource": motor["resource"], "source_unit": motor["unit"],
                       "selected_timing_ns": [motor[field] for field in TIMINGS], **params,
                       "provenance": "reviewed_unverified_user_selections", "physically_qualified": False})
    host["alarm_trip_mask"] = host["alarm_on_no_current"] = host["active_mask"]
    selections = {}
    for name, prefix, count in (("inputs", "SIM.DI", 24), ("outputs", "SIM.DO", 16), ("encoders", "SIM.ABZ", 4)):
        selections[name] = sorted(({"channel": _resource_index(item["resource"], prefix, count), **deepcopy(item)}
                                   for item in active["draft"][name]), key=lambda item: item["channel"])
    for encoder in selections["encoders"]:
        host["required_encoder_mask"] |= 1 << encoder["channel"]
    for output in selections["outputs"]:
        host["dout_enable_mask"] |= 1 << output["channel"]
    payload = {"schema_version": 1, "kind": "cnc3_sim2_reviewed_runtime", "scope": "disconnected_integration_candidate",
               "configuration_binding": binding, "catalog_sha256": snapshot["catalog_sha256"],
               "profile_id": active["draft"]["profile_id"], "machine_name": active["draft"]["machine_name"],
               "simulation_context": {**context, "context_sha256": context_sha, "source_sha256": inventory},
               "cnc3_host": host, "motors": sorted(motors, key=lambda item: item["channel"]),
               "virtual_encoder_mapping": mapping, "mapping_provenance": "explicit_lab_selection_unmeasured",
               "configured_io": selections, "output_groups": checked["output_groups"],
               "wire_identifiers_are_authentication": False, "physical_backend_allowed": False,
               "physical_measurements": 0, "api_calls": 0, **deepcopy(GUARDS)}
    return {**payload, "manifest_sha256": digest(payload)}


def verify_configuration(manifest, service, *, source_root, expected_source_files):
    """Reject altered/stale manifests and changed sources before a lab run."""
    if type(manifest) is not dict:
        _reject("SIM2_MANIFEST", "Expected a complete runtime manifest")
    try:
        payload = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
        if type(manifest.get("manifest_sha256")) is not str or digest(payload) != manifest["manifest_sha256"]:
            _reject("SIM2_MANIFEST", "Manifest bytes changed after preparation")
        trusted_inventory = _source_inventory(source_root, expected_source_files)
        if set(manifest["simulation_context"]["source_sha256"]) != set(trusted_inventory):
            _reject("SIM2_SOURCE_CLOSURE", "Manifest omits or adds a runtime dependency from the trusted source set")
        expected = prepare_configuration(service, manifest["configuration_binding"],
            run_id=manifest["simulation_context"]["run_id"], source_root=source_root,
            source_files=expected_source_files,
            encoder_mapping=manifest["virtual_encoder_mapping"])
    except (KeyError, TypeError, ValueError, RecursionError) as exc:
        if isinstance(exc, ConfigurationError):
            raise
        _reject("SIM2_MANIFEST", "Malformed runtime manifest")
    if canonical(manifest) != canonical(expected):
        _reject("SIM2_MANIFEST", "Runtime manifest differs from fresh source and configuration recomputation")
    return deepcopy(expected)
