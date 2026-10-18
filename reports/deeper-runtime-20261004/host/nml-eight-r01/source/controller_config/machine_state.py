"""Read-only state projection of explicitly bound simulation observations.

This is not a hardware monitor, authority service or health score. Configuration
and wiring come from one independently validated active setup definition. Raw
recorder envelopes remain detached and unchanged; only typed, bound facts enter
the projection. Freshness is evaluated on a caller-declared simulation timeline.
"""
from copy import deepcopy
import math
import re

from .model import ConfigurationError
from .service import canonical, digest
from .setup_service import validate_draft

DOMAINS = ("motion", "spindle", "io", "safety", "modules", "temperatures", "network", "controller")
SOURCES = ("measured", "commanded", "reported")
# Matches the recorder's maximum chunk/count inventory; the separate 8 MiB
# byte cap is tighter for ordinary envelopes and prevents an unbounded report.
MAX_RECORDS = 96 * 1024
MAX_RECORD_BYTES = 16384
MAX_TOTAL_BYTES = 8 * 1024 * 1024
MAX_TIMESTAMP = 2**63 - 1
BINDING_FIELDS = {"store_id", "epoch", "revision", "generation", "configuration_sha256"}
OBSERVATION_FIELDS = {"domain", "resource", "key", "value", "unit", "source", "valid", "fresh", "age_ms", "max_age_ms"}
ENVELOPE_FIELDS = {"schema_version", "simulation_only", "timestamp_ns", "source", "sequence", "kind", "data"}
GUARDS = {"simulation_only": True, "physical_evidence": False, "executed": False,
          "machine_commands": [], "grants_authority": False}

# Static entries are simulation resource vocabulary, not detected equipment.
# type, exact unit, allowed source categories, numeric bounds / string enum.
_ALL = SOURCES
_OBSERVED = ("measured", "reported")
FIXED_FIELDS = {
    "spindle": {"resources": ["SIM.SPINDLE"], "fields": {
        "speed": ("number", "rpm", _ALL, (0, 1000000)),
        "running": ("boolean", "bool", _ALL, None),
        "alarm": ("boolean", "bool", _OBSERVED, None)}},
    "safety": {"resources": ["SIM.SAFETY"], "fields": {
        "estop_active": ("boolean", "bool", _OBSERVED, None),
        "watchdog_fault": ("boolean", "bool", _OBSERVED, None),
        "inhibit_observed": ("boolean", "bool", _OBSERVED, None)}},
    "modules": {"resources": ["SIM.COMPUTE", "SIM.ESP", "SIM.STORAGE"], "fields": {
        "present": ("boolean", "bool", _OBSERVED, None),
        "identity": ("string", "text", ("reported",), None),
        "fault": ("boolean", "bool", _OBSERVED, None)}},
    "temperatures": {"resources": ["SIM.MOTHERBOARD", "SIM.COMPUTE", "SIM.ESP", "SIM.SPINDLE"], "fields": {
        "temperature": ("number", "degC", _OBSERVED, (-273.15, 1000))}},
    "network": {"resources": ["SIM.NETWORK"], "fields": {
        "link_up": ("boolean", "bool", _OBSERVED, None),
        "latency": ("number", "ms", _OBSERVED, (0, 3600000)),
        "rx_errors": ("integer", "count", _OBSERVED, (0, 2**53 - 1))}},
    "controller": {"resources": ["SIM.CONTROLLER"], "fields": {
        "fault": ("boolean", "bool", _OBSERVED, None),
        "uptime": ("number", "s", ("reported",), (0, 2**53 - 1)),
        "state": ("string", "text", ("reported",), ("booting", "idle", "running", "fault", "service"))}},
}


class MachineStateError(ConfigurationError):
    pass


def _require(condition, code, message):
    if not condition:
        raise MachineStateError(code, message)


def _integer(value, high=MAX_TIMESTAMP, low=0):
    return type(value) is int and low <= value <= high


def _number(value, low, high):
    return ((type(value) is int and low <= value <= high) or
            (type(value) is float and math.isfinite(value) and low <= value <= high))


