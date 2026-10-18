"""Read-only, hash-labelled whole-motherboard power allocation audit.

These are source inventories and explicit design reservations. They are not
measurements, target timing results, or a regulator stability qualification.
"""
from __future__ import annotations
import collections
import hashlib
import json
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
IO = {"IO_3V3", "MOTOR_IO_3V3"}

def number(value: str, kind: str) -> float:
    match = re.search(r"([\d.]+)\s*([munpkM]?)" + ("F" if kind == "C" else "(?:ohm)?"), value)
    if not match:
        raise ValueError(value)
    return float(match[1]) * {"": 1, "m": 1e-3, "u": 1e-6, "n": 1e-9, "p": 1e-12, "k": 1e3, "M": 1e6}[match[2]]

def run() -> dict:
    src = ROOT / "hardware/motherboard/design.json"
    raw = src.read_bytes()
    design = json.loads(raw)
    components = design["components"]
    capacitors = []
    ic = collections.defaultdict(list)
    io_pin_nets = set()
    for ref, c in components.items():
        nets = set(c.get("pins", {}).values())
        if IO & nets:
            if ref.startswith("C") and "LOGIC_GND" in nets:
                nominal = c.get("capacitance_f", number(c["value"], "C"))
                # The exact fitted MPNS below are all K (10%) MLCCs except C2005
                # M (20%). Preserve explicitly supplied original metadata.
                tolerance = c.get("tolerance", .20 if ref == "C2005" else .10)
                thermal = c.get("temperature_change", .22 if ref == "C2005" else .15)
                capacitors.append({"ref": ref, "mpn": c["mpn"], "source_block": c.get("source_block"),
                    "nominal_f": nominal, "tolerance_fraction": tolerance,
                    "temperature_fraction_screen": thermal,
                    "upper_25c_f": nominal * (1 + tolerance),
                    "upper_before_dc_bias_f": nominal * (1 + tolerance) * (1 + thermal),
                    "dc_bias_minimum_qualified": False})
            if ref.startswith("U"):
                ic[c["mpn"]].append(ref)
            io_pin_nets |= nets
    # Conservative resistive screen: every R to logic ground whose other net
    # touches an IO3 IC, plus direct IO3 pullups. This can count mutually
    # exclusive states and non-output pins. It is deliberately not a graph
    # proof of a realizable maximum operating state.
    resistors = []
    for ref, c in components.items():
        if not ref.startswith("R") or len(c.get("pins", {})) != 2:
            continue
        a, b = c["pins"].values()
        related = (a in IO or b in IO or
                   (a == "LOGIC_GND" and b in io_pin_nets) or
                   (b == "LOGIC_GND" and a in io_pin_nets))
        if not related or (a == b):
            continue
        ohms = c.get("resistance_ohm", c.get("resistance_ohms", None))
        if ohms is None:
            try: ohms = number(c["value"], "R")
            except ValueError: continue
        if not ohms or ohms < 1000:
            # Series termination, mode straps and bleed on other domains are
            # not silently treated as a direct 3.4 V grounded load.
            continue
        resistors.append({"ref": ref, "nets": [a,b], "ohms": ohms,
            "current_screen_a": 3.4 / (ohms * .98)})
    cap_totals = {key: sum(c[key] for c in capacitors) for key in
                  ["nominal_f", "upper_25c_f", "upper_before_dc_bias_f"]}
    pulls = sum(r["current_screen_a"] for r in resistors)
    # Exact table anchors are separated from reservations. The FPGA 0.4 A
    # reservation is inherited FPGA source metadata, not an Efinity estimate.
    allocations = [
        {"function": "FPGA IO/internal/switching allocation", "a": .4, "evidence": "inherited reservation; not target power analysis"},
        {"function": "50 MHz oscillator", "a": .019, "evidence": "Abracon ASE maximum source metadata"},
        {"function": "SPI flash", "a": .025, "evidence": "Winbond maximum program/erase allocation; read-only operation smaller"},
        {"function": "Four AM26LV32E receivers", "a": .068, "evidence": "TI 17 mA/package maximum no external output dynamics"},
        {"function": "Nineteen ISO1212 packages", "a": len(ic.get("ISO1212DBQR", [])) * .0019, "evidence": "TI 1.9 mA/package logic maximum, output loads extra"},
        {"function": "Two ISO7762F core sides", "a": .0188, "evidence": "TI 9.4 mA/package maximum static HIGH at 3.3 V; mixed/dynamic qualification extra"},
        {"function": "Two ISO7720F core sides", "a": .025, "evidence": "allocation covering 100 Mbps same-supply table; actual mixed supply table applicability open"},
        {"function": "Three STM32G031 complete nodes", "a": .050, "evidence": "reservation; TI/ST baseline 3 x 6.9 mA excludes peripherals and IO"},
        {"function": "Other logic/supervisor static allowance", "a": .005, "evidence": "reservation; exact per-MPN static table reconciliation still required"},
        {"function": "Resistive loads conservative graph screen", "a": pulls, "evidence": "not all terms can necessarily occur simultaneously; avoids counting former 0.06 A support again"},
        {"function": "Remaining logic/output/transition dynamics", "a": .100, "evidence": "reservation; no maximum mixed-frequency load proof"},
        {"function": "Forthcoming compute/status/service crossings", "a": .050, "evidence": "reservation; compute/ESP own supplies, logic crossings only"},
    ]
    io_allocation = sum(x["a"] for x in allocations)
    # Full temperature VFB +/-0.9%, ISS 2.3..2.7 uA, CSS 6.8nF +/-5%.
    # K <=700 us is a coarse upper graphical envelope for the whole Fig7-4
    # domain. It deliberately does not interpolate the curve at 6.8 nF.
    tmin_us = 6800 * .95 / 2.7 * (.6 * .991 / .75) - 700
    tmax_us = 6800 * 1.05 / 2.3 * (.6 * 1.009 / .75) + 160
    charge = cap_totals["upper_before_dc_bias_f"] * 3.34125 / (tmin_us * 1e-6)
    # Efficiency is an explicit planning floor, NOT a TI guaranteed minimum.
    efficiency = .85
    io_from_core = io_allocation * 3.34125 / (4.95 * efficiency)
    core_12_from_core = .8 * 1.25 / (4.95 * efficiency)
    core5_normal = 3.0 + .7 + io_from_core + core_12_from_core
    core5_fault_screen = 3.0 + 1.375 + io_from_core + core_12_from_core
    report = {
        "schema_version": 1, "source_path": str(src.relative_to(ROOT)),
        "source_sha256": hashlib.sha256(raw).hexdigest(),
        "physical_footprints_snapshot": design["physical_footprints"],
        "contains_operator": "U14007" in components,
        "contains_power_entry": "U11001" in components,
        "manufacturing_ready": False, "power_qualified": False,
        "cap_inventory": capacitors, "cap_totals": cap_totals,
        "regulator_local_cap_refs": ["C2005", "C2010"],
        "distributed_cap_nominal_f": cap_totals["nominal_f"] - sum(c["nominal_f"] for c in capacitors if c["ref"] in ["C2005", "C2010"]),
        "ic_inventory": dict(ic), "resistive_screen": resistors,
        "io3_allocations": allocations, "io3_total_allocation_a": io_allocation,
        "old_mc_allocation_a": .15,
        "startup_screen": {"css_f": 6.8e-9, "tolerance": .05,
            "k_coarse_graph_envelope_us": 700, "tss_min_us": tmin_us,
            "tss_max_us": tmax_us, "ideal_ramp_capacitive_current_a": charge,
            "steady_allocation_plus_ideal_charge_a": io_allocation+charge,
            "limitations": "K is a graphical bound, ramp derivative/charging peak and concurrent FPGA startup load are not guaranteed by this arithmetic."},
        "core5_budget": {"converter_rating_a": 6, "planning_efficiency_floor": efficiency,
            "normal_before_nvme_display_a": core5_normal,
            "esp_fault_before_nvme_display_a": core5_fault_screen,
            "normal_unallocated_a": 6-core5_normal,
            "esp_fault_unallocated_a": 6-core5_fault_screen,
            "nvme_normal_3v3_equivalent_a": max(0,6-core5_normal)*4.95*efficiency/3.3,
            "limits": "SBC3A is an allocation, not a current limiter. NVMe/display not yet selected; no complete capacity guarantee."},
        "motion5_budget": {"converter_rating_a": 6,
            "motors_normal_a": .8976+.4488,
            "receiving_bleed_a": 2*5.05/(330*.99),
            "operator_ports_normal_a": 1.05,
            "operator_ports_limit_screen_a": 1.493498,
            "operator_quiescent_and_contacts_screen_a": .009,
            "normal_total_a": .8976+.4488+2*5.05/(330*.99)+1.05+.009,
            "limits": "Motor driver actual loaded/dynamic current, startup and line IR drop still require qualification."},
        "esp_drop_screen": {"combined_resistance_ohm": .135+.120,
            "normal_current_a": .7, "normal_header_min_v": 4.95-.7*(.135+.120),
            "fault_current_a": 1.375, "fault_header_min_v": 4.95-1.375*(.135+.120),
            "limits": "LM66100 exact5V/-200mA RON table is used conditionally; devkit LDO/revision/dropout/copper unspecified."},
        "candidate_corrections": [
            "Do not delete required bypass capacitors to make aggregate nominal fit a local Cout rule.",
            "Retain local22.1uF and introduce source-backed >=10mohm distributed damping, verifying physical VOS/local reservoir topology and all alternate copper bypasses.",
            "TPS62902 same-RPJ9 2A can provide startup/current margin but still needs the same damping; actual part/mode/VSET/package/source ledger must be reviewed before substitution.",
            "TPS62132 matrix covers1uH/100 and200uF nominal with +20/-50 effective envelope, but different16pinfootprint/PGshutdown behavior would require more intrusive source and copper changes.",
        ],
        "remaining_engineering_gates": [
            "Exact all-MPN mixed static/dynamic load proof and target FPGA IO power profile; reservations are not electrical maxima.",
            "Effective MLCC minima/maxima under bias, temperature and aging; local Cout must remain at least10uF effective.",
            "Distributed >=10mohm damping actual topology and impedance, local VOS Kelvin point, stability/transient/EMI qualification.",
            "Actual startup load and peak capacitor charging current, load-inhibit sequencing, regulator thermal/layout capacity.",
            "CORE5 total NVMe/display/module-aux allocation, converter/fuse minimum-input/efficiency/thermal coordination.",
            "MOTOR5 20.36mV distribution allowance, AUX5 55.8mV allowance, actual line/noise/current corners.",
            "ESP devkit LDO and full-range series switch resistance/headroom, qualified branch current-limit resistor drift.",
        ],
        "primary_sources": [
            "https://www.ti.com/lit/ds/symlink/tps62901.pdf#page=39",
            "https://www.ti.com/lit/ds/symlink/tps62902.pdf",
            "https://www.ti.com/lit/ds/symlink/tps62132.pdf#page=14",
            "https://www.susumu.co.jp/en/product_detail/?pdid=505",
            "https://www.ti.com/lit/ds/symlink/tps2553.pdf#page=7",
            "https://www.ti.com/lit/ds/symlink/lm66100.pdf#page=5",
        ],
    }
    (OUT/"whole-board-power-audit.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf8")
    return report

if __name__ == "__main__":
    r=run()
    print(json.dumps({k:r[k] for k in ["physical_footprints_snapshot","cap_totals","io3_total_allocation_a","startup_screen","core5_budget","motion5_budget"]},indent=2))
