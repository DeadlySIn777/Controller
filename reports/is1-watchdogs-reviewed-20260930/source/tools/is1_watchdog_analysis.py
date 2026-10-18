"""Numerical screening of the IS-1 external watchdog candidate.

This is neither a SPICE model nor a physical timing measurement. Capacitor
temperature, board parasitics and leakage remain assumed design allowances.
Datasheet current and timing tolerances are not independent, so the IC's
current min/max are not multiplied into its specified timer error a second time.
"""
from __future__ import annotations

import argparse
import json
import math
from pathlib import Path

TI_SOURCE = "https://www.ti.com/lit/ds/symlink/tps3851.pdf"
CAP_SOURCE = "https://product.samsungsem.com/mlcc/CL10C332JB8NNN.do"


def screen(cap_nf=3.3, tolerance=.05, temperature_allowance=.006,
           parasitic_pf=10.0, leakage_na=10.0, downstream_ms=4.31):
    """Return explicit bounds; finite nonnegative inputs only.

    0.6% temperature allowance and 10pF parasitics are engineering screens,
    not measured values or capacitor manufacturer guarantees. +/-10nA uses
    the IS-1 leakage approximation against TI's typical 375nA charging current.
    The watchdog IC timing specification alone does not validate that model.
    """
    values = (cap_nf, tolerance, temperature_allowance, parasitic_pf,
              leakage_na, downstream_ms)
    if any(not isinstance(v, (int, float)) or isinstance(v, bool) or
           not math.isfinite(v) for v in values):
        raise ValueError("finite numeric inputs required")
    if cap_nf <= 0 or not 0 <= tolerance < 1 or not 0 <= temperature_allowance < 1:
        raise ValueError("positive capacitor and fractional tolerances required")
    if parasitic_pf < 0 or not 0 <= leakage_na < 375 or downstream_ms < 0:
        raise ValueError("nonnegative allowances and leakage below 375nA required")
    lower_c = cap_nf * (1-tolerance)
    upper_c = cap_nf * (1+tolerance)
    if lower_c*(1-temperature_allowance) < .1 or upper_c*(1+temperature_allowance)+parasitic_pf/1000 > 1000:
        raise ValueError("effective capacitor screen exceeds TI's 0.1-1000nF recommended range")
    # TI SBVS300B, section 7.1.1, Equation 1, standard-timing 'S' suffix.
    timer = lambda c: 3.23*c + .381
    ideal_min = timer(lower_c)*.905
    ideal_max = timer(upper_c)*1.095
    # Reproduce frozen IS-1's approximation exactly; then extend the screen.
    leakage_min = ideal_min * 375/(375+leakage_na)
    leakage_max = ideal_max * 375/(375-leakage_na)
    screen_min = timer(lower_c*(1-temperature_allowance))*.905*375/(375+leakage_na)
    screen_max = timer(upper_c*(1+temperature_allowance)+parasitic_pf/1000)*1.095*375/(375-leakage_na)
    total = screen_max+downstream_ms
    return {
        "evidence_kind": "datasheet arithmetic with unverified design allowances",
        "manufacturing_ready": False,
        "input": dict(zip(("cap_nf", "initial_tolerance", "temperature_allowance",
                           "parasitic_pf", "leakage_na", "downstream_ms"), values)),
        "nominal_ms": timer(cap_nf),
        "cap_and_ic_only_ms": [ideal_min, ideal_max],
        "is1_leakage_screen_ms": [leakage_min, leakage_max],
        "extended_screen_ms": [screen_min, screen_max],
        "clock_stall_to_inhibit_allocation_ms": total,
        "remaining_20ms_budget_ms": 20-total,
        "below_20ms_under_assumptions": total <= 20,
        "greater_than_5ms_under_assumptions": screen_min > 5,
        "old_toggle_10ms_edge_spacing_compatible": screen_min > 10,
        "selftest_is1_window_ms": [9.06, 13.37],
        "extended_request_to_trip_with_nominal_setup_ms": [screen_min, screen_max+.150],
        "set1_setup_nominal_ms": .150,
        "set1_setup_maximum_guaranteed": False,
        "selftest_window_contains_nominal_setup_screen":
            screen_min >= 9.06 and screen_max+.150 <= 13.37,
        "selftest_upper_clearance_under_nominal_setup_assumption_ms": 13.37-(screen_max+.150),
        "selftest_guaranteed_timing_bounds_closed": False,
        "wdi_pulse_ns": 1000,
        "wdi_minimum_pulse_ns": 50,
        "wdi_pulse_ratio": 20,
        "downstream_is_an_allocation_not_a_measurement": True,
        "startup_and_set1_transients_physically_verified": False,
        "not_proved": ["capacitor temperature/bias/ageing envelope", "CWD leakage at 55C/85%RH",
                       "PCB node parasitics", "startup/SET1 evaluation time", "Schmitt VOL margin",
                       "complete permission-chain delays", "physical clock-stall fault response"],
        "sources": [TI_SOURCE, CAP_SOURCE],
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = {"schema_version": 1, "selected_3n3": screen(),
              "previous_4n7_comparison": screen(cap_nf=4.7)}
    raw = json.dumps(report, indent=2)+"\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        if args.output.exists():
            raise SystemExit("Refusing to overwrite numerical evidence")
        args.output.write_text(raw, encoding="utf-8")
    print(raw)


if __name__ == "__main__":
    main()
