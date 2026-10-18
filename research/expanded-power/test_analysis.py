"""Numerical failure-boundary checks, not hardware verification."""
import importlib.util
import math
import unittest
from pathlib import Path

spec = importlib.util.spec_from_file_location('expanded_power', Path(__file__).with_name('analyze.py'))
model = importlib.util.module_from_spec(spec)
spec.loader.exec_module(model)


class ArithmeticBoundaries(unittest.TestCase):
    def test_input_power_balances_load_and_path_loss(self):
        i = model.input_current(35, efficiency=.85, auxiliary=.065, voltage=19, resistance=.2)
        delivered = (i - .065) * (19 - .2*i) * .85
        self.assertAlmostEqual(delivered, 35, places=10)

    def test_bad_or_impossible_input_is_rejected(self):
        for power in (False, -1, 0, math.nan, math.inf):
            with self.subTest(power=power), self.assertRaises(ValueError):
                model.input_current(power)
        with self.assertRaises(ValueError):
            model.input_current(10000)

    def test_esr_impossible_case_is_explicit_not_negative_capacitance(self):
        row = model.unload(10, 2, target=5.15)
        self.assertFalse(row['finite_cap_can_meet_target_with_fixed_ripple_and_esr'])
        self.assertIsNone(row['required_effective_cap_f'])
        self.assertFalse(row['passes_upper_voltage_arithmetic_only'])

    def test_phase_peak_never_uses_average_load_energy(self):
        row = model.unload(6, 3, target=5.15)
        for corner in row['phase_corners']:
            self.assertGreater(corner['twice_inductor_energy_j'], corner['inductance_h'] * 6**2)

    def test_full10a_needs_three_bulk_for_revised_upper_bound(self):
        self.assertFalse(model.unload(10, 2)['passes_upper_voltage_arithmetic_only'])
        self.assertTrue(model.unload(10, 3)['passes_upper_voltage_arithmetic_only'])
        self.assertFalse(model.unload(10, 3)['production_or_stability_pass'])

    def test_more_storage_reduces_but_does_not_qualify_unload(self):
        a, b = model.unload(6.6, 2), model.unload(6.6, 3)
        self.assertLess(b['screen_max_v'], a['screen_max_v'])
        self.assertFalse(b['production_or_stability_pass'])


if __name__ == '__main__':
    unittest.main()
