"""Reproducible, disconnected power-design screens; no circuit mutation.

Every conversion efficiency, unsourced current allocation and L/ESR/capacity
screen is explicitly identified. These calculations are not physical evidence.
"""
from __future__ import annotations

import hashlib
import json
import math
from collections import defaultdict
from pathlib import Path
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
INPUTS = HERE / "source-inputs"


def load(relative):
    return json.loads((INPUTS / relative).read_text(encoding="utf-8"))


def verify_inputs():
    records = json.loads((HERE / "input-hashes.json").read_text())
    for name, record in records.items():
        raw = (INPUTS / name).read_bytes()
        assert hashlib.sha256(raw).hexdigest() == record["sha256"], name
        assert len(raw) == record["bytes"], name
    return len(records)


def rail_inventory():
    tree = ET.parse(INPUTS / "hardware/motherboard/netlist.xml").getroot()
    parts = {(p.get("lib"), p.get("part")): {
        pin.get("num"): pin.attrib for pin in p.findall("pins/pin")
    } for p in tree.findall("libparts/libpart")}
    comps = {c.get("ref"): c for c in tree.findall("components/comp")}
    rows = defaultdict(list)
    selected = {"IO_3V3", "CORE_5V", "SBC_5V", "CORE_1V2", "CM_AUX_3V3"}
    for net in tree.findall("nets/net"):
        if net.get("name").split("/")[-1] not in selected:
            continue
        for node in net.findall("node"):
            ref, num = node.get("ref"), node.get("pin")
            if not ref.startswith("U"):
                continue
            comp = comps[ref]
            lib = comp.find("libsource")
            pin = parts[(lib.get("lib"), lib.get("part"))][num]
            name = pin["name"]
            if pin["type"] not in {"power_in", "power_out"} and not any(
                t in name.upper() for t in ("VCC", "VIN", "VDD", "BIAS")
            ):
                continue
            rows[net.get("name")].append({
                "ref": ref, "pin": num, "function": name,
                "value": comp.findtext("value"), "electrical_type": pin["type"],
                "current_max_proven_by_inventory": False,
            })
    return dict(rows)


def rail_screen(io3_a):
    # Allocations: distinct from a full-temperature part maximum or target power
    # report. CM5 external AUX explicitly excluded from the Pi consumption table.
    eta_aux = eta_io3 = eta_core12 = .85
    aux_normal = .250 + .037  # SD branch / non-SD AUX reservation respectively
    aux_5_equiv = aux_normal * 3.465 / (4.75 * eta_aux)
    sbc = 2.5 + aux_5_equiv + .350 + .05505
    upstream_io = io3_a * 3.465 / (4.95 * eta_io3)
    upstream_core12 = .8 * 1.25 / (4.95 * eta_core12)
    total = sbc + upstream_io + upstream_core12 + .7 + .55 + .341 + .010
    return {
        "IO3_supported_normal_allocation_a": io3_a,
        "CM5_design_allowance_a": 2.5,
        "SD_normal_branch_allocation_a": .250,
        "qualified_SD_part_selected": False,
        "AUX_nonSD_reservation_a": .037,
        "CM_AUX_normal_allocation_a": aux_normal,
        "CM_AUX_5V_equivalent_screen_a": aux_5_equiv,
        "USB_normal_bank_allocation_a": .350,
        "USB_external_allocation_after_bleed_a": .345,
        "USB_allocation_enforcement_implemented": False,
        "HDMI_normal_source_a": .05505,
        "HDMI_running_IC_quiescent_maximum_proven": False,
        "SBC_normal_screen_a": sbc,
        "IO3_CORE5_conversion_screen_a": upstream_io,
        "CORE1V2_allocation_a": .8,
        "CORE1V2_CORE5_conversion_screen_a": upstream_core12,
        "FPGA_target_power_proven": False,
        "ESP_normal_allocation_a": .7,
        "status_normal_planning_allocation_a": .55,
        "status_guaranteed_complete_maximum": False,
        "loaded_RS485_CAN_source_table_screen_a": .341,
        "other_CORE5_reservation_a": .010,
        "CORE5_total_normal_screen_a": total,
        "original_6A_margin_a": 6.0-total,
        "candidate_7A_margin_a": 7.0-total,
        "conversion_efficiency_floor_assumed": .85,
        "conversion_efficiency_floor_guaranteed": False,
        "complete_normal_budget_qualified": False,
    }


