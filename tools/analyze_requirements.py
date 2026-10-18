#!/usr/bin/env python3
"""Analyze explicit machine-demand assumptions; no hardware dependencies.

Run from the project root:
    python tools/analyze_requirements.py config/machine-study.json \
        --output reports/timing-budget.json

This calculates demands, not real-time schedulability or a safe stopping system.
"""

from __future__ import annotations

import argparse
import json
import math
from pathlib import Path
import sys
from typing import Any


class InputError(ValueError):
    """A configuration is invalid or its units are unsupported."""


UNITS = {
    "linear_distance": "mm",
    "linear_speed": "mm/min",
    "shaft_speed": "rev/min",
    "pulse_duration": "us",
    "reaction_and_update_time": "ms",
    "linear_acceleration": "mm/s^2",
    "network_capacity": "Mbit/s",
    "data_size": "byte",
}


def object_keys(value: Any, required: set[str], optional: set[str], path: str) -> dict:
    if not isinstance(value, dict):
        raise InputError(f"{path}: expected an object")
    missing, extra = required - value.keys(), value.keys() - required - optional
    if missing:
        raise InputError(f"{path}: missing fields: {', '.join(sorted(missing))}")
    if extra:
        raise InputError(f"{path}: unknown fields: {', '.join(sorted(extra))}")
    return value


def number(value: Any, path: str, *, positive: bool = False, integer: bool = False) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise InputError(f"{path}: expected a finite number, not a boolean or string")
    try:
        finite = math.isfinite(value)
    except OverflowError:
        finite = False
    if not finite or value < 0 or (positive and value == 0):
        raise InputError(f"{path}: expected a finite {'positive' if positive else 'nonnegative'} number")
    if integer and (not isinstance(value, int)):
        raise InputError(f"{path}: expected an integer")
    return value


