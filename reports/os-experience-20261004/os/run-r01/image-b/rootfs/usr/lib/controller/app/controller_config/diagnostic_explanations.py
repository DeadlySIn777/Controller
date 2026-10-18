"""Offline explanations of supplied fault evidence; no transport or machine API.

Records are reported data, not authenticated hardware measurements. A simulation
record stays simulation evidence even when its authored measurement is fresh.
"""
from copy import deepcopy
import math
import re

from .model import ConfigurationError


VERSION = "diagnostic-explanations/1"
SOURCES = {"measured", "commanded", "reported"}
RECORD_KEYS = {"schema_version", "code", "resource", "source", "observations", "machine_response"}
OBSERVATION_KEYS = {"name", "value", "unit", "source", "valid", "fresh", "age_ms", "max_age_ms"}
CATALOG = {
    "MOTOR_DRIVE_ALARM": (
        "Motor drive alarm reported",
        "An alarm was recorded for this motor channel. The drive's own diagnostic code and fresh observations are needed to identify the cause.",
        [("drive_code", "Read the drive's diagnostic code", "Record the exact drive model and its displayed alarm code, then consult its approved manual. An alarm alone does not identify a wiring or mechanical cause."),
         ("timeline", "Review the events around the alarm", "Compare fresh measured feedback with command history. Commanded velocity does not establish actual movement."),
         ("alarm_path", "Verify the alarm path", "Under the approved power-off service procedure, compare the alarm harness and configured polarity with the exact machine documentation. This explanation supplies no physical pin assignments.")]),
    "TELEMETRY_STALE": (
        "Telemetry is out of date",
        "The record reports stale telemetry. Old values cannot describe the current machine state, including zero values.",
        [("freshness", "Check observation age and validity", "Use the source timestamp, age and its approved freshness limit. A recent command does not refresh a measurement."),
         ("connection", "Inspect the diagnostic connection history", "Review recorded disconnects, resets, sequence gaps and supply events. Missing telemetry does not by itself identify which component failed.")]),
    "WATCHDOG_TIMEOUT": (
        "Watchdog timeout reported",
        "A watchdog timeout was recorded. It indicates that expected progress or communication was not reported in time; the record alone does not identify the cause or prove that motion stopped.",
        [("progress", "Review progress and timing evidence", "Compare watchdog, communication and reset records at the fault time. Keep the watchdog deadline separate from physical machine stopping time."),
         ("response", "Find fresh response observations", "Look for measured permission, output and motion feedback. An inhibit request or fault latch is not confirmation of terminal state or mechanical rest.")]),
    "SMART_OUTPUT_FAULT": (
        "Smart output fault reported",
        "A fault was recorded for a smart output. Current, supply and temperature observations may help distinguish possible causes; the fault code alone cannot prove an overload, short circuit or failed component.",
        [("load", "Review the load and group budget", "The retained IS-2 requirement is 0.5 A per channel and 2 A per group of four. Compare the exact qualified load profile and fresh current measurements; these limits are not measured values."),
         ("output_path", "Inspect the output path", "Under the approved power-off service procedure, review the load and harness against the exact machine documentation. Do not infer terminal voltage from the commanded output bit.")]),
}
COMMON_CHECK = {"id": "recovery", "title": "Use the reviewed recovery procedure",
    "detail": "A cleared fault or restored configuration does not verify position, restore homing or authorize restart. Complete the required independent checks before a deliberate restart.", "action": "inspection_only"}
MEASUREMENT_UNITS = {"velocity": {"mm/s", "in/s"}, "spindle_speed": {"rpm"},
    "output_voltage": {"V"}, "output_current": {"A"}, "supply_voltage": {"V"}, "temperature": {"degC"}}
BOOLEAN_OBSERVATIONS = {"drive_alarm", "watchdog_fault", "output_fault", "motion_inhibited",
    "spindle_enabled", "output_enabled", "enable_feedback"}


def _require(ok, message):
    if not ok:
        raise ConfigurationError("DIAGNOSTIC_RECORD", message)


def _text(value, maximum=120):
    _require(type(value) is str and bool(value.strip()) and len(value) <= maximum
             and all(ord(c) >= 32 for c in value), "Expected bounded printable diagnostic text")
    return value


def _keys(value, required, optional=()):
    _require(type(value) is dict and set(required) <= set(value)
             and set(value) <= set(required) | set(optional), "Unknown or missing diagnostic record fields")


def _integer(value, label, maximum=2**53 - 1):
    _require(type(value) is int and 0 <= value <= maximum, f"Invalid {label}")


