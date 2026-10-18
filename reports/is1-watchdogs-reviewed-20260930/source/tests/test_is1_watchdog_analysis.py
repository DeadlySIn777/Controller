"""Design screens distinguish old feeding semantics from the IS-1 hardware."""
import math
import unittest
from tools.is1_watchdog_analysis import screen


class Is1WatchdogAnalysisTests(unittest.TestCase):
    def test_reproduces_published_frozen_arithmetic(self):
        r = screen(temperature_allowance=0, parasitic_pf=0)
        self.assertAlmostEqual(11.04, r["nominal_ms"])
        self.assertEqual(9.26, round(r["is1_leakage_screen_ms"][0], 2))
        self.assertEqual(13.02, round(r["is1_leakage_screen_ms"][1], 2))
        self.assertTrue(r["below_20ms_under_assumptions"])

    def test_selected_part_has_margin_with_explicit_extra_allowances(self):
        r = screen()
        self.assertLess(r["clock_stall_to_inhibit_allocation_ms"], 20)
        self.assertGreater(r["remaining_20ms_budget_ms"], 2.5)
        self.assertTrue(r["selftest_window_contains_nominal_setup_screen"])
        self.assertFalse(r["set1_setup_maximum_guaranteed"])
        self.assertFalse(r["selftest_guaranteed_timing_bounds_closed"])
        self.assertFalse(r["manufacturing_ready"])

    def test_old_toggling_logic_is_not_compatible_with_new_capacitor(self):
        r = screen()
        self.assertTrue(r["greater_than_5ms_under_assumptions"])
        self.assertFalse(r["old_toggle_10ms_edge_spacing_compatible"])

    def test_previous_larger_capacitor_exceeds_fault_budget(self):
        r = screen(cap_nf=4.7)
        self.assertFalse(r["below_20ms_under_assumptions"])
        self.assertLess(r["remaining_20ms_budget_ms"], 0)

    def test_larger_parasitic_and_leakage_can_destroy_claimed_margin(self):
        r = screen(parasitic_pf=1000, leakage_na=100)
        self.assertFalse(r["below_20ms_under_assumptions"])
        self.assertFalse(r["selftest_window_contains_nominal_setup_screen"])

    def test_allowances_widen_bounds_monotonically(self):
        base = screen(temperature_allowance=0, parasitic_pf=0, leakage_na=0)
        larger = screen()
        self.assertLess(larger["extended_screen_ms"][0], base["extended_screen_ms"][0])
        self.assertGreater(larger["extended_screen_ms"][1], base["extended_screen_ms"][1])

    def test_unphysical_inputs_are_rejected(self):
        for kwargs in ({"cap_nf": 0}, {"cap_nf": True}, {"cap_nf": math.nan},
                       {"leakage_na": 375}, {"leakage_na": -1},
                       {"parasitic_pf": -1}, {"tolerance": 1},
                       {"temperature_allowance": math.inf}, {"downstream_ms": -1}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                screen(**kwargs)

    def test_increased_downstream_delay_is_not_hidden(self):
        r = screen(downstream_ms=8)
        self.assertFalse(r["below_20ms_under_assumptions"])
        self.assertTrue(r["downstream_is_an_allocation_not_a_measurement"])

    def test_capacitor_effective_envelope_stays_in_datasheet_range(self):
        for kwargs in ({"cap_nf": .01}, {"cap_nf": .1}, {"cap_nf": 1000},
                       {"parasitic_pf": 1000000}):
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                screen(**kwargs)
        self.assertFalse(screen(cap_nf=.2)["manufacturing_ready"])


if __name__ == "__main__":
    unittest.main()
