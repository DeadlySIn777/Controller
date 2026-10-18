"""Read-only option screening. Does not change any implemented circuit or budget.

Run from any directory with Python 3: python research/expanded-power/analyze.py
Only this directory's analysis.json is written. No physical-device access.
"""
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).resolve().parent


def finite_positive(value):
    if isinstance(value, bool) or not isinstance(value, (float, int)):
        raise ValueError("finite positive number required")
    if not math.isfinite(value) or value <= 0:
        raise ValueError("finite positive number required")
    return value


def input_current(power, efficiency=.85, auxiliary=.065, voltage=19, resistance=.2):
    for x in (power, efficiency, auxiliary, voltage, resistance):
        finite_positive(x)
    if efficiency > 1:
        raise ValueError("efficiency above unity")
    b = voltage + resistance * auxiliary
    c = voltage * auxiliary + power / efficiency
    d = b * b - 4 * resistance * c
    if d < 0:
        raise ValueError("no stable static power/path operating point")
    return 2 * c / (b + math.sqrt(d))


def current_limit(resistor):
    finite_positive(resistor)
    # Transfer +/-10% is a screening assumption, not a guaranteed TI bound
    # at 5.10k or7.50k. Resistor total +/-0.5% also requires qualification.
    return [18000 * .9 / (resistor * 1.005),
            18000 * 1.1 / (resistor * .995)]


def unload(current, bulk_count, input_v=48.4, target=5.25):
    for x in (current, bulk_count, input_v, target):
        finite_positive(x)
    if not isinstance(bulk_count, int):
        raise ValueError("integer capacitor count required")
    # Same unqualified effective L and capacitor assumptions as r0.3 core
    # study. A different inductor requires reconfirming the effective limits.
    lmin, lmax, fmin = 2.632e-6, 5.64e-6, 398000
    cer_min = 3 * 20.5e-6
    cap_min = bulk_count * 330e-6 * .8 * .8 + cer_min
    esr = .0065 * 2 / bulk_count + .0006666666666666666
    ripple = 5.05 * (1 - 5.05 / input_v) / (lmin * fmin)
    start_v = 5.05 + ripple * (.002 + 1 / (8 * fmin * cer_min)) / 2
    corners = []
    for inductance in (lmin, lmax):
        peak = current + 5.05 * (1 - 5.05 / input_v) / (2 * inductance * fmin)
        corners.append({"inductance_h": inductance, "phase_peak_a": peak,
                        "twice_inductor_energy_j": inductance * peak * peak})
    energy = max(x["twice_inductor_energy_j"] for x in corners)
    esr_step = max(x["phase_peak_a"] for x in corners) * esr
    maximum = math.sqrt(start_v * start_v + energy / cap_min) + esr_step
    denominator = (target - esr_step) ** 2 - start_v ** 2
    feasible_denominator = target > esr_step and denominator > 0
    return {"load_removed_a": current, "bulk_count": bulk_count,
            "input_reference_v": input_v, "effective_cap_min_f_assumed": cap_min,
            "esr_ohm_assumed": esr, "phase_corners": corners,
            "initial_voltage_v": start_v, "independent_esr_step_v": esr_step,
            "screen_max_v": maximum, "screen_margin_v": target - maximum,
            "required_effective_cap_f": energy / denominator if feasible_denominator else None,
            "finite_cap_can_meet_target_with_fixed_ripple_and_esr": feasible_denominator,
            "passes_upper_voltage_arithmetic_only": maximum <= target,
            "production_or_stability_pass": False}


