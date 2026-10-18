"""Boundary regressions for declared electrical budgets, not physical tests."""
import math
import unittest
from tools.watchdog_conditioning_analysis import screen


class WatchdogConditioningAnalysisTests(unittest.TestCase):
    def test_startup_recalculated_independently(self):
        # Parallel equivalent resistance * summed source current, independently
        # stated TI/Efinix values and 5uA board allowance.
        equivalent = 1/(1/27000+1/4747)
        expected = equivalent*(3.465/27000+(10+5+5)/1000000)
        got = screen()
        self.assertAlmostEqual(got['startup_input_max_v_under_assumptions'], expected, 12)
        self.assertTrue(got['startup_input_low_under_assumptions'])
        self.assertAlmostEqual(got['startup_low_margin_v_under_assumptions'], .20114861246731985)

    def test_10k_and_historical_100k_rejected(self):
        for pull in (10000, 100000):
            with self.subTest(pull=pull):
                got = screen(pull_ohm=pull)
                self.assertFalse(got['startup_input_low_under_assumptions'])
                self.assertLess(got['startup_low_margin_v_under_assumptions'], 0)

    def test_excessive_leakage_loses_startup_margin(self):
        self.assertFalse(screen(injected_leakage_ua=100)['startup_input_low_under_assumptions'])

    def test_open_reset_has_strong_default_under_assumptions(self):
        self.assertAlmostEqual(screen()['disconnected_reset_max_v_under_assumptions'], .118675)
        self.assertTrue(screen()['disconnected_reset_low_under_assumptions'])

    def test_high_output_load_includes_pulldown(self):
        got = screen()
        self.assertAlmostEqual(got['set1_high_source_budget_ua'], 85)
        self.assertTrue(got['high_load_within_100ua_characterization'])
        self.assertAlmostEqual(got['set1_voh_min_v_conditional_on_load_budget'], 2.99)

    def test_unknown_timer_leakage_can_exceed_high_characterization(self):
        got = screen(timer_pin_load_ua=66)
        self.assertFalse(got['high_load_within_100ua_characterization'])
        self.assertIsNone(got['set1_voh_min_v_conditional_on_load_budget'])

    def test_excessive_low_current_removes_vol_claim(self):
        got = screen(timer_pin_load_ua=101)
        self.assertFalse(got['low_load_within_100ua_characterization'])
        self.assertIsNone(got['set1_vol_max_v_conditional_on_load_budget'])
        self.assertIsNone(got['set1_low_margin_v_conditional_on_load_budget'])

    def test_one_microsecond_pulse_has_qualified_table_delay_allowance(self):
        got = screen()
        self.assertEqual(got['wdi_high_width_range_ns_under_datasheet_test_conditions'], [995.3,1004.7])
        self.assertTrue(got['wdi_width_passes_under_datasheet_test_conditions'])
        self.assertFalse(got['physical_transition_duplicate_edges_qualified'])

    def test_too_short_pulse_rejected_by_screen(self):
        self.assertFalse(screen(wdi_high_ns=54)['wdi_width_passes_under_datasheet_test_conditions'])

    def test_no_qualification_or_agreement_claims(self):
        got = screen()
        for key in ('interface_agreed', 'manufacturing_ready', 'physical_qualification',
                    'startup_defaults_qualified', 'complete_permission_chain',
                    'timer_input_leakage_datasheet_bound_available',
                    'timer_pin_load_budget_physically_verified', 'set1_setup_maximum_guaranteed',
                    'fpga_selected_loaded_drive_strength_qualified', 'upstream_reset_total_fanout_qualified'):
            self.assertIs(got[key], False, key)

    def test_invalid_inputs_raise(self):
        for kwargs in ({'pull_ohm':0}, {'tolerance':1}, {'injected_leakage_ua':-1},
                       {'timer_pin_load_ua':math.nan}, {'pull_ohm':True},
                       {'wdi_high_ns':0}, {'output_load_pf':51}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                screen(**kwargs)


if __name__ == '__main__':
    unittest.main()