def _bounded_json(value, limit):
    def walk(item, depth=0):
        _require(depth <= 16, "MACHINE_STATE_INPUT", "Input nesting is too deep")
        if type(item) is dict:
            _require(len(item) <= 512 and all(type(k) is str and len(k) <= 256 for k in item), "MACHINE_STATE_INPUT", "Invalid bounded JSON object")
            for child in item.values():
                walk(child, depth + 1)
        elif type(item) is list:
            _require(len(item) <= MAX_RECORDS, "MACHINE_STATE_INPUT", "Input list is too long")
            for child in item:
                walk(child, depth + 1)
        else:
            _require(item is None or type(item) is bool or
                     (type(item) is str and len(item) <= limit) or
                     (type(item) in (int, float) and _number(item, -MAX_TIMESTAMP, MAX_TIMESTAMP)),
                     "MACHINE_STATE_INPUT", "Expected bounded finite JSON values")
    walk(value)
    try:
        size = len(canonical(value))
    except (ValueError, TypeError, UnicodeError, RecursionError) as error:
        raise MachineStateError("MACHINE_STATE_INPUT", "Input cannot be represented as finite UTF-8 JSON") from error
    _require(size <= limit, "MACHINE_STATE_SIZE", "Input exceeds its byte limit")
    return size


def _definition(snapshot):
    _require(type(snapshot) is dict, "MACHINE_STATE_SETUP", "Expected a setup snapshot")
    _bounded_json(snapshot, 2 * 1024 * 1024)
    _require(snapshot.get("simulation_only") is True, "MACHINE_STATE_SETUP", "An explicitly disconnected setup snapshot is required")
    if snapshot.get("active") is None:
        return None
    active = snapshot["active"]
    _require(snapshot.get("initialized") is True and type(active) is dict and
             set(active) == {"generation", "draft", "calculations", "wiring", "configuration_sha256"},
             "MACHINE_STATE_SETUP", "Active setup definition is invalid")
    _require(all(type(snapshot.get(k)) is str and re.fullmatch(r"[A-Za-z0-9_.:-]{1,128}", snapshot[k]) for k in ("store_id", "epoch")),
             "MACHINE_STATE_SETUP", "Missing bounded setup identity")
    _require(_integer(snapshot.get("revision"), 2**53 - 1) and
             type(snapshot.get("current_revision")) is int and snapshot["current_revision"] == snapshot["revision"] and
             _integer(snapshot.get("generation"), 2**53 - 1, 1) and
             type(active["generation"]) is int and active["generation"] == snapshot["generation"],
             "MACHINE_STATE_SETUP", "Setup revisions or generations disagree")
    checked = validate_draft(active["draft"], require_complete=True)
    _require(active["configuration_sha256"] == digest(active["draft"]) and
             canonical(active["calculations"]) == canonical(checked["calculations"]) and
             canonical(active["wiring"]) == canonical(checked["wiring"]),
             "MACHINE_STATE_SETUP", "Active configuration, calculations or wiring are inconsistent")
    binding = {"store_id": snapshot["store_id"], "epoch": snapshot["epoch"],
               "revision": snapshot["current_revision"], "generation": snapshot["generation"],
               "configuration_sha256": active["configuration_sha256"]}
    definition = {"schema_version": 1, "binding": binding, "configuration": deepcopy(active["draft"]),
                  "calculations": deepcopy(checked["calculations"]), "wiring": deepcopy(checked["wiring"]),
                  "configured_resources": deepcopy(checked["assigned_resources"]),
                  "provenance": "validated_active_simulation_configuration_not_physical_equipment", "qualified": False}
    return {**definition, "definition_sha256": digest(definition)}


def configuration_binding(setup_snapshot):
    """Return the exact active binding, or None before a validated active commit."""
    definition = _definition(setup_snapshot)
    return deepcopy(definition["binding"]) if definition is not None else None


