"""Bounded arithmetic for the proposed core converter; no device access or simulation.

All design assumptions come from requirements, not stored result fields. Manufacturer
numbers used below are identified by datasheet section in the accompanying review.
"""
from __future__ import annotations
import argparse
import hashlib
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DEFAULT = ROOT / "hardware/core_converter/requirements.json"


def number(obj, name, lo=0.0, hi=1e9, *, positive=False):
    value = obj[name]
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise ValueError(f"{name}: finite number required")
    try:
        value = float(value)
    except OverflowError as exc:
        raise ValueError(f"{name}: out of range") from exc
    if not math.isfinite(value) or value < lo or value > hi or (positive and value <= 0):
        raise ValueError(f"{name}: outside allowed range")
    return value


def pair(obj, name, lo=0.0, hi=1e9):
    values = obj[name]
    if not isinstance(values, list) or len(values) != 2:
        raise ValueError(f"{name}: ordered two-value range required")
    a, b = [number({name: v}, name, lo, hi) for v in values]
    if a > b:
        raise ValueError(f"{name}: reversed range")
    return a, b


def input_current(v, r, output_power, efficiency, aux):
    """Low-current root of I=P/[eta*(V-R*I)]+aux, stable for small R."""
    if not all(math.isfinite(x) for x in (v, r, output_power, efficiency, aux)):
        raise ValueError("nonfinite input-current operand")
    if v <= 0 or r < 0 or output_power < 0 or not 0 < efficiency <= 1 or aux < 0:
        raise ValueError("invalid input-current operand")
    b = v + r * aux
    c = v * aux + output_power / efficiency
    discriminant = b * b - 4 * r * c
    if discriminant < 0:
        raise ValueError("no static operating point with given resistance and power")
    current = 2 * c / (b + math.sqrt(discriminant))
    if v - r * current <= 0:
        raise ValueError("no positive protected-input voltage")
    return current