def converter_screen(load, bulk_count, vin):
    # Inherited explicit screening assumptions, not Coilcraft hot guarantees.
    lmin, lmax, fmin = 2.632e-6, 5.64e-6, 398e3
    vout = 5.05
    ripple_lmin = vout * (1-vout/vin)/(lmin*fmin)
    ripple_lmax = vout * (1-vout/vin)/(lmax*fmin)
    capmin = bulk_count * 330e-6 * .8 * .8 + 3 * 20.5e-6
    capmax = bulk_count * 330e-6 * 1.2 * 1.2 + 3 * 47e-6 * 1.2
    esr = 2 * .0065/bulk_count + .0006666666666666666
    peak = load + ripple_lmax/2
    # Correlated maximum-L ripple at unload; also retain noncorrelated stronger
    # corner for an intentionally conservative comparison.
    energy_voltage = math.sqrt(vout*vout + lmax*peak*peak/capmin)
    release = energy_voltage + peak*esr
    stronger_peak = load+ripple_lmin/2
    stronger_release = math.sqrt(vout*vout+lmax*stronger_peak**2/capmin)+stronger_peak*esr
    rc = 9530.0
    fc = rc / (2*math.pi*(5/.8)*(.005*10/.0012)*capmin)
    zero = 1/(2*math.pi*rc*22e-9)
    pole = 1/(2*math.pi*rc*(330e-12+38e-12))
    esrzero = 1/(2*math.pi*capmin*esr)
    minlimit = .050/(.005*1.02)
    maxlimit = .062/(.005*.98)
    typical_delay_extra = vin*75e-9/lmin
    return {
        "load_a": load, "protected_VIN_screen_v": vin,
        "bulk330_count": bulk_count,
        "bulk_MPN": "16SVPG330M",
        "screen_Cout_min_f": capmin, "screen_Cout_max_f": capmax,
        "screen_ESR_ohm": esr,
        "minimum_L_assumed_h": lmin, "maximum_L_assumed_h": lmax,
        "frequency_min_assumed_hz": fmin,
        "ripple_with_Lmin_a_pp": ripple_lmin,
        "normal_peak_with_Lmin_a": stronger_peak,
        "limit_min_screen_a": minlimit,
        "limit_max_before_delay_screen_a": maxlimit,
        "current_limit_min_margin_a": minlimit-stronger_peak,
        "short_peak_75ns_typical_delay_screen_a": maxlimit+typical_delay_extra,
        "delay_maximum_guaranteed": False,
        "phase_correlated_unload_peak_a": peak,
        "phase_correlated_unload_voltage_screen_v": release,
        "noncorrelated_conservative_unload_screen_v": stronger_release,
        "target_ceiling_v": 5.15,
        "compensation_nominal_crossover_at_Cmin_hz": fc,
        "compensation_zero_hz": zero,
        "compensation_high_pole_including_38pF_hz": pole,
        "screen_ESR_zero_hz": esrzero,
        "compensation_proven_stable": False,
        "transient_proven": False,
        "engineering_screen_only": True,
    }