def _resource(value):
    _keys(value, {"kind", "id", "axis"})
    kind, identifier, axis = value["kind"], _text(value["id"], 64), value["axis"]
    _require(kind in ("motor", "smart_output", "controller", "compute", "esp", "storage", "unknown"), "Unknown resource kind")
    if axis is not None:
        _text(axis, 40)
    label = identifier
    if kind == "motor":
        _require(re.fullmatch(r"M(?:[0-9]|1[01])", identifier) is not None, "Motor IDs must be logical M0 through M11")
        label = f"M{int(identifier[1:]) + 1}"
    elif kind == "smart_output":
        _require(re.fullmatch(r"DO(?:[0-9]|1[0-5])", identifier) is not None, "Output IDs must be logical DO0 through DO15")
    integrated = kind in ("motor", "smart_output", "controller")
    service = ("Soldered FPGA and I/O regions are serviced through motherboard repair or whole-motherboard replacement. An external motor drive or load is a separate component."
               if integrated else "Only an exact qualified commodity module may be exchanged under its approved powered-off service procedure."
               if kind in ("compute", "esp", "storage") else "The service unit is unknown; verify the exact equipment identity.")
    return {"kind": kind, "logical_id": identifier, "display_label": label, "axis": axis,
            "label": f"{axis + ' · ' if axis else ''}{label}" + (f" (logical {identifier})" if kind == "motor" else ""),
            "integrated_motherboard_region": integrated, "physical_location_verified": False,
            "service_guidance": service}


def _observation(item):
    _keys(item, {"name", "source"}, OBSERVATION_KEYS - {"name", "source"})
    name, source = _text(item["name"], 64), item["source"]
    _require(re.fullmatch(r"[A-Za-z][A-Za-z0-9_.-]*", name) is not None, "Invalid observation name")
    _require(type(source) is str and source in SOURCES, "Observation source must distinguish measured, commanded and reported")
    value, unit = item.get("value"), item.get("unit")
    _require(value is None or type(value) in (bool, int, float, str), "Observation value must be a scalar")
    if type(value) in (int, float):
        _require((type(value) is not float or math.isfinite(value)) and abs(value) <= 10**12, "Observation number is nonfinite or outside the bounded record range")
    elif type(value) is str:
        _text(value, 200)
    if unit is not None:
        _text(unit, 24)
    for flag in ("valid", "fresh"):
        _require(item.get(flag) is None or type(item[flag]) is bool, f"{flag} must be boolean or unavailable")
    for field in ("age_ms", "max_age_ms"):
        if item.get(field) is not None:
            _integer(item[field], field)
    reasons = []
    if item.get("valid") is not True:
        reasons.append("invalid_or_missing_validity")
    if item.get("fresh") is not True:
        reasons.append("stale_or_missing_freshness")
    age, limit = item.get("age_ms"), item.get("max_age_ms")
    if age is None or limit is None:
        reasons.append("missing_age_or_freshness_limit")
    elif age > limit:
        reasons.append("age_exceeds_freshness_limit")
    if value is None:
        reasons.append("missing_value")
    if name not in MEASUREMENT_UNITS and name not in BOOLEAN_OBSERVATIONS:
        reasons.append("unknown_observation_interpretation")
    if name in MEASUREMENT_UNITS and (type(value) not in (int, float) or unit not in MEASUREMENT_UNITS[name]):
        reasons.append("missing_or_incompatible_measurement_unit")
    if name in BOOLEAN_OBSERVATIONS and type(value) is not bool:
        reasons.append("boolean_feedback_required")
    if name in BOOLEAN_OBSERVATIONS and unit not in (None, "bool"):
        reasons.append("incompatible_boolean_feedback_unit")
    available = not reasons
    label = name.replace("_", " ").capitalize()
    reading = str(value).lower() if type(value) is bool else str(value)
    text = (f"{label}: unavailable ({', '.join(reasons).replace('_', ' ')})." if not available else
            f"{source.capitalize()} {name.replace('_', ' ')}: {reading}{' ' + unit if unit else ''}.")
    if available and source == "commanded":
        text += " This is a request, not measured behavior."
    elif available and source == "reported":
        text += " This is a reported indication, not an independent measurement."
    return {"name": name, "source": source, "available": available, "value": deepcopy(value) if available else None,
            "unit": unit, "age_ms": age, "max_age_ms": limit, "unavailable_reasons": reasons,
            "supports_measured_state": available and source == "measured", "text": text}


