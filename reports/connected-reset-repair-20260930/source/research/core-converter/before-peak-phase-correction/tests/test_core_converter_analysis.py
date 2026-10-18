import copy
import importlib.util
import json
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("core_converter_analysis", ROOT / "tools/core_converter_analysis.py")
MOD = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MOD)


class CoreConverterAnalysis(unittest.TestCase):
    def setUp(self):
        self.req = json.loads((ROOT / "hardware/core_converter/requirements.json").read_text())

    def test_series_drop_is_solved_not_ignored(self):
        current = MOD.input_current(19, 0.2, 30.3, 0.85, 0.065)
        self.assertAlmostEqual((current - 0.065) * (19 - 0.2 * current) * 0.85, 30.3, places=10)
        self.assertGreater(current, 30.3 / (19 * 0.85) + 0.065)

    def test_no_static_operating_point_is_rejected(self):
        with self.assertRaises(ValueError):
            MOD.input_current(5, 10, 30, 0.85, 0)

    def test_fault_and_transient_failures_remain_visible(self):
        data = MOD.analyze(self.req)
        self.assertTrue(data["entry"]["operating_cases"]["encoder_fault"]["fits6a"])
        self.assertFalse(data["entry"]["operating_cases"]["unsequenced_all_loads_start"]["fits6a"])
        self.assertTrue(data["entry"]["operating_cases"]["main_charge_host_off_encoder_faults"]["fits6a"])
        self.assertTrue(data["entry"]["operating_cases"]["host_start_after_main_charge"]["fits6a"])
        self.assertTrue(data["transient_regulation"]["full6a_unload_pass"])
        self.assertFalse(data["production_qualified"])

    def test_limit_or_efficiency_reduction_cannot_keep_false_pass(self):
        self.req["design_envelope"]["efficiency_screening_floor"] = 0.65
        data = MOD.analyze(self.req)
        self.assertFalse(data["entry"]["operating_cases"]["rated6a"]["fits_screened_entry_minimum"])

    def test_stored_results_are_ignored(self):
        expected = MOD.analyze(self.req)
        self.req["results"] = {"production_qualified": True, "full6a_unload_pass": True}
        self.assertEqual(MOD.analyze(self.req), expected)

    def test_unsafe_numeric_operands(self):
        for bad in (True, float("nan"), float("inf"), -1, "0.85", 10 ** 10000):
            with self.subTest(value=type(bad).__name__):
                req = copy.deepcopy(self.req)
                req["design_envelope"]["efficiency_screening_floor"] = bad
                with self.assertRaises(ValueError):
                    MOD.analyze(req)

    def test_wrong_device_cannot_borrow_higher_current(self):
        self.req["converter"]["mpn"] = "LM706A0RRXR"
        with self.assertRaises(ValueError):
            MOD.analyze(self.req)

    def test_wrong_magnetics_are_rejected(self):
        self.req["passives"][0]["mpn"] = "XGL6060-472MEC"
        with self.assertRaises(ValueError):
            MOD.analyze(self.req)

    def test_unsorted_range_and_zero_cap_are_rejected(self):
        for key, value in (("whole_controller_input_v_proposed", [30, 19]), ("output_effective_capacitance_f_assumed", 0), ("soft_start_time_s", [0.0044, 0.0028, 0.0019])):
            req = copy.deepcopy(self.req)
            req["design_envelope"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                MOD.analyze(req)

    def test_added_load_and_capacitance_change_actual_results(self):
        base = MOD.analyze(self.req)
        self.req["design_envelope"]["sequenced_sbc"]["bulk_count"] *= 2
        self.req["design_envelope"]["simultaneous_encoder_limited_fault_current_a"] += 0.3
        revised = MOD.analyze(self.req)
        self.assertFalse(revised["entry"]["operating_cases"]["main_charge_host_off_encoder_faults"]["fits6a"])
        self.assertGreater(revised["entry"]["operating_cases"]["encoder_fault"]["input_current_a"], base["entry"]["operating_cases"]["encoder_fault"]["input_current_a"])

    def test_historical_failure_is_preserved_and_reproducible(self):
        old=json.loads((ROOT/'research/core-converter/before-sbc-sequencing/hardware/core_converter/requirements.json').read_text())
        result=MOD.analyze(old)
        self.assertFalse(result['transient_regulation']['full6a_unload_pass'])
        self.assertFalse(result['entry']['operating_cases']['startup_with_encoder_fault']['fits6a'])

    def test_esr_cannot_make_negative_capacitance_or_divide_by_zero(self):
        for esr in (0.5/6,0.2):
            req=copy.deepcopy(self.req)
            req['design_envelope']['sequenced_sbc']['capacitor_interconnect_esr_ohm_max']=esr
            with self.subTest(esr=esr),self.assertRaises(ValueError):MOD.analyze(req)

    def test_unqualified_high_esr_cannot_claim_transient_pass(self):
        self.req['design_envelope']['sequenced_sbc']['capacitor_interconnect_esr_ohm_max']=.002
        result=MOD.analyze(self.req)
        self.assertFalse(result['transient_regulation']['full6a_unload_pass'])


if __name__ == "__main__":
    unittest.main()
