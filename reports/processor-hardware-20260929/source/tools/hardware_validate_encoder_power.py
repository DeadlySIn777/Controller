"""Independently check the two encoder power branches and their bounded budget."""
from collections import defaultdict
import hashlib
import json
import math
from pathlib import Path
import sys
import xml.etree.ElementTree as ET

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "hardware/encoder_power"


def validate(tree, design, envelope):
    errors = []
    loads = [row for row in design["power_loads"] if row["id"] == "encoder_supply"]
    if len(loads) != 1 or (loads[0]["rail"], loads[0]["budget_a"]) != ("CORE_5V", 0.4):
        errors.append("Frozen ledger normal encoder reservation differs from 0.4 A on CORE_5V")
    for channel in range(2):
        for position, net in ((7, f"ENC{channel}_5V_LIMITED"), (8, "LOGIC_GND")):
            rows = [t for t in design["terminals"] if (t["connector"], t["position"]) == (f"JENC{channel}", position)]
            if len(rows) != 1 or rows[0]["net"] != net:
                errors.append(f"Frozen ledger boundary differs: JENC{channel}.{position}")
    expected = defaultdict(set)
    def connect(net, *nodes):
        expected[net].update((ref, str(pin)) for ref, pin in nodes)
    boundary = {"JIN1": ["CORE_5V", "LOGIC_GND", "IO_3V3"],
                "JOUT1": ["ENC0_5V_LIMITED", "LOGIC_GND", "ENC1_5V_LIMITED", "LOGIC_GND"],
                "JCTRL1": ["ENC0_POWER_EN", "ENC0_POWER_FAULT_N", "LOGIC_GND",
                           "ENC1_POWER_EN", "ENC1_POWER_FAULT_N", "LOGIC_GND"]}
    for ref, nets in boundary.items():
        for pin, net in enumerate(nets, 1):
            connect(net, (ref, pin))
    for channel in range(2):
        u, r, c = f"U{channel+1}", channel*4, channel*4
        output, en, fault, ilim = (f"ENC{channel}_5V_LIMITED", f"ENC{channel}_POWER_EN",
                                   f"ENC{channel}_POWER_FAULT_N", f"ENC{channel}_ILIM")
        # TI Rev. F DBV table, independently transcribed: DRV is different.
        connect("CORE_5V", (u, 1), (f"C{c+1}", 1), (f"C{c+2}", 1))
        connect("LOGIC_GND", (u, 2), (f"R{r+1}", 2), (f"R{r+2}", 2), (f"R{r+4}", 2))
        connect(en, (u, 3), (f"R{r+2}", 1))
        connect(fault, (u, 4), (f"R{r+3}", 2))
        connect(ilim, (u, 5), (f"R{r+1}", 1))
        connect(output, (u, 6), (f"R{r+4}", 1), (f"C{c+3}", 1), (f"C{c+4}", 1))
        connect("IO_3V3", (f"R{r+3}", 1))
        for cap in range(c+1, c+5):
            connect("LOGIC_GND", (f"C{cap}", 2))
    actual, seen = {}, set()
    for net in tree.findall(".//nets/net"):
        name = net.attrib["name"].lstrip("/")
        if name in actual:
            errors.append(f"Duplicate net: {name}")
        nodes = [(n.attrib["ref"], n.attrib["pin"]) for n in net.findall("node")]
        for node in nodes:
            if node in seen:
                errors.append(f"Pin appears more than once: {node}")
            seen.add(node)
        actual[name] = set(nodes)
    for net in sorted(set(actual) | set(expected)):
        if actual.get(net, set()) != expected.get(net, set()):
            errors.append(f"Net {net}: missing={sorted(expected.get(net, set())-actual.get(net, set()))}; unexpected={sorted(actual.get(net, set())-expected.get(net, set()))}")
    elements = tree.findall(".//components/comp")
    components = {c.attrib["ref"]: c for c in elements}
    if len(elements) != len(components) or set(components) != {"U1", "U2", *boundary, *[f"R{i}" for i in range(1, 9)], *[f"C{i}" for i in range(1, 9)]}:
        errors.append("Component population differs from the reviewed two-branch block")
    for ref, comp in components.items():
        value, footprint = comp.findtext("value"), comp.findtext("footprint")
        mpn = comp.findtext("./fields/field[@name='MPN']") or ""
        if any(p.attrib.get("name", "").lower() == "dnp" for p in comp.findall("property")):
            errors.append(f"Required component is marked DNP: {ref}")
        if ref.startswith("U") and (value, footprint, mpn) != ("TPS2553DBVR-1", "Package_TO_SOT_SMD:SOT-23-6", "TPS2553DBVR-1"):
            errors.append(f"Wrong switch or package: {ref}; active-high DBV latch-off part required")
        if ref.startswith("R"):
            index = (int(ref[1:])-1) % 4
            target = ("110k 1% 100ppm", "10k 1%", "10k 1%", "100k 1% 100ppm")[index]
            target_mpn = "CRCW0603110KFKEA" if index == 0 else ""
            if (value, footprint, mpn) != (target, "Resistor_SMD:R_0603_1608Metric", target_mpn):
                errors.append(f"Current-limit/default/fault/bleed resistor changed: {ref}")
        if ref.startswith("C"):
            index = (int(ref[1:])-1) % 4
            target = ("100nF 25V X7R", "10uF 16V X7R", "100nF 25V X7R", "1uF 16V X7R")[index]
            target_fp = "Capacitor_SMD:C_0805_2012Metric" if index == 1 else "Capacitor_SMD:C_0603_1608Metric"
            if (value, footprint, mpn) != (target, target_fp, ""):
                errors.append(f"Supply capacitance or unqualified capacitor MPN changed: {ref}")
    pins = tree.findall(".//libpart[@part='TPS2553DBVR-1']/pins/pin")
    actual_pins = {p.attrib["num"]: (p.attrib["name"], p.attrib["type"]) for p in pins}
    expected_pins = {"1": ("IN", "power_in"), "2": ("GND", "power_in"), "3": ("EN", "input"),
                     "4": ("~{FAULT}", "open_collector"), "5": ("ILIM", "output"), "6": ("OUT", "power_out")}
    if len(pins) != 6 or actual_pins != expected_pins:
        errors.append("Symbol pin names/types differ from the DBV datasheet map")

    def check(section, targets):
        row = envelope if section is None else envelope.get(section, {})
        for key, target in targets.items():
            if row.get(key) != target or (type(target) is bool and type(row.get(key)) is not bool):
                errors.append(f"Unreviewed envelope value: {section or 'root'}.{key}")
    def number(section, key, target):
        value = envelope.get(section, {}).get(key)
        if type(value) not in (int, float) or not math.isfinite(value) or abs(value-target) > 1e-10:
            errors.append(f"Calculation mismatch: {section}.{key}")
    check(None, {"schema_version": 1, "scope": "two encoder branches only", "manufacturing_ready": False,
                 "mpn": "TPS2553DBVR-1", "package": "DBV_SOT23_6", "boundary": boundary,
                 "pins": {"1": "IN", "2": "GND", "3": "EN", "4": "FAULT_N", "5": "ILIM", "6": "OUT"}})
    check("input_v", {"min": 4.75, "nominal": 5.0, "max": 5.25})
    check("logic_io_v", {"min": 0, "max": 3.6, "ground": "LOGIC_GND", "partial_power_qualified": False})
    check("rilim", {"ohms": 110000, "tolerance": 0.01, "tcr_ppm_per_k": 100,
                     "temperature_excursion_k": 150, "mpn_reference": "CRCW0603110KFKEA"})
    rmin, rmax = 110*0.99*0.985, 110*1.01*1.015
    imin, inom, imax = 25230/rmax**1.016/1000, 23950/110**0.977/1000, 22980/rmin**0.94/1000
    number("rilim", "minimum_kohms", rmin)
    number("rilim", "maximum_kohms", rmax)
    for key, value in (("min", imin), ("nominal", inom), ("max", imax)):
        number("calculated_threshold_a", key, value)
    check("budget", {"normal_encoder_load_a_each": 0.2, "ledger_normal_load_a_both": 0.4,
                      "switch_quiescent_a_each_reservation": 0.00014, "full_rail_fault_budget_qualified": False})
    bleed = 5.25/(100000*0.99*0.985)
    for key, value in (("output_bleed_max_a_each", bleed), ("normal_5v_a_both_with_switch_and_bleed", 0.4+2*0.00014+2*bleed),
                       ("simultaneous_limited_fault_a_both", 2*imax), ("fault_a_both_with_switch_reservation", 2*imax+2*0.00014)):
        number("budget", key, value)
    if 0.2+bleed >= imin:
        errors.append("Normal encoder load exceeds minimum limit threshold")
    check("thermal", {"ron_max_ohms_dbv": 0.135, "initial_local_ambient_max_c": 70, "qualified": False})
    for key, value in (("normal_switch_loss_w_each", (0.2+bleed)**2*0.135), ("normal_switch_drop_v_each", (0.2+bleed)*0.135),
                       ("near_short_dissipation_w_each", 5.25*imax)):
        number("thermal", key, value)
    check("behavior", {"enable_default": "10k_pulldown_off_if_upstream_high_z", "fault_active_low": True,
                       "fault_is_power_good": False, "fault_latch_cleared_by": ["enable_toggle", "input_power_cycle"],
                       "thermal_auto_retry_possible": True, "reverse_current_before_turnoff_possible": True,
                       "external_fault_inhibit_implemented": False, "active_output_discharge": False})
    return errors