def _field(domain, resource, key, definition):
    _require(domain in DOMAINS and type(resource) is str and type(key) is str,
             "MACHINE_STATE_FIELD", "Unknown observation domain or field")
    configuration = definition["configuration"]
    spec = None
    if domain == "motion":
        motor = next((m for m in configuration["motors"] if m["resource"] == resource), None)
        encoder = next((m for m in configuration["encoders"] if m["resource"] == resource), None)
        if motor:
            spec = {"position": ("number", motor["unit"], _ALL, (-1e12, 1e12)),
                    "velocity": ("number", motor["unit"] + "/s", _ALL, (-1e9, 1e9)),
                    "alarm": ("boolean", "bool", _OBSERVED, None)}.get(key)
        elif encoder and key == "count":
            spec = ("integer", "count", _OBSERVED, (-(2**53 - 1), 2**53 - 1))
    elif domain == "io":
        input_ = any(i["resource"] == resource for i in configuration["inputs"])
        output = any(i["resource"] == resource for i in configuration["outputs"])
        if input_ or output:
            spec = {"state": ("boolean", "bool", _ALL if output else _OBSERVED, None),
                    "voltage": ("number", "V", _OBSERVED, (-1000, 1000))}.get(key)
            if output and key in ("current", "alarm"):
                spec = {"current": ("number", "A", _OBSERVED, (-1000, 1000)),
                        "alarm": ("boolean", "bool", _OBSERVED, None)}[key]
    else:
        entry = FIXED_FIELDS[domain]
        if resource in entry["resources"]:
            spec = entry["fields"].get(key)
    _require(spec is not None, "MACHINE_STATE_FIELD", "Unknown field or resource outside the validated configuration/simulation vocabulary")
    return spec


def _observation(value, definition):
    _require(type(value) is dict and set(value) == OBSERVATION_FIELDS, "MACHINE_STATE_OBSERVATION", "Unexpected observation fields")
    type_, unit, sources, bound = _field(value["domain"], value["resource"], value["key"], definition)
    _require(value["unit"] == unit and value["source"] in sources, "MACHINE_STATE_UNIT", "Observation unit or source category is inappropriate for this field")
    _require(type(value["valid"]) is bool and type(value["fresh"]) is bool and
             _number(value["age_ms"], 0, 3600000) and _number(value["max_age_ms"], 0, 3600000),
             "MACHINE_STATE_VALIDITY", "Validity, freshness and bounded ages must be explicit")
    v = value["value"]
    if v is None and value["valid"] is False:
        return
    valid_type = ((type_ == "boolean" and type(v) is bool) or
                  (type_ == "number" and _number(v, *bound)) or
                  (type_ == "integer" and type(v) is int and bound[0] <= v <= bound[1]) or
                  (type_ == "string" and type(v) is str and 0 < len(v) <= 128 and
                   all(ord(c) >= 32 for c in v) and (bound is None or v in bound)))
    _require(valid_type, "MACHINE_STATE_VALUE", "Observation value has the wrong type, range or enum")


