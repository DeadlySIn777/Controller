"""Explicit DC/pulse screens for the separate proposed IS-2 circuit.

Numbers describe valid 3.14-3.465V rails, not a complete startup/partial-power
guarantee. TPS3851 SET1 and WDI input leakage maxima are not specified in the
retained datasheet; 50uA is a qualification requirement, never a datasheet fact.
"""
from __future__ import annotations
import argparse
import json
import math
from pathlib import Path


def screen(pull_ohm=4700, tolerance=.01, injected_leakage_ua=20,
           timer_pin_load_ua=50, wdi_high_ns=1000, output_load_pf=50):
    values = (pull_ohm, tolerance, injected_leakage_ua, timer_pin_load_ua,
              wdi_high_ns, output_load_pf)
    if any(isinstance(v, bool) or not isinstance(v, (int, float)) or
           not math.isfinite(v) for v in values):
        raise ValueError('finite numeric inputs required')
    if pull_ohm <= 0 or not 0 <= tolerance < 1 or min(injected_leakage_ua, timer_pin_load_ua) < 0:
        raise ValueError('positive pull and bounded nonnegative allowances required')
    if wdi_high_ns <= 0 or not 0 < output_load_pf <= 50:
        raise ValueError('positive pulse and source-screened output load <=50pF required')
    rail_min, rail_max = 3.14, 3.465
    weak_pull_min = 27000
    strongest_pd = pull_ohm*(1-tolerance)
    weakest_pd = pull_ohm*(1+tolerance)
    current_a = injected_leakage_ua*1e-6
    startup_v = (rail_max/weak_pull_min + current_a)/(1/weak_pull_min+1/weakest_pd)
    # Two powered AND inputs (5uA each), upstream unpowered output (10uA),
    # plus assumed 5uA board leakage. Open reset boundary uses a stronger pull.
    disconnected_reset_v = 25e-6*weakest_pd
    gpio_high_load_ua = (rail_max/strongest_pd+5e-6)*1e6
    reset_high_load_ua = (rail_max/strongest_pd+10e-6)*1e6
    low_load_ua = timer_pin_load_ua  # PD discharges toward ground; does not source current.
    high_load_ua = rail_max/(100000*.99)*1e6+timer_pin_load_ua
    low_light_load_supported = low_load_ua <= 100
    high_light_load_supported = high_load_ua <= 100
    # TI maximum over -40..125C and VCC=3.3V +/-0.3V, <=50pF load.
    set_delay_max_ns, wdi_delay_max_ns = 6.0, 4.7
    # No minimum credit: use [0,max] for each edge; no skew multiplication.
    wdi_min_high_ns = wdi_high_ns-wdi_delay_max_ns
    wdi_max_high_ns = wdi_high_ns+wdi_delay_max_ns
    return {
        'evidence_class': 'manufacturer_datasheet_arithmetic_with_declared_load_leakage_assumptions',
        'interface_revision': 'IS-2-PROPOSED', 'interface_agreed': False,
        'manufacturing_ready': False, 'physical_qualification': False,
        'startup_defaults_qualified': False, 'complete_permission_chain': False,
        'inputs': dict(zip(('pull_ohm', 'tolerance', 'injected_leakage_ua', 'timer_pin_load_ua',
                            'wdi_high_ns', 'output_load_pf'), values)),
        'rail_screen_v': [rail_min, rail_max], 'weak_pullup_min_ohm': weak_pull_min,
        'startup_input_max_v_under_assumptions': startup_v,
        'buffer_vil_max_v': .8, 'startup_low_margin_v_under_assumptions': .8-startup_v,
        'startup_input_low_under_assumptions': startup_v <= .8,
        'disconnected_reset_max_v_under_assumptions': disconnected_reset_v,
        'disconnected_reset_low_under_assumptions': disconnected_reset_v <= .8,
        'additional_gpio_high_load_max_ua_under_assumptions': gpio_high_load_ua,
        'additional_user_reset_high_load_max_ua_under_assumptions': reset_high_load_ua,
        'fpga_lvcmos_voh_min_v': rail_min-.2, 'buffer_vih_min_v': 2,
        'fpga_high_margin_v_conditional_on_drive_standard_and_load': rail_min-.2-2,
        'fpga_selected_loaded_drive_strength_qualified': False,
        'upstream_lvc_reset_driver_voh_min_v_at_16ma': 2.4,
        'upstream_reset_driver_total_load_must_not_exceed_ma': 16,
        'upstream_reset_total_fanout_qualified': False,
        'set1_low_sink_budget_ua': low_load_ua,
        'set1_high_source_budget_ua': high_load_ua,
        'low_load_within_100ua_characterization': low_light_load_supported,
        'high_load_within_100ua_characterization': high_light_load_supported,
        'set1_vol_max_v_conditional_on_load_budget': .1 if low_light_load_supported else None,
        'set1_vil_max_v': .25,
        'set1_low_margin_v_conditional_on_load_budget': .15 if low_light_load_supported else None,
        'set1_voh_min_v_conditional_on_load_budget': rail_min-.15 if high_light_load_supported else None,
        'set1_vih_min_v': .8,
        'timer_input_leakage_datasheet_bound_available': False,
        'timer_pin_load_budget_physically_verified': False,
        'wdi_vol_max_v_conditional_on_load_budget': .1 if low_light_load_supported else None,
        'wdi_low_threshold_min_v': .3*rail_min,
        'wdi_voh_min_v_conditional_on_load_budget': rail_min-.1 if high_light_load_supported else None,
        'wdi_high_threshold_max_v': .8*rail_max,
        'set1_gate_delay_max_ns_under_datasheet_test_conditions': set_delay_max_ns,
        'wdi_buffer_delay_max_ns_under_datasheet_test_conditions': wdi_delay_max_ns,
        'wdi_high_width_range_ns_under_datasheet_test_conditions': [wdi_min_high_ns, wdi_max_high_ns],
        'wdi_minimum_high_ns': 50,
        'wdi_width_passes_under_datasheet_test_conditions': wdi_min_high_ns >= 50,
        'pulse_count_preserved_in_ideal_static_guard_model': True,
        'physical_transition_duplicate_edges_qualified': False,
        'set1_setup_nominal_ms': .150, 'set1_setup_maximum_guaranteed': False,
        'additional_request_delay_allocation_ms': set_delay_max_ns/1e6,
        'not_proved': ['IS-2 agreement', 'TPS3851 pin leakage maximum', 'GPIO loaded VOH/VOL',
                      'input slew/noise and output capacitance', 'reset guard fanout and sequence',
                      'ramping or partially powered components', 'no extra physical WDI edges',
                      'complete permission/latch chain', 'physical 20ms fault-to-inhibit'],
        'sources': ['https://www.ti.com/lit/ds/symlink/sn74lvc1g08.pdf',
                    'https://www.ti.com/lit/ds/symlink/sn74lvc1g34.pdf',
                    'https://www.ti.com/lit/ds/symlink/tps3851.pdf',
                    'research/fpga-core/trion20-ds-v6.0.pdf'],
    }


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--output', type=Path)
    args = ap.parse_args()
    report = {'schema_version': 1, 'proposed_4k7': screen(),
              'rejected_10k_comparison': screen(pull_ohm=10000),
              'historical_100k_comparison': screen(pull_ohm=100000)}
    raw = json.dumps(report, indent=2)+'\n'
    if args.output:
        if args.output.exists():
            raise SystemExit('Refusing to overwrite numerical evidence')
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(raw, encoding='utf-8')
    print(raw)


if __name__ == '__main__':
    main()