def main():
    frozen = OUT / "input-electrical-design.json"
    design = json.loads(frozen.read_text(encoding="utf-8"))
    envelope = json.loads((OUT / "design-envelope.json").read_text(encoding="utf-8"))
    tree = ET.parse(OUT / "netlist.xml")
    errors = validate(tree, design, envelope)
    if envelope["source_ledger_sha256"] != hashlib.sha256(frozen.read_bytes()).hexdigest():
        errors.append("Frozen ledger hash differs from the generator input")
    erc = json.loads((OUT / "erc.json").read_text(encoding="utf-8"))
    violations = [v for sheet in erc["sheets"] for v in sheet["violations"]]
    if violations:
        errors.append(f"ERC contains {len(violations)} violations")
    sources = ["tools/hardware_build_tx_schematic.py", "tools/hardware_build_encoder_power.py",
               "tools/hardware_validate_encoder_power.py", "tests/test_encoder_power.py", "reports/ENCODER_POWER.md"]
    sources += [p.relative_to(ROOT).as_posix() for p in sorted(OUT.iterdir()) if p.is_file() and p.name != "validation.json"]
    result = {"schema_version": 1, "scope": "two independently current-limited 5V encoder supplies",
              "consistency_pass": not errors, "manufacturing_ready": False, "errors": errors,
              "switch_count": 2, "component_count": len(tree.findall('.//components/comp')),
              "net_count": len(tree.findall('.//nets/net')), "kicad_version": erc["kicad_version"],
              "erc_violations": len(violations), "erc_ignored_checks": erc["ignored_checks"],
              "source_sha256": {p: hashlib.sha256((ROOT/p).read_bytes()).hexdigest() for p in sources},
              "boundary": "Connectivity/ERC and bounded arithmetic only; no transient, thermal, partial-power, system fault policy or physical qualification"}
    (OUT / "validation.json").write_text(json.dumps(result, indent=2)+"\n", encoding="utf-8")
    print(f"Encoder power: {'PASS' if not errors else 'FAIL'}; {len(errors)} issues; manufacturing blocked")
    for error in errors:
        print(error)
    return bool(errors)


if __name__ == "__main__":
    sys.exit(main())