def explain_fault(record):
    """Explain fault content or a recorder fault envelope, without mutating it."""
    _require(type(record) is dict, "Expected a diagnostic record object")
    envelope = None
    if "data" in record or "kind" in record:
        _keys(record, {"schema_version", "simulation_only", "timestamp_ns", "source", "sequence", "kind", "data"})
        _require(type(record["schema_version"]) is int and record["schema_version"] == 1
                 and record["simulation_only"] is True and record["kind"] == "fault", "Expected a simulation recorder fault envelope")
        _integer(record["timestamp_ns"], "timestamp_ns", 2**63 - 1)
        _integer(record["sequence"], "sequence", 2**63 - 1)
        _text(record["source"], 64)
        _require(re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}", record["source"]) is not None, "Recorder source needs a stable ASCII identifier")
        envelope = deepcopy({k: v for k, v in record.items() if k != "data"})
        record = record["data"]
    _keys(record, RECORD_KEYS)
    _require(type(record["schema_version"]) is int and record["schema_version"] == 1, "Unsupported diagnostic record version")
    code = _text(record["code"], 80)
    _require(re.fullmatch(r"[A-Za-z0-9_.:-]+", code) is not None, "Invalid fault code")
    resource = _resource(record["resource"])
    expected_kind = {"MOTOR_DRIVE_ALARM": "motor", "SMART_OUTPUT_FAULT": "smart_output"}.get(code)
    _require(expected_kind is None or resource["kind"] == expected_kind, "Fault code does not match its resource kind")
    _keys(record["source"], {"type", "reference"})
    _require(record["source"]["type"] in ("simulation_fixture", "controller_telemetry", "imported_record"), "Unknown fault source type")
    _text(record["source"]["reference"], 300)
    if envelope:
        _require(record["source"]["type"] != "controller_telemetry", "Simulation envelope cannot promote its content to physical controller telemetry")
    observations, responses, seen = [], [], set()
    for group, output in (("observations", observations), ("machine_response", responses)):
        items = record[group]
        _require(type(items) is list and len(items) <= 32, "Expected at most 32 bounded observations per group")
        for item in items:
            explained = _observation(item)
            identity = (explained["name"], explained["source"])
            _require(identity not in seen, "Duplicate/conflicting observation identity")
            seen.add(identity)
            output.append(explained)
    known = code in CATALOG
    title, summary, checks = CATALOG.get(code, (
        f"Unrecognized fault code: {code}",
        f"The record contains code {code}. This explanation catalog has no verified meaning or cause for that code.",
        [("reference", "Find the exact fault-code reference", "Preserve this record and consult the matching firmware or equipment documentation before drawing a conclusion.")]))
    confirmed = [x for x in responses if x["supports_measured_state"]]
    response_text = ("Fresh measured response values are reported below. They describe only the named signals at their recorded age."
                     if confirmed else "Actual machine response is unavailable: no fresh valid measured response was supplied.")
    response_text += " Faults, inhibit requests and zero-valued samples do not establish whole-machine rest, retained position or restart permission."
    simulation = envelope is not None or record["source"]["type"] == "simulation_fixture"
    return {"schema_version": 1, "code": code, "known_code": known, "title": title,
        "summary": summary, "observations": observations,
        "machine_response": {"summary": response_text, "measured": confirmed,
                             "observations": responses, "position_retained": "unverified", "whole_machine_stopped": "unverified", "restart_authorized": False},
        "checks": [{"id": key, "title": label, "detail": detail, "action": "inspection_only"} for key, label, detail in checks] + [deepcopy(COMMON_CHECK)],
        "resource": resource,
        "wiring": {"scope": "logical_resource_reference_only", "physical_pin_guidance": False,
                   "logical_resource": resource["logical_id"], "terminals": [],
                   "required_reference": "Exact approved machine wiring and equipment profile; not supplied by this explanation"},
        "provenance": {"catalog": VERSION, "method": "deterministic_offline_rules", "record_source": deepcopy(record["source"]),
                       "recorder_envelope": envelope, "input_authenticated": False,
                       "timestamp_basis": "caller_declared_simulation_monotonic_ns_not_physical_clock" if envelope else "no_envelope_timestamp",
                       "references": ["docs/MOTHERBOARD_IS2.md", "docs/AI_SETUP_CONTRACT.md"]},
        "scope": {"simulation_only": simulation, "record_only": True, "physical_state_verified": False,
                  "causal_diagnosis_verified": False, "machine_authority": False},
        "paid_calls": 0, "executed": False, "machine_commands": []}


def example_fault():
    """Authored Y2/M2 fixture: requested velocity is not measured velocity."""
    return {"schema_version": 1, "code": "MOTOR_DRIVE_ALARM",
        "resource": {"kind": "motor", "id": "M2", "axis": "Y2"},
        "source": {"type": "simulation_fixture", "reference": "authored-diagnostic-example-v1"},
        "observations": [
            {"name": "drive_alarm", "value": True, "unit": None, "source": "reported", "valid": True, "fresh": True, "age_ms": 0, "max_age_ms": 1000},
            {"name": "velocity", "value": 82, "unit": "mm/s", "source": "commanded", "valid": True, "fresh": True, "age_ms": 0, "max_age_ms": 1000}],
        "machine_response": []}