def run():
    count = verify_inputs()
    compute = load("hardware/motherboard_compute/design.json")
    parent = load("hardware/motherboard/design.json")
    assert compute["components"]["J15001"]["mpn"] == "10164227-1001A1RLF"
    assert compute["components"]["U15012"]["pins"]["1"] == "CM_AUX_3V3"
    source = load("hardware/motherboard_power_entry/design.json")
    assert source["components"]["U11007"]["mpn"] == "LM70660RRXR"
    assert source["components"]["R11022"]["resistance_ohm"] == .006
    cases = [rail_screen(1.2), rail_screen(2.0)]
    aux_fault = .447*3.465/(4.75*.85)
    fault = 2.5 + aux_fault + .491222463889 + .210
    # Input budget includes independently CORE24-fed analog converters; they
    # must not also appear inside CORE5. MOTION5 is a separate output converter.
    motion = .8976+.4488+2*5.05/(330*.99)+1.05+.009
    core5 = cases[1]["CORE5_total_normal_screen_a"]
    # Actual current source has four1W TMR1 plus one3.5W RECOM directly on C24.
    # Replacement parts must preserve the supported load, not silently turn
    # their larger nameplate into a new load promise.
    isolated_output_capacity = 4*1.0+3.5
    input_power = (core5+motion)*5.05/.85+isolated_output_capacity/.80
    efuse_rtol=.01+.015  # inherited 1%,100ppm over150K additive screen
    ilim_low=4.185/(1+efuse_rtol)
    required_efficiency = (core5+motion)*5.05/(17.7*ilim_low-isolated_output_capacity/.8)
    report = {
        "schema_version": 1,
        "status": "bounded_source_correction_required_not_physical_qualification",
        "source_input_hashes_verified": count,
        "parent_source_footprints_at_snapshot": parent["physical_footprints"],
        "parent_includes_status290": "U17001" in parent["components"],
        "standalone_status290_reviewed_separately": True,
        "compute_physical_parts": compute["physical_component_count"],
        "source_mutation_performed": False,
        "manufacturing_ready": False,
        "power_qualified": False,
        "normal_cases": cases,
        "fault_only_SBC_screen": {
            "AUX_fault_reservation_a": .447,
            "AUX_5V_equivalent_with_assumed_efficiency_a": aux_fault,
            "USB_hardware_ILIM_max_a": .491222463889,
            "HDMI_fault_reservation_a": .210,
            "SBC_all_short_screen_a": fault,
            "simultaneous_fault_operation_required": False,
            "correct_response": "Trip/inhibit safely; prove absolute, transient, thermal and restart behavior. Do not promise continuous all-fault running.",
        },
        "CORE5_source_correction_candidate": {
            "regulator_ref": "U11007", "old_MPN": "LM70660RRXR",
            "new_MPN": "LM706A0RRXR", "same_pinout": True,
            "silicon_recommended_max_a": 10,
            "continuous_board_design_target_a": 7,
            "full_10A_board_capability_claim": False,
            "shunt_ref": "R11022", "new_resistance_ohm": .005,
            "exact_new_shunt_MPN_qualified": False,
            "inductor_ref": "L11001", "new_MPN_candidate": "XAL1010-472MED",
            "inductor_new_footprint_required": True,
            "new_bulk_quantity": 1, "new_bulk_MPN": "16SVPG330M",
            "MOTION5_converter_changed": False,
            "scope": "Only existing CORE converter capacity/support correction; no new architecture or optional features.",
            "not_yet_adopted": True,
        },
        "converter_screens": [converter_screen(a,n,v) for a in (7,8,10)
            for n in (3,4) for v in (30,60)],
        "shared_CORE24_input_normal_screen": {
            "motion5_existing_normal_screen_a": motion,
            "CORE5_profile_screen_a": core5,
            "AI_AO_independent_isolated_output_capacity_sum_w": isolated_output_capacity,
            "actual_source_converters": {
                "U14601": "TMR1-2412", "U14619": "TMR1-2412",
                "U14701": "TMR1-2411", "U14702": "TMR1-2413",
                "U14703": "REC3.5-2424SRW/R8/A",
            },
            "isolated_efficiency_floor_assumed": .80,
            "buck_efficiency_floor_assumed": .85,
            "protected_input_power_screen_w": input_power,
            "entry_testpoint_ILIM_min_a": 4.185,
            "entry_ILIM_with_unproven_inverse_R_corner_screen_a": ilim_low,
            "entry_R_total_drift_screen_fraction": efuse_rtol,
            "protected_input_v_after_assumed_drop": 17.7,
            "normal_input_current_screen_a": input_power/17.7,
            "entry_current_margin_screen_a": ilim_low-input_power/17.7,
            "minimum_combined_buck_efficiency_for_this_screen": required_efficiency,
            "efficiency_or_R_transfer_guaranteed": False,
            "18V_analog_input_requirement_closed": False,
            "source_foldback_fuse_TVS_thermal_qualified": False,
        },
        "native_rail_supply_pin_inventory": rail_inventory(),
        "boot_transition_policy": {
            "module_hot_swap_supported": False,
            "cold_start_staged_loads": "CORE5 ramp with compute/logic delayed; logic then SBC release; field permission remains inhibited.",
            "CORE5_bulk_with_candidate_4parts_max_f": converter_screen(7,4,30)["screen_Cout_max_f"],
            "CORE5_bulk_ideal_charge_at1p9ms_a": converter_screen(7,4,30)["screen_Cout_max_f"]*5.05/.0019,
            "literal_ramp_peak_guaranteed": False,
            "actual_new_distributed_cap_inventory_and_partial_reset_overlap_required": True,
            "SBC_CT_effective_cap_rise_time_proven": False,
            "USB_service_role_changed_only_when_cold": True,
        },
        "remaining_engineering_gates": [
            "IO3 actual mixed static/dynamic aggregate, target FPGA power, clocks/loads and startup: 2A is a source envelope, not proof all consumers fit.",
            "Status full-temperature ICC/TTL transition current maximum absent; .55A is a planning allocation requiring an enforceable/validated operating profile.",
            "Qualified ordinary SD card maximum/startup at actual3.3V/50MHz; .250A supported branch allocation is not any-card compatibility.",
            "Exact shunt MPN tolerance/TCR/wattage/footprint, inductor hot Isat/DCR/L and full converter compensation/load-step/input ripple proof.",
            "Main24V eFuse exact off-testpoint ILIM/resistor transfer, series path, loss/thermal, analog18V and inputPSU foldback coordination.",
            "CM5 complete-pair high-current application thermal/IR qualification; blanket.3A test is not the same as Pi's stated higher-current application testing.",
            "SBC/SD/USB module powered-off/ramp/backfeed and sequencing under reset/recovery; all-fault response must cut safely without automatic rearm.",
        ],
    }
    (HERE / "power-capacity-review.json").write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
    print(json.dumps({k:report[k] for k in ("source_input_hashes_verified","parent_source_footprints_at_snapshot","compute_physical_parts","normal_cases","shared_CORE24_input_normal_screen")},indent=2))
    return report


if __name__ == "__main__":
    run()