def machine_observation_schema():
    """Strict data schema plus field vocabulary; dynamic units use the active draft."""
    def obj(properties):
        return {"type": "object", "properties": properties, "required": list(properties), "additionalProperties": False}
    binding = obj({"store_id": {"type": "string", "minLength": 1, "maxLength": 128},
                   "epoch": {"type": "string", "minLength": 1, "maxLength": 128},
                   "revision": {"type": "integer", "minimum": 0, "maximum": 2**53 - 1},
                   "generation": {"type": "integer", "minimum": 1, "maximum": 2**53 - 1},
                   "configuration_sha256": {"type": "string", "pattern": "^[0-9a-f]{64}$"}})
    observation = obj({"domain": {"enum": list(DOMAINS)}, "resource": {"type": "string", "maxLength": 64},
                       "key": {"type": "string", "maxLength": 64},
                       "value": {"type": ["number", "boolean", "string", "null"]},
                       "unit": {"type": "string", "maxLength": 16}, "source": {"enum": list(SOURCES)},
                       "valid": {"type": "boolean"}, "fresh": {"type": "boolean"},
                       "age_ms": {"type": "number", "minimum": 0, "maximum": 3600000},
                       "max_age_ms": {"type": "number", "minimum": 0, "maximum": 3600000}})
    variants = []
    def variant(domain, resources, key, spec):
        type_, unit, sources, bound = spec
        value = {"type": type_}
        if type_ in ("number", "integer"):
            value.update(minimum=bound[0], maximum=bound[1])
        elif type_ == "string":
            value.update(minLength=1, maxLength=128, pattern="^[^\\x00-\\x1f]+$")
            if bound is not None:
                value["enum"] = list(bound)
        variants.append({"properties": {"domain": {"const": domain}, "resource": {"enum": resources},
                         "key": {"const": key}, "unit": {"const": unit}, "source": {"enum": list(sources)},
                         "value": {"anyOf": [value, {"type": "null"}]}}})
    motors = [f"SIM.M{i}" for i in range(12)]
    for unit in ("mm", "in"):
        variant("motion", motors, "position", ("number", unit, _ALL, (-1e12, 1e12)))
        variant("motion", motors, "velocity", ("number", unit + "/s", _ALL, (-1e9, 1e9)))
    variant("motion", motors, "alarm", ("boolean", "bool", _OBSERVED, None))
    variant("motion", [f"SIM.ABZ{i}" for i in range(4)], "count", ("integer", "count", _OBSERVED, (-(2**53 - 1), 2**53 - 1)))
    for direction, maximum in (("DI", 24), ("DO", 16)):
        resources = [f"SIM.{direction}{i}" for i in range(maximum)]
        variant("io", resources, "state", ("boolean", "bool", _ALL if direction == "DO" else _OBSERVED, None))
        variant("io", resources, "voltage", ("number", "V", _OBSERVED, (-1000, 1000)))
        if direction == "DO":
            variant("io", resources, "current", ("number", "A", _OBSERVED, (-1000, 1000)))
            variant("io", resources, "alarm", ("boolean", "bool", _OBSERVED, None))
    for domain, entry in FIXED_FIELDS.items():
        for key, spec in entry["fields"].items():
            variant(domain, entry["resources"], key, spec)
    observation["allOf"] = [{"oneOf": variants},
                            {"if": {"properties": {"value": {"type": "null"}}},
                             "then": {"properties": {"valid": {"const": False}}}}]
    data = obj({"schema_version": {"type": "integer", "const": 1}, "kind": {"const": "machine_observation"},
                "configuration_binding": binding,
                "observations": {"type": "array", "minItems": 1, "maxItems": 64, "items": observation}})
    return {"schema_version": 1, "data_schema": data, "envelope": "diagnostic_recorder sample envelope schema 1",
            "domains": list(DOMAINS), "fixed_fields": deepcopy(FIXED_FIELDS),
            "configured_fields": {"motion": "Configured SIM.M*: position (motor unit), velocity (unit/s), alarm (bool); configured SIM.ABZ*: count (count)",
                                  "io": "Configured SIM.DI*/DO*: state (bool), voltage (V); DO only current (A), alarm (bool)"},
            "binding_policy": "Exact current active store/epoch/revision/generation/configuration SHA; no extra fields or type coercion",
            "timeline": "Caller-declared simulation nanoseconds only; default latest supplied valid-envelope timestamp is a frozen timeline, not wall clock",
            "max_records": MAX_RECORDS, "max_total_bytes": MAX_TOTAL_BYTES, **deepcopy(GUARDS)}


def example_machine_observation(setup_snapshot, timestamp_ns=0, sequence=0):
    """Authored demo envelope with command/reported values, never fabricated measurements."""
    definition = _definition(setup_snapshot)
    _require(definition is not None, "MACHINE_STATE_NO_ACTIVE", "Commit a complete simulation configuration first")
    _require(_integer(timestamp_ns) and _integer(sequence), "MACHINE_STATE_INPUT", "Invalid demonstration timestamp or sequence")
    motor = definition["configuration"]["motors"][0]
    observations = [
        {"domain": "motion", "resource": motor["resource"], "key": "position", "value": 12.5,
         "unit": motor["unit"], "source": "commanded", "valid": True, "fresh": True, "age_ms": 0, "max_age_ms": 1000},
        {"domain": "controller", "resource": "SIM.CONTROLLER", "key": "state", "value": "service",
         "unit": "text", "source": "reported", "valid": True, "fresh": True, "age_ms": 0, "max_age_ms": 1000}]
    return {"schema_version": 1, "simulation_only": True, "timestamp_ns": timestamp_ns,
            "source": "authored-simulation-demo", "sequence": sequence, "kind": "sample",
            "data": {"schema_version": 1, "kind": "machine_observation",
                     "configuration_binding": deepcopy(definition["binding"]), "observations": observations}}


