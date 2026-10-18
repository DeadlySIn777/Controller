"""Independent, bounded receiving-CLR topology review; no physical guarantee."""
from __future__ import annotations
import copy
import xml.etree.ElementTree as ET
from hardware_apply_motor_feed_reset import REFS, added_components, feed_reset_screen

def native_nodes(path):
    root = ET.parse(path)
    return {(node.get("ref"), node.get("pin")): net.get("name")
            for net in root.findall(".//nets/net") for node in net.findall("node")}

def validate_native_functions(path):
    root = ET.parse(path)
    expected = {
        "FEED_POR": {"1": "RESET_N", "2": "GND", "3": "MR_N", "4": "CT", "5": "SENSE", "6": "VDD"},
        "FEED_SCHMITT": {"1": "NC", "2": "A", "3": "GND", "4": "Y", "5": "VCC"},
    }
    errors = []
    for part, pins in expected.items():
        matches = root.findall('.//libparts/libpart[@lib="CNC_MB_FeedReset"][@part="' + part + '"]')
        if len(matches) != 1 or {p.get("num"): p.get("name") for p in matches[0].findall("pins/pin")} != pins:
            errors.append("Manufacturer native function map differs " + part)
    return dict(consistency_pass=not errors, errors=errors)

def validate(model, baseline, nodes=None, baseline_nodes=None):
    errors = []
    before, after = baseline["components"], model["components"]
    extra = added_components()
    if set(after) - set(before) != set(extra):
        errors.append("Exact ten additive references required")
    if set(before) - set(after):
        errors.append("Existing components removed")
    for ref, part in before.items():
        expected = copy.deepcopy(part)
        for bank, refs in REFS.items():
            if ref == refs["latch"]:
                expected["pins"]["6"] = "MOTOR_FEED_CLEAR_FAST_N_" + bank
            if ref == refs["source"]:
                expected.update(mpn="CRCW060312K1FKEA", value="12.1k 1%",
                                resistance_ohm=12100, inherited_mpn="CRCW06031K00FKEA",
                                component_substitution="MB-MOTOR-FEED-POR-001")
        if after.get(ref) != expected:
            errors.append("Unreviewed existing component delta " + ref)
    for ref, expected in extra.items():
        if after.get(ref) != expected:
            errors.append("Wrong new power/reset/default circuit " + ref)
    if nodes is not None:
        for bank, refs in REFS.items():
            expected = "/motherboard_power_entry/MOTOR_FEED_CLEAR_FAST_N_" + bank
            if nodes.get((refs["latch"], "6")) != expected:
                errors.append("Native latch reset incorrect " + bank)
        for ref, part in extra.items():
            for pin, net in part["pins"].items():
                expected = None if net is None else "/LOGIC_GND" if net == "LOGIC_GND" else "/motherboard_power_entry/" + net
                actual = nodes.get((ref, pin))
                nc_ok = net is None and (actual is None or
                    (actual.startswith("unconnected-(") and
                     sum(v == actual for v in nodes.values()) == 1))
                if not nc_ok and actual != expected:
                    errors.append("Native new endpoint incorrect " + ref + "." + pin)
        if baseline_nodes is not None:
            allowed = {(refs["latch"], "6") for refs in REFS.values()}
            if any(nodes.get(pin) != net for pin, net in baseline_nodes.items() if pin not in allowed):
                errors.append("Native independent final inhibit or other old endpoint changed")
    screen = feed_reset_screen()
    if screen["healthy_old_CLR_node_screen_v"] <= screen["highest_schmitt_VTplus_discrete_screen_v"]:
        errors.append("Insufficient static healthy Schmitt threshold screen")
    if screen["off_node_screen_v"] >= screen["lowest_steady_schmitt_VTminus_discrete_screen_v"]:
        errors.append("Unsafe contact-open LOW screen")
    if screen["reset_max_positive_release_threshold_screen_v"] >= 4.95:
        errors.append("Supervisor cannot release at receiving-RAW minimum")
    return dict(consistency_pass=not errors, errors=errors, screen=screen,
                actual_loaded_ramp_and_output_slew_qualified=False)

def stable_rail_latch(previous_q, raw_qualified, supervisor_released,
                      core_contact_closed, field_contact_closed,
                      new_rearm_rising_edge):
    """Actual DFF truth at valid rails, distinct from below-rated power-up."""
    clear_n = bool(raw_qualified and supervisor_released and core_contact_closed
                   and field_contact_closed)
    return False if not clear_n else True if new_rearm_rising_edge else previous_q