def analyze(req):
    if req["converter"]["mpn"] != "LM70660RRXR":
        raise ValueError("this analysis requires exact6A LM70660RRXR, not10A LM706A0")
    expected = {"L1": "XAL7070-472MEC", "RS1": "KRL3216D-C-R006-F-T1"}
    passives = {p["id"]: p for p in req["passives"]}
    for ref, mpn in expected.items():
        if passives[ref]["mpn"] != mpn:
            raise ValueError(f"{ref}: unsupported part for fixed manufacturer constants")
    e = req["design_envelope"]
    vin_min, vin_max = pair(e, "whole_controller_input_v_proposed", 4.5, 60)
    vout_min, vout_max = pair(req["converter"], "fixed_output_v", 4.5, 5.5)
    current_rating = number(req["converter"], "rated_output_current_a", 6, 6)
    normal = number(e, "normal_current_with_encoder_overhead_a", 0, 20)
    fault = number(e, "simultaneous_encoder_limited_fault_current_a", normal, 20)
    efficiency = number(e, "efficiency_screening_floor", 0.1, 1)
    aux = number(e, "analog_input_reservation_a", 0, 1) + number(e, "entry_and_auxiliary_input_reservation_a", 0, 1)
    path = number(e, "series_path_resistance_budget_ohm", 0, 5)
    rilim = number(e, "proposed_entry_rilim_ohm", 3000, 30000)
    itol = number(e, "entry_ilim_screening_ic_fraction", 0, 0.5)
    rtol = number(e, "entry_ilim_screening_resistor_fraction", 0, 0.1)
    ilim_low = 18000 * (1 - itol) / (rilim * (1 + rtol))
    ilim_high = 18000 * (1 + itol) / (rilim * (1 - rtol))
    source_rating = number(e, "proposed_core_source_wiring_capacity_a", 0, 20, positive=True)
    soft = e["soft_start_time_s"]
    if not isinstance(soft, list) or len(soft) != 3:
        raise ValueError("three softstart corners required")
    soft = [number({"soft": x}, "soft", 0.0001, 1) for x in soft]
    if sorted(soft) != soft:
        raise ValueError("softstart corners must be ordered")
    cap_start = number(e, "startup_total_output_capacitance_screening_max_f", 1e-9, 0.1)
    load_start = number(e, "startup_load_before_encoder_enable_max_a", 0, 20)
    cap_current = cap_start * vout_max / soft[0]
    startup = load_start + cap_current
    startup_fault = fault + cap_current
    lmin = number(e, "inductor_screening_min_h", 1e-9, 1)
    lmax = number(e, "inductor_screening_max_h", lmin, 1)
    fmin, fmax = pair(e, "switching_frequency_hz_with_extra_screening_drift", 100000, 3000000)
    cout = number(e, "output_effective_capacitance_f_assumed", 1e-9, 0.1)
    esr = number(e, "output_esr_ohm_assumed", 0, 1)
    shunt_tol = number(e, "shunt_total_tolerance_fraction_assumed", 0, 0.1)
    shunt_min, shunt_max = 0.006 * (1 - shunt_tol), 0.006 * (1 + shunt_tol)
    threshold_min, threshold_max = 0.050 / shunt_max, 0.062 / shunt_min
    transient = number(e, "protected_positive_transient_v_reference", vin_max, 65)
    ripple = vout_max * (1 - vout_max / vin_max) / (lmin * fmin)
    ripple_transient = vout_max * (1 - vout_max / transient) / (lmin * fmin)
    peak = current_rating + ripple / 2
    peak_transient = current_rating + ripple_transient / 2
    rms = math.sqrt(current_rating ** 2 + ripple ** 2 / 12)
    output_high = pair(e, "output_steady_state_target_v", 4.5, 5.5)[1]
    if output_high <= vout_max:
        raise ValueError("output target leaves no positive overshoot allowance")
    max_allowed_step = math.sqrt(cout * (output_high ** 2 - vout_max ** 2) / lmax)
    unload_v = math.sqrt(vout_max ** 2 + lmax * current_rating ** 2 / cout)
    required_cout = lmax * current_rating ** 2 / (output_high ** 2 - vout_max ** 2)
    rcomp = 4990.0
    fc = rcomp / (2 * math.pi * (5 / 0.8) * (0.006 * 10 / 0.0012) * cout)
    rows = {}
    for name, amps in (("normal", normal), ("encoder_fault", fault), ("rated6a", current_rating), ("startup_encoders_off", startup), ("startup_with_encoder_fault", startup_fault)):
        iin = input_current(vin_min, path, vout_max * amps, efficiency, aux)
        rows[name] = {"output_current_a": amps, "input_current_a": iin,
                      "protected_input_v": vin_min - path * iin,
                      "screened_ilim_margin_a": ilim_low - iin,
                      "fits6a": amps <= current_rating,
                      "fits_screened_entry_minimum": iin <= ilim_low}
    output = {
        "evidence": "bounded arithmetic only; assumptions are not manufacturer guarantees or physical measurements",
        "entry": {"nominal_limit_a": 18000 / rilim, "screening_min_a": ilim_low,
                  "screening_max_a": ilim_high, "source_capacity_margin_a": source_rating - ilim_high,
                  "minimum_efficiency_for6a_with_screened_limit": vout_max * current_rating / ((ilim_low - aux) * (vin_min - path * ilim_low)),
                  "operating_cases": rows},
        "startup": {"capacitor_charge_current_a": cap_current, "total_cap_budget_f": cap_start,
                    "local_caps_temperature_tolerance_max_f": 4 * 47e-6 * 1.2 * 1.22,
                    "remaining_downstream_cap_budget_f": cap_start - 4 * 47e-6 * 1.2 * 1.22,
                    "max_capacitance_at_fault_load_and6a_f": (current_rating - fault) * soft[0] / vout_max},
        "switching": {"ripple_current_normal_a_pp": ripple, "peak_current6a_normal_a": peak,
                      "ripple_current_transient_a_pp": ripple_transient, "peak_current6a_transient_a": peak_transient,
                      "inductor_rms6a_a": rms, "ocp_threshold_min_a": threshold_min, "ocp_threshold_max_a": threshold_max,
                      "normal_ocp_margin_a": threshold_min - peak, "transient_ocp_margin_a": threshold_min - peak_transient,
                      "short_peak_at_reference_clamp_using_typ75ns_delay_a": threshold_max + transient * 75e-9 / lmin,
                      "short_peak_is_guaranteed_bound": False,
                      "shunt6a_loss_w": rms ** 2 * shunt_max,
                      "inductor_copper_loss125c_using_linear_tcr_w": rms ** 2 * 0.01426 * (1 + 0.00393 * 100),
                      "output_ripple_linear_upper_estimate_v_pp": ripple / (8 * fmin * cout) + esr * ripple,
                      "input_cap_rms_conservative50pct_a": current_rating / 2,
                      "input_cap_min_for0p5v_pp_at50pct_f": 0.25 * current_rating / (fmin * (0.5 - esr * current_rating))},
        "transient_regulation": {"full6a_unload_energy_screen_output_v": unload_v,
                                 "target_max_v": output_high, "full6a_unload_pass": unload_v <= output_high,
                                 "effective_cap_needed_full6a_unload_f": required_cout,
                                 "max_unload_step_energy_only_a": max_allowed_step,
                                 "warning": "energy-only necessary screen omits control delay/ESR/tolerance interaction; passing is not measured regulation"},
        "compensation": {"typical_crossover_hz": fc, "zero_hz": 1 / (2 * math.pi * rcomp * 10e-9),
                         "hf_pole_hz_with38pf_internal": 1 / (2 * math.pi * rcomp * (47e-12 + 38e-12)),
                         "phase_margin_proven": False},
        "enable": {"open_node_at19v_v": 19 / 11, "open_node_at30v_v": 30 / 11,
                   "open_node_at48p4v_v": transient / 11,
                   "pgood_low_at48p4v_using130ohm_v": transient * (10000 * 130 / (10000 + 130)) / (100000 + 10000 * 130 / (10000 + 130)),
                   "partial_power_function_proven": False},
        "thermal": {"total_converter_loss_at6a_assumed_efficiency_w": vout_max * current_rating * (1 / efficiency - 1),
                    "measured_thermal_pass": False},
        "production_qualified": False,
    }
    json.dumps(output, allow_nan=False)
    return output


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--requirements", type=Path, default=DEFAULT)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    try:
        raw = args.requirements.read_bytes()
        results = analyze(json.loads(raw))
        results["requirements_sha256"] = hashlib.sha256(raw).hexdigest()
        results["calculator_sha256"] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
        text = json.dumps(results, indent=2, allow_nan=False) + "\n"
        if args.output:
            args.output.write_text(text, encoding="utf-8")
        else:
            print(text, end="")
    except (ValueError, KeyError, TypeError, OSError, OverflowError) as exc:
        parser.exit(2, f"invalid core converter input: {exc}\n")


if __name__ == "__main__":
    main()