def build_machine_state(setup_snapshot, record_envelopes, *, evaluation_timestamp_ns=None):
    _require(type(record_envelopes) is list and len(record_envelopes) <= MAX_RECORDS,
             "MACHINE_STATE_INPUT", "Expected a bounded list of supplied simulation envelopes")
    _require(evaluation_timestamp_ns is None or _integer(evaluation_timestamp_ns),
             "MACHINE_STATE_TIME", "Evaluation time must be bounded simulation nanoseconds")
    total = 0
    for record in record_envelopes:
        total += _bounded_json(record, MAX_RECORD_BYTES)
        _require(total <= MAX_TOTAL_BYTES, "MACHINE_STATE_SIZE", "Supplied records exceed their total byte limit")
    definition_error = None
    try:
        definition = _definition(setup_snapshot)
    except ConfigurationError as error:
        definition, definition_error = None, error.as_dict()
    binding = definition["binding"] if definition else None
    rejected, unrecognized, duplicates, accepted, candidates = [], [], [], [], {}
    envelopes, identities, producer_timelines = [], {}, {}
    for index, record in enumerate(record_envelopes):
        try:
            _require(type(record) is dict and set(record) == ENVELOPE_FIELDS and
                     type(record["schema_version"]) is int and record["schema_version"] == 1 and
                     record["simulation_only"] is True and _integer(record["timestamp_ns"]) and _integer(record["sequence"]) and
                     type(record["source"]) is str and re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.:-]{0,63}", record["source"]) and
                     record["kind"] in ("sample", "event", "fault") and type(record["data"]) is dict,
                     "MACHINE_STATE_ENVELOPE", "Invalid simulation recorder envelope")
            identity = (record["source"], record["sequence"])
            identities.setdefault(identity, []).append(index)
            producer_timelines.setdefault(record["source"], {})[record["sequence"]] = record["timestamp_ns"]
            envelopes.append((index, record))
        except ConfigurationError as error:
            rejected.append({"record_index": index, **error.as_dict()})
    conflicts = {index for indexes in identities.values() if len({digest(record_envelopes[i]) for i in indexes}) > 1 for index in indexes}
    # An inconsistent producer cannot refresh a fact by replaying an older
    # sequence with a newer timestamp. Quarantine the whole supplied source
    # stream: removing only its bad newest row would resurrect older facts.
    source_errors = {record_envelopes[index]["source"]: "MACHINE_STATE_DUPLICATE" for index in conflicts}
    for producer, timeline in producer_timelines.items():
        times = [value for _, value in sorted(timeline.items())]
        if any(after < before for before, after in zip(times, times[1:])):
            source_errors.setdefault(producer, "MACHINE_STATE_SEQUENCE")
    timestamp = evaluation_timestamp_ns
    if timestamp is None and envelopes:
        timestamp = max(record["timestamp_ns"] for _, record in envelopes)
    seen, invalid_current_sources = set(), set()
    for index, record in envelopes:
        identity = (record["source"], record["sequence"])
        try:
            _require(record["source"] not in source_errors,
                     source_errors.get(record["source"], "MACHINE_STATE_SOURCE"),
                     "Producer sequence/timestamp history is inconsistent; its supplied facts are unavailable")
            if identity in seen:
                duplicates.append(index)
                continue
            seen.add(identity)
            data = record["data"]
            if record["kind"] != "sample" or data.get("kind") != "machine_observation":
                unrecognized.append({"record_index": index, "reason": "not_a_bound_machine_observation_sample"})
                continue
            _require(set(data) == {"schema_version", "kind", "configuration_binding", "observations"} and
                     type(data["schema_version"]) is int and data["schema_version"] == 1,
                     "MACHINE_STATE_SCHEMA", "Unknown machine observation schema or fields")
            supplied = data["configuration_binding"]
            _require(binding is not None and type(supplied) is dict and set(supplied) == BINDING_FIELDS and
                     canonical(supplied) == canonical(binding), "MACHINE_STATE_BINDING", "Observation does not exactly match the current validated active configuration")
            _require(timestamp is not None and record["timestamp_ns"] <= timestamp,
                     "MACHINE_STATE_TIME", "Observation lies after the declared evaluation time")
            observations = data["observations"]
            _require(type(observations) is list and 1 <= len(observations) <= 64,
                     "MACHINE_STATE_OBSERVATION", "Expected a bounded nonempty observation list")
            keys = set()
            for observation in observations:
                _observation(observation, definition)
                key = tuple(observation[k] for k in ("domain", "resource", "key", "source"))
                _require(key not in keys, "MACHINE_STATE_DUPLICATE", "Duplicate observation field/source within a sample")
                keys.add(key)
            accepted.append(index)
            for observation_index, observation in enumerate(observations):
                key = tuple(observation[k] for k in ("domain", "resource", "key", "source"))
                candidates.setdefault(key, []).append((record["timestamp_ns"], record["sequence"], record["source"], index, observation_index, observation))
        except ConfigurationError as error:
            rejected.append({"record_index": index, **error.as_dict()})
            # Invalid observations bound to this exact current definition also
            # invalidate older rows from that producer. Old configurations are
            # expected in a recorder and do not taint a newer bound stream.
            data = record["data"]
            if (data.get("kind") == "machine_observation" and binding is not None and
                    type(data.get("configuration_binding")) is dict and
                    canonical(data["configuration_binding"]) == canonical(binding) and
                    error.code not in ("MACHINE_STATE_TIME", "MACHINE_STATE_SEQUENCE")):
                invalid_current_sources.add(record["source"])
    if invalid_current_sources:
        removed = [index for index in accepted + duplicates
                   if record_envelopes[index]["source"] in invalid_current_sources]
        rejected.extend({"record_index": index, "code": "MACHINE_STATE_SOURCE",
                         "message": "Malformed current-bound observations invalidate this producer's supplied facts"}
                        for index in removed)
        accepted = [index for index in accepted if record_envelopes[index]["source"] not in invalid_current_sources]
        duplicates = [index for index in duplicates if record_envelopes[index]["source"] not in invalid_current_sources]
        candidates = {key: [row for row in rows if row[2] not in invalid_current_sources]
                      for key, rows in candidates.items()}
        candidates = {key: rows for key, rows in candidates.items() if rows}
    domains = {name: {"status": "unknown", "facts": [], "counts": {"measured": 0, "commanded": 0, "reported": 0, "unavailable": 0}}
               for name in DOMAINS}
    facts = {}
    for key, choices in sorted(candidates.items()):
        domain, resource, field, source = key
        # A source may publish multiple sequence-valid updates at one timestamp.
        # Its newest sequence wins; separate producers have no authority order.
        producer_latest = {}
        for row in choices:
            previous = producer_latest.get(row[2])
            if previous is None or (row[1], row[0], row[3]) > (previous[1], previous[0], previous[3]):
                producer_latest[row[2]] = row
        latest = list(producer_latest.values())
        available = [row for row in latest if row[5]["valid"] and row[5]["fresh"] and
                     row[5]["age_ms"] + (timestamp-row[0])/1_000_000 <= row[5]["max_age_ms"]]
        ambiguous = len({(row[5]["unit"], row[5]["value"]) for row in available}) > 1
        chosen = max(latest, key=lambda row: (row[0], row[1], row[2], row[3]))
        event_time, _, _, record_index, observation_index, observation = chosen
        age = observation["age_ms"] + (timestamp - event_time) / 1_000_000
        conflict_reason = ("conflicting_same_time_observations" if len({row[0] for row in available}) == 1
                           else "conflicting_fresh_producers")
        reason = (conflict_reason if ambiguous else "invalid" if not observation["valid"] else
                  "producer_marked_stale" if not observation["fresh"] else "stale" if age > observation["max_age_ms"] else None)
        entry = {"status": "unavailable" if reason else "available", "value": None if reason else observation["value"],
                 "unit": observation["unit"], "source": source, "reason": reason, "evaluated_age_ms": age,
                 "max_age_ms": observation["max_age_ms"], "raw_record_index": record_index,
                 "raw_observation_index": observation_index,
                 "producer": record_envelopes[record_index]["source"], "sequence": record_envelopes[record_index]["sequence"],
                 "timestamp_ns": event_time, "raw_record_sha256": digest(record_envelopes[record_index]),
                 "conflicting_record_count": len(available) if ambiguous else 0,
                 "conflicting_record_indexes": [r[3] for r in available][-64:] if ambiguous else [],
                 "producer_count": len(latest)}
        fact = facts.setdefault((domain, resource, field), {"resource": resource, "key": field, "unit": observation["unit"],
                                                          "measured": None, "commanded": None, "reported": None})
        fact[source] = entry
        domains[domain]["counts"]["unavailable" if reason else source] += 1
    for (domain, _, _), fact in sorted(facts.items()):
        domains[domain]["facts"].append(fact)
    for domain in domains.values():
        counts = domain["counts"]
        domain["status"] = ("observed" if counts["measured"] else "reported_only" if counts["reported"] else
                            "commanded_only" if counts["commanded"] else "unknown")
    observed = sum(d["status"] == "observed" for d in domains.values())
    return {"schema_version": 1, "kind": "simulation_machine_state", "configuration_binding": deepcopy(binding),
            "machine_definition": definition, "definition_error": definition_error,
            "declared_target": {"motor_channels": 12, "abz_encoders": 4, "general_di": 24, "general_do": 16,
                                "qualified": False, "observed_presence": False, "basis": "IS-2 design requirements only"},
            "service_topology": {"soldered_regions": {"fpga": "whole_motherboard_exchange", "io": "whole_motherboard_exchange"},
                                 "commodity_modules": {"compute": "unknown", "esp": "unknown", "storage": "unknown"},
                                 "basis": "architecture requirements; no inferred physical presence"},
            "timeline": {"evaluation_timestamp_ns": timestamp,
                         "selection": "explicit" if evaluation_timestamp_ns is not None else "latest_supplied_valid_envelope_timestamp",
                         "basis": "caller_declared_simulation_ns_not_wall_clock", "live_freshness_claim": False},
            "domains": domains, "counts": {"observed_domains": observed, "unknown_domains": len(DOMAINS) - observed,
                                           "accepted_records": len(accepted), "rejected_records": len(rejected),
                                           "unrecognized_records": len(unrecognized), "duplicate_records": len(duplicates)},
            "accepted_record_indexes": accepted[-64:], "rejected_records": rejected[-64:], "unrecognized_records": unrecognized[-64:],
            "duplicate_record_indexes": duplicates[-64:],
            "record_detail_limit": 64,
            "source_consistency": {"quarantined_sources": sorted(set(source_errors) | invalid_current_sources)[:64],
                                   "quarantined_source_count": len(set(source_errors) | invalid_current_sources),
                                   "details_truncated": len(set(source_errors) | invalid_current_sources) > 64,
                                   "policy": "inconsistent sequences/timestamps or malformed current-bound samples cannot refresh older facts; contradictory fresh producers are unavailable"},
            "record_details_truncated": any(len(rows) > 64 for rows in (accepted, rejected, unrecognized, duplicates)),
            "provenance": {"raw_records_embedded": False, "input_record_count": len(record_envelopes),
                           "input_envelopes_sha256": digest(record_envelopes),
                           "reference": "caller_supplied_record_envelopes; report.records when embedded in recorder report",
                           "classification": "supplied_simulation_data_not_authenticated_physical_measurements"},
            **deepcopy(GUARDS)}