def label(value: Any, path: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise InputError(f"{path}: expected a nonempty string")
    return value


def sequence(value: Any, path: str, *, allow_empty: bool = False) -> list:
    if not isinstance(value, list) or (not allow_empty and not value):
        raise InputError(f"{path}: expected a {'possibly empty' if allow_empty else 'nonempty'} list")
    return value


def unique_name(name: str, names: set[str], path: str) -> None:
    if name in names:
        raise InputError(f"{path}: duplicate name {name!r}")
    names.add(name)


def limit_result(demand: float, limit: float) -> dict:
    return {
        "demand_hz": demand,
        "assumed_limit_hz": limit,
        "utilization": demand / limit,
        "within_assumed_limit": demand <= limit,
    }


def analyze_encoder(config: dict, shaft_revs_per_second: float, path: str) -> dict:
    object_keys(config, {"signal_definition", "resolution_per_rev"},
                {"assumed_count_rate_limit_hz", "index_pulses_per_rev"}, path)
    definition = config["signal_definition"]
    definitions = {
        "quadrature_lines_per_rev": 4,
        "decoded_counts_per_rev": 1,
        "single_channel_rising_pulses_per_rev": 1,
    }
    if not isinstance(definition, str) or definition not in definitions:
        raise InputError(f"{path}.signal_definition: choose one of {', '.join(definitions)}")
    resolution = number(config["resolution_per_rev"], f"{path}.resolution_per_rev", positive=True, integer=True)
    counts_per_rev = resolution * definitions[definition]
    count_rate = counts_per_rev * shaft_revs_per_second
    result = {
        "signal_definition": definition,
        "resolution_per_rev": resolution,
        "shaft_revs_per_second": shaft_revs_per_second,
        "decoded_counts_or_rising_pulses_per_rev": counts_per_rev,
        "decoded_count_or_rising_pulse_rate_hz": count_rate,
        "quadrature_channel_cycle_rate_hz": resolution * shaft_revs_per_second
        if definition == "quadrature_lines_per_rev" else None,
    }
    if "index_pulses_per_rev" in config:
        index = number(config["index_pulses_per_rev"], f"{path}.index_pulses_per_rev", integer=True)
        result["index_rising_pulse_rate_hz"] = index * shaft_revs_per_second
    if "assumed_count_rate_limit_hz" in config:
        limit = number(config["assumed_count_rate_limit_hz"], f"{path}.assumed_count_rate_limit_hz", positive=True)
        result["count_rate_limit_check"] = limit_result(count_rate, limit)
    return result


def analyze_joint(config: dict, path: str) -> dict:
    common = {"name", "kind", "drive_input_pulses_per_motor_rev", "motor_revs_per_output_rev",
              "minimum_pulse_high_us", "minimum_pulse_low_us"}
    object_keys(config, common, {"output_mm_per_rev", "maximum_speed_mm_min", "maximum_output_speed_rpm",
                               "encoder", "encoder_shaft", "assumed_output_rate_limit_hz"}, path)
    name = label(config["name"], f"{path}.name")
    kind = config["kind"]
    ratio = number(config["motor_revs_per_output_rev"], f"{path}.motor_revs_per_output_rev", positive=True)
    pulses = number(config["drive_input_pulses_per_motor_rev"], f"{path}.drive_input_pulses_per_motor_rev", positive=True, integer=True)
    high = number(config["minimum_pulse_high_us"], f"{path}.minimum_pulse_high_us", positive=True)
    low = number(config["minimum_pulse_low_us"], f"{path}.minimum_pulse_low_us", positive=True)
    if kind == "linear":
        if "output_mm_per_rev" not in config or "maximum_speed_mm_min" not in config or "maximum_output_speed_rpm" in config:
            raise InputError(f"{path}: linear joint requires output_mm_per_rev and maximum_speed_mm_min, and forbids maximum_output_speed_rpm")
        lead = number(config["output_mm_per_rev"], f"{path}.output_mm_per_rev", positive=True)
        speed = number(config["maximum_speed_mm_min"], f"{path}.maximum_speed_mm_min")
        output_rps = speed / 60 / lead
        scale = {"command_pulses_per_mm": pulses * ratio / lead, "maximum_speed_mm_min": speed}
    elif kind == "rotary":
        if "maximum_output_speed_rpm" not in config or "output_mm_per_rev" in config or "maximum_speed_mm_min" in config:
            raise InputError(f"{path}: rotary joint requires maximum_output_speed_rpm and forbids linear speed/lead")
        speed = number(config["maximum_output_speed_rpm"], f"{path}.maximum_output_speed_rpm")
        output_rps = speed / 60
        scale = {"command_pulses_per_output_rev": pulses * ratio, "maximum_output_speed_rpm": speed}
    else:
        raise InputError(f"{path}.kind: expected linear or rotary")
    motor_rps = output_rps * ratio
    step_rate = motor_rps * pulses
    pulse_limit = 1_000_000 / (high + low)
    result = {
        "name": name, "kind": kind, **scale,
        "output_revs_per_second": output_rps,
        "motor_revs_per_second": motor_rps,
        "required_step_pulses_per_second": step_rate,
        "required_step_pin_transitions_per_second": 2 * step_rate,
        "step_period_us_at_maximum_speed": 1_000_000 / step_rate if step_rate else None,
        "pulse_width_limit_check": limit_result(step_rate, pulse_limit),
    }
    if "assumed_output_rate_limit_hz" in config:
        limit = number(config["assumed_output_rate_limit_hz"], f"{path}.assumed_output_rate_limit_hz", positive=True)
        result["output_rate_limit_check"] = limit_result(step_rate, limit)
    if ("encoder" in config) != ("encoder_shaft" in config):
        raise InputError(f"{path}: encoder and encoder_shaft must be provided together")
    if "encoder" in config:
        shaft = config["encoder_shaft"]
        if shaft not in ("motor", "output"):
            raise InputError(f"{path}.encoder_shaft: expected motor or output")
        result["encoder"] = analyze_encoder(config["encoder"], motor_rps if shaft == "motor" else output_rps, f"{path}.encoder")
        result["encoder"]["shaft"] = shaft
    return result


def analyze_network(config: dict, path: str) -> dict:
    object_keys(config, {"link_capacity_mbit_s", "capacity_mode", "overhead_bytes", "ip_mtu_bytes", "streams"}, set(), path)
    capacity = number(config["link_capacity_mbit_s"], f"{path}.link_capacity_mbit_s", positive=True) * 1_000_000
    mode = config["capacity_mode"]
    if mode not in ("full_duplex", "shared"):
        raise InputError(f"{path}.capacity_mode: expected full_duplex or shared")
    overhead = object_keys(config["overhead_bytes"],
                           {"ethernet_header", "ethernet_fcs", "preamble_and_sfd", "interpacket_gap", "ip_header", "transport_header", "minimum_ethernet_payload"}, set(), f"{path}.overhead_bytes")
    for name, value in overhead.items():
        number(value, f"{path}.overhead_bytes.{name}", integer=True)
    mtu = number(config["ip_mtu_bytes"], f"{path}.ip_mtu_bytes", positive=True, integer=True)
    if overhead["ip_header"] + overhead["transport_header"] > mtu:
        raise InputError(f"{path}: IP and transport headers exceed assumed IP MTU")
    directions = {"host_to_controller": 0.0, "controller_to_host": 0.0}
    streams, names = [], set()
    for index, stream in enumerate(sequence(config["streams"], f"{path}.streams")):
        spath = f"{path}.streams[{index}]"
        object_keys(stream, {"name", "direction", "payload_bytes_per_packet", "packets_per_update", "update_period_ms"}, set(), spath)
        name = label(stream["name"], f"{spath}.name")
        unique_name(name, names, spath)
        direction = stream["direction"]
        if not isinstance(direction, str) or direction not in directions:
            raise InputError(f"{spath}.direction: expected host_to_controller or controller_to_host")
        payload = number(stream["payload_bytes_per_packet"], f"{spath}.payload_bytes_per_packet", integer=True)
        packets = number(stream["packets_per_update"], f"{spath}.packets_per_update", positive=True, integer=True)
        period = number(stream["update_period_ms"], f"{spath}.update_period_ms", positive=True)
        ip_bytes = payload + overhead["ip_header"] + overhead["transport_header"]
        if ip_bytes > mtu:
            raise InputError(f"{spath}: modeled IP packet exceeds assumed MTU; fragmentation is not modeled")
        padded_payload = max(ip_bytes, overhead["minimum_ethernet_payload"])
        wire_bytes = padded_payload + sum(overhead[k] for k in ("ethernet_header", "ethernet_fcs", "preamble_and_sfd", "interpacket_gap"))
        packet_rate = packets * 1_000 / period
        wire_bits_per_s = wire_bytes * 8 * packet_rate
        directions[direction] += wire_bits_per_s
        streams.append({
            "name": name, "direction": direction, "update_hz": 1_000 / period,
            "packets_per_second": packet_rate,
            "application_payload_bytes_per_packet": payload,
            "modeled_wire_slot_bytes_per_packet": wire_bytes,
            "payload_bits_per_second": payload * 8 * packet_rate,
            "wire_slot_bits_per_second": wire_bits_per_s,
            "serialization_and_gap_us_per_packet": wire_bytes * 8 / capacity * 1_000_000,
            "serialization_and_gap_us_per_update": wire_bytes * packets * 8 / capacity * 1_000_000,
        })
    aggregate = sum(directions.values())
    constrained_demand = max(directions.values()) if mode == "full_duplex" else aggregate
    return {
        "capacity_mode": mode, "assumed_link_capacity_bits_per_second": capacity,
        "assumed_overhead_bytes": overhead, "assumed_ip_mtu_bytes": mtu,
        "streams": streams, "wire_slot_bits_per_second_by_direction": directions,
        "aggregate_wire_slot_bits_per_second_both_directions": aggregate,
        "capacity_utilization": constrained_demand / capacity,
        "within_assumed_capacity": constrained_demand <= capacity,
        "deadline_guaranteed": False,
        "excluded": ["OS scheduling", "queueing", "switch delay", "jitter", "retries", "packet loss", "clock drift", "other traffic", "wireless contention", "USB transport overhead"],
    }


def analyze_stopping(config: dict, path: str) -> dict:
    object_keys(config, {"name", "speed_mm_min", "assumed_reaction_time_ms", "assumed_constant_deceleration_mm_s2"}, set(), path)
    name = label(config["name"], f"{path}.name")
    speed = number(config["speed_mm_min"], f"{path}.speed_mm_min") / 60
    reaction = number(config["assumed_reaction_time_ms"], f"{path}.assumed_reaction_time_ms") / 1_000
    deceleration = number(config["assumed_constant_deceleration_mm_s2"], f"{path}.assumed_constant_deceleration_mm_s2", positive=True)
    reaction_distance = speed * reaction
    braking_distance = speed * speed / (2 * deceleration)
    return {
        "name": name, "initial_speed_mm_s": speed, "assumed_reaction_time_s": reaction,
        "assumed_constant_deceleration_mm_s2": deceleration,
        "ideal_reaction_distance_mm": reaction_distance,
        "ideal_braking_distance_mm": braking_distance,
        "ideal_total_distance_mm": reaction_distance + braking_distance,
        "ideal_braking_time_s": speed / deceleration,
        "ideal_reaction_plus_braking_time_s": reaction + speed / deceleration,
        "safety_validated": False,
    }


def finite_tree(value: Any, path: str = "analysis") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            finite_tree(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            finite_tree(child, f"{path}[{index}]")
    elif isinstance(value, (int, float)) and not isinstance(value, bool):
        try:
            finite = math.isfinite(value)
        except OverflowError:
            finite = False
        if not finite:
            raise InputError(f"{path}: derived value is outside finite numeric range")


def analyze(config: dict) -> dict:
    object_keys(config, {"schema_version", "requirements_status", "units", "assumptions", "scenarios"}, set(), "study")
    number(config["schema_version"], "study.schema_version", positive=True, integer=True)
    if config["schema_version"] != 1:
        raise InputError("study.schema_version: only version 1 is supported")
    if config["requirements_status"] not in ("illustrative_unconfirmed", "user_confirmed"):
        raise InputError("study.requirements_status: expected illustrative_unconfirmed or user_confirmed")
    if config["units"] != UNITS:
        raise InputError(f"study.units: expected exactly {json.dumps(UNITS, sort_keys=True)}; conversions are not implicit")
    assumptions = sequence(config["assumptions"], "study.assumptions")
    for index, assumption in enumerate(assumptions):
        label(assumption, f"study.assumptions[{index}]")
    scenarios, names = [], set()
    for index, scenario in enumerate(sequence(config["scenarios"], "study.scenarios")):
        path = f"study.scenarios[{index}]"
        object_keys(scenario, {"name", "description", "joints", "network", "stopping_examples"},
                    {"spindle_encoders", "assumed_aggregate_step_pulses_per_second_limit"}, path)
        name = label(scenario["name"], f"{path}.name")
        unique_name(name, names, path)
        joints, joint_names, violations = [], set(), []
        for jindex, joint in enumerate(sequence(scenario["joints"], f"{path}.joints")):
            result = analyze_joint(joint, f"{path}.joints[{jindex}]")
            unique_name(result["name"], joint_names, path)
            joints.append(result)
            for check in ("pulse_width_limit_check", "output_rate_limit_check"):
                if check in result and not result[check]["within_assumed_limit"]:
                    violations.append(f"joint {result['name']}: {check}")
            encoder_check = result.get("encoder", {}).get("count_rate_limit_check")
            if encoder_check and not encoder_check["within_assumed_limit"]:
                violations.append(f"joint {result['name']}: encoder count rate")
        aggregate = sum(j["required_step_pulses_per_second"] for j in joints)
        result = {
            "name": name, "description": label(scenario["description"], f"{path}.description"),
            "joints": joints,
            "aggregate_step_pulses_per_second_at_simultaneous_joint_maxima": aggregate,
            "aggregate_step_pin_transitions_per_second_at_simultaneous_joint_maxima": 2 * aggregate,
            "largest_single_joint_step_pulses_per_second": max(j["required_step_pulses_per_second"] for j in joints),
            "network": analyze_network(scenario["network"], f"{path}.network"),
            "stopping_examples": [], "spindle_encoders": [],
        }
        if "assumed_aggregate_step_pulses_per_second_limit" in scenario:
            limit = number(scenario["assumed_aggregate_step_pulses_per_second_limit"], f"{path}.assumed_aggregate_step_pulses_per_second_limit", positive=True)
            result["aggregate_step_rate_limit_check"] = limit_result(aggregate, limit)
            if aggregate > limit:
                violations.append("aggregate joint step pulse rate")
        if not result["network"]["within_assumed_capacity"]:
            violations.append("network modeled link capacity")
        spindle_names = set()
        for sindex, spindle in enumerate(sequence(scenario.get("spindle_encoders", []), f"{path}.spindle_encoders", allow_empty=True)):
            spath = f"{path}.spindle_encoders[{sindex}]"
            object_keys(spindle, {"name", "maximum_speed_rpm", "encoder"}, set(), spath)
            spindle_name = label(spindle["name"], f"{spath}.name")
            unique_name(spindle_name, spindle_names, spath)
            speed = number(spindle["maximum_speed_rpm"], f"{spath}.maximum_speed_rpm")
            encoder = analyze_encoder(spindle["encoder"], speed / 60, f"{spath}.encoder")
            result["spindle_encoders"].append({"name": spindle_name, **encoder})
            if "count_rate_limit_check" in encoder and not encoder["count_rate_limit_check"]["within_assumed_limit"]:
                violations.append(f"spindle {spindle_name}: encoder count rate")
        stop_names = set()
        for sindex, stop in enumerate(sequence(scenario["stopping_examples"], f"{path}.stopping_examples", allow_empty=True)):
            stopping = analyze_stopping(stop, f"{path}.stopping_examples[{sindex}]")
            unique_name(stopping["name"], stop_names, path)
            result["stopping_examples"].append(stopping)
        result["assumed_limit_violations"] = violations
        result["within_all_configured_assumed_limits"] = not violations
        scenarios.append(result)
    report = {
        "schema_version": 1, "requirements_status": config["requirements_status"],
        "assumptions": assumptions,
        "scope": "Analytical demand estimates only; neither hardware validation, schedulability proof nor safety certification.",
        "scenarios": scenarios,
        "all_scenarios_within_configured_assumed_limits": all(s["within_all_configured_assumed_limits"] for s in scenarios),
    }
    finite_tree(report)
    return report


def reject_duplicate_keys(pairs: list[tuple[str, Any]]) -> dict:
    result = {}
    for key, value in pairs:
        if key in result:
            raise InputError(f"duplicate JSON field: {key}")
        result[key] = value
    return result


def reject_constant(value: str) -> None:
    raise InputError(f"non-finite JSON constant is unsupported: {value}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", nargs="?", type=Path, default=Path("config/machine-study.json"))
    parser.add_argument("--output", type=Path, help="Also write the JSON report to this file")
    parser.add_argument("--fail-on-limit", action="store_true", help="Exit 1 if a configured assumed limit is exceeded")
    args = parser.parse_args(argv)
    try:
        config = json.loads(args.config.read_text(encoding="utf-8-sig"), object_pairs_hook=reject_duplicate_keys, parse_constant=reject_constant)
        report = analyze(config)
        rendered = json.dumps(report, indent=2, allow_nan=False) + "\n"
        if args.output:
            if args.output.resolve() == args.config.resolve():
                raise InputError("output must not overwrite the input configuration")
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(rendered, encoding="utf-8")
        sys.stdout.write(rendered)
        return 1 if args.fail_on_limit and not report["all_scenarios_within_configured_assumed_limits"] else 0
    except (InputError, OSError, ValueError, OverflowError, ZeroDivisionError) as exc:
        print(f"Input error: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