def analyze():
    req_path = ROOT / 'hardware/core_converter/requirements.json'
    req = json.loads(req_path.read_text(encoding='utf-8-sig'))
    e = req['design_envelope']
    s = e['sequenced_sbc']
    # Parent task's newly audited loads, additional to old six-joint source.
    additional_io3v3_a = .060 + .010
    io3v3_worst_v, core5_min_v, efficiency = 3.34125, 4.85, .85
    additional_core5_running_a = additional_io3v3_a * io3v3_worst_v / (core5_min_v * efficiency)
    caps = {'esp_3v3_f': 28.658e-6, 'fpga_1v2_f': 10.879e-6,
            'fpga_io3v3_f': 44.92e-6, 'permission_io3v3_f': .9662e-6}
    new_charge = (caps['fpga_1v2_f'] * 1.215**2 +
                  (caps['esp_3v3_f'] + caps['fpga_io3v3_f'] + caps['permission_io3v3_f']) * io3v3_worst_v**2) / (.001156 * core5_min_v * efficiency)
    base_local_charge = 32.208e-6 * (1.215**2 + 2 * io3v3_worst_v**2) / (.001156 * core5_min_v * efficiency)
    logic_charge_reservation = .400
    host_rise = ((.011 * 5.25 + .002) * 470e3 + 4.7 * 5.25 + 7.8) * 1e-6 * .5
    host_charge = .001 * .8 * 5.25 / host_rise
    main_max_cap = (3 * 330e-6 * 1.2 * 1.2 + 3 * 47e-6 * 1.2 * 1.22
                    + s['existing_other_main_cap_max_f_assumed'] + s['new_sbc_input_cap_max_f_assumed'])
    main_charge = main_max_cap * 5.05 / .0019
    result = {
        'scope': 'Proposal screening only; existing six-joint circuit remains unchanged. No AI/display power allowance.',
        'current_requirement': '8 motors minimum; 12-motor expansion; historical6 retained for comparison only',
        'assumptions': {
            'additional_io3v3_a': additional_io3v3_a, 'additional_core5_running_a': additional_core5_running_a,
            'local_cap_max_f_assumed': caps, 'additional_logic_cap_charge_core5_a': new_charge,
            'existing_local_output_cap_charge_core5_a': base_local_charge,
            'calculated_combined_logic_charge_core5_a': new_charge + base_local_charge,
            'rounded_logic_charge_reservation_a': logic_charge_reservation,
            'host_cap_charge_core5_a': host_charge, 'main_cap_max_f': main_max_cap,
            'main_cap_charge_a': main_charge, 'input_efficiency': efficiency,
            'input_efficiency_is_guaranteed': False, 'main_voltage_proposal_v': [4.85, 5.25],
            'fixed5v_dc_regulation_v': [4.95, 5.05],
            'maximum_input_power_uses_5p25v_times_reserved_current': True,
            'tx_bank_0p2a_reservation_is_guaranteed_load_fault_bound': False,
        },
        'entry_screening': {str(r): {'min_a': current_limit(r)[0], 'max_a': current_limit(r)[1]}
                            for r in (7500, 5100)},
        'integrated_options': {},
    }
    for motors in (6, 8, 12):
        tx = motors * .1
        normal = e['normal_current_with_encoder_overhead_a'] + tx - .6 + additional_core5_running_a
        fault = e['simultaneous_encoder_limited_fault_current_a'] + tx - .6 + additional_core5_running_a
        # New IO support consumes no operating reservation while its rail is held off;
        # disabled current screening remains1mA, not guaranteed partial-power behavior.
        main_start = fault - 3 - 1.29 - additional_core5_running_a + .001 + main_charge
        cases = {'normal': normal, 'encoder_limited_fault': fault,
                 'cold_main_charge': main_start, 'logic_charge_host_off': fault - 3 + logic_charge_reservation,
                 'host_charge_after_logic': fault + host_charge,
                 'unqualified_logic_host_overlap': fault + host_charge + logic_charge_reservation,
                 'unqualified_all_loads_with_main_charge': fault + main_charge}
        rows = {}
        for name, current in cases.items():
            input_a = input_current(current * 5.25)
            rows[name] = {'core5_current_a': current, 'fits6a': current <= 6, 'fits10a': current <= 10,
                          'input_current_a': input_a, 'protected_input_v': 19 - .2 * input_a,
                          'old7500ohm_entry_margin_a': current_limit(7500)[0] - input_a,
                          'proposed5100ohm_entry_margin_a': current_limit(5100)[0] - input_a}
        result['integrated_options'][str(motors)] = rows
    # Dedicated24V->5V TX branch removes ALL old TX0.6A from the main, not only delta.
    split_fault = e['simultaneous_encoder_limited_fault_current_a'] - .6 + additional_core5_running_a
    result['dedicated_tx_5v'] = {
        'main_fault_current_a': split_fault,
        'main_host_start_a': split_fault + host_charge,
        'main_cold_start_a': split_fault - 3 - 1.29 - additional_core5_running_a + .001 + main_charge,
        'tx_reserved_a_12motor': 1.2, 'tx_converter_rating_a': 2,
        'shared_input_host_start_a_same85pct_efficiency': input_current((split_fault + host_charge + 1.2) * 5.25),
        'additional_converter_startup_and_quiescent_current_included': False,
    }
    # 3.3V TXrail reservation kept1.2A; not a promised driver current reduction.
    # Worst3.34125V output,85% local efficiency, input4.85V; the upstream24V
    # converter adds another efficiency loss, so no double-counted savings.
    tx3v3_core5 = 1.2 * 3.34125 / (.85 * 4.85)
    result['dedicated_tx_3v3_from_core5'] = {
        'tx3v3_reserved_a_12motor': 1.2, 'tx_converter_rating_a_proposal': 2,
        'core5_equivalent_tx_a': tx3v3_core5,
        'total_core5_fault_a': split_fault + tx3v3_core5,
        'total_core5_host_start_a': split_fault + tx3v3_core5 + host_charge,
        'main6a_host_start_pass': split_fault + tx3v3_core5 + host_charge <= 6,
        'additional_regulator_iq_and_startup_charge_included': False,
        'existing_io3v3_total_with_shared_tx_a': .4 + .07 + 1.2,
        'existing_io3v3_1a_regulator_sufficient': False,
    }
    result['dedicated_tx_3v3_from_protected24v'] = {
        'main_fault_current_a': split_fault, 'main_host_start_a': split_fault + host_charge,
        'main_cold_start_a': result['dedicated_tx_5v']['main_cold_start_a'],
        'tx_reserved_a_12motor': 1.2, 'tx_output_max_screening_v': 3.6,
        'tx_converter_rating_a_proposal': 2,
        'shared_input_host_start_a_same85pct_efficiency': input_current((split_fault + host_charge) * 5.25 + 1.2 * 3.6),
        'added_regulator_iq_or_tx_startup_included': False,
        'old_entry_or_new_driver_current_qualified': False,
    }
    result['unload_screens'] = [unload(current, n, vin, target)
        for current in (6, result['integrated_options']['12']['host_charge_after_logic']['core5_current_a'], 10)
        for n in (2, 3) for vin in (30, 48.4) for target in (5.15, 5.25)]
    result['lm706a0_shunt_screen'] = {
        'supported_shunt_ohm': .004, 'assumed_total_resistance_tolerance': .02,
        'ocp_threshold_min_a': .05 / (.004 * 1.02),
        'ocp_threshold_max_a': .062 / (.004 * .98),
        'short_peak_using_typ75ns_delay_a': .062 / (.004 * .98) + 48.4 * 75e-9 / 2.632e-6,
        'guaranteed_maximum_short_current': False,
        'input_at_full10a_5p25v_a': input_current(10 * 5.25),
        'entry5100ohm_supports_full10a_load': input_current(10 * 5.25) <= current_limit(5100)[0],
        'old7070_typ25c_30pct_drop_current_a': 15.2,
        'proposed1010_typ25c_30pct_drop_current_a': 25.4,
        'proposed1010_hot_saturation_guaranteed': False,
        'compensation_unchanged9p53k_crossover_typ_hz': .8/5*.0012/(.004*10)*9530/(2*math.pi*695.1e-6),
        'candidate6p34k_crossover_typ_hz': .8/5*.0012/(.004*10)*6340/(2*math.pi*695.1e-6),
        'candidate33nf_zero_hz': 1/(2*math.pi*6340*33e-9),
        'candidate560pf_plus38pf_hf_pole_hz': 1/(2*math.pi*6340*(560e-12+38e-12)),
        'compensation_stability_proven': False,
    }
    result['voltage_compatibility'] = {
        'cm4_module_input_min_v': 4.75, 'cm4_module_input_max_v': 5.25,
        'sbc_path_resistance_assumed_ohm': .008 + .015,
        'sbc_min_if_main4p75_v': 4.75 - 3*(.008+.015),
        'main_min_needed_for4p75_sbc_v': 4.75 + 3*(.008+.015),
        'existing_core5_ov_trip_v': [5.072599256, 5.137464293],
        'existing_monitor_compatible_with5p25_v': False,
    }
    paths = [req_path, ROOT/'tools/core_converter_analysis.py',
             ROOT/'hardware/power_entry/requirements.json',
             ROOT/'hardware/power_sequence/design-envelope.json',
             ROOT/'hardware/esp_service/design-envelope.json',
             ROOT/'hardware/fpga_core/design.json',
             ROOT/'hardware/machine_permission/design-envelope.json', Path(__file__)]
    result['source_hashes_at_calculation'] = {str(p.relative_to(ROOT)).replace('\\','/'):
        hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    result['manufacturing_ready'] = False
    return result


if __name__ == '__main__':
    result = analyze()
    (HERE/'analysis.json').write_text(json.dumps(result, indent=2, allow_nan=False)+'\n', encoding='utf-8')
    print(json.dumps({'status': 'option_arithmetic_complete_not_qualified',
                     '12motor': result['integrated_options']['12'],
                     'split': result['dedicated_tx_5v'],
                     '3v3_tx': result['dedicated_tx_3v3_from_core5']}, indent=2))
