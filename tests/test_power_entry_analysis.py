"""Fault-inject the assumptions and boundaries of the power-entry calculation."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("power_entry_analysis", ROOT/"tools/power_entry_analysis.py")
analysis = importlib.util.module_from_spec(spec)
spec.loader.exec_module(analysis)


class PowerEntryAnalysisTests(unittest.TestCase):
    def setUp(self):
        self.req = json.loads((ROOT/"hardware/power_entry/requirements.json").read_text())
        self.ledger = json.loads((ROOT/"hardware/electrical-design.json").read_text())

    def run_case(self):
        return analysis.analyze(self.req, self.ledger)

    def test_current_design_is_calculable_but_not_qualified(self):
        r = self.run_case()
        self.assertTrue(r["calculation_valid"], r["errors"])
        self.assertFalse(r["manufacturing_ready"])
        self.assertGreater(r["thresholds"]["uvlo_rise_v"][1], 18.7)
        self.assertLess(r["thresholds"]["uvlo_rise_v"][1], 19)
        self.assertGreater(r["branches"]["FIELD"]["assumed_low_limit_margin_a"], .05)
        self.assertLess(r["branches"]["FIELD"]["assumed_low_limit_margin_a"], .06)
        self.assertTrue(any("recovery" in x for x in r["issues"]))

    def test_ideal_network_reduces_to_analytic_divider(self):
        # A=8, B=1, C=1; no leakage/error: UV at6V, OV at12V.
        self.assertEqual(analysis.ladder_corners([8,1,1], 0, [1.2], 0, node="uv"), [6,6])
        self.assertEqual(analysis.ladder_corners([8,1,1], 0, [1.2], 0, node="ov"), [12,12])
        self.assertEqual(analysis.divider_corners(9,1,0,[1.2],0), [12,12])

    def test_wider_tolerance_never_shrinks_corners(self):
        for node in ("uv", "ov"):
            a = analysis.ladder_corners([887000,29400,34000],.001,[1.176,1.224],node=node)
            b = analysis.ladder_corners([887000,29400,34000],.005,[1.176,1.224],node=node)
            self.assertLess(b[0], a[0])
            self.assertGreater(b[1], a[1])

    def test_embedded_previous_results_are_not_an_authority(self):
        before = self.run_case()
        self.req["calculations"] = {"ovp_rise_v": [1,2], "core": {"ilim_screening_high_a": 99}}
        after = self.run_case()
        self.assertEqual(before, after)

    def test_all_nonfinite_and_boolean_current_inputs_rejected(self):
        for value in (float("nan"), float("inf"), -float("inf"), True, False, "4.36", None, 10**500):
            with self.subTest(value=repr(value)[:40]):
                self.req["branches"][1]["normal_load_a"] = value
                self.assertFalse(self.run_case()["calculation_valid"])

    def test_nan_hidden_in_unrelated_json_is_rejected(self):
        self.req["metadata"] = {"hidden": float("nan")}
        self.assertFalse(self.run_case()["calculation_valid"])

    def test_singular_or_negative_resistors_are_rejected(self):
        for value in (0, -100, False):
            with self.subTest(value=value):
                self.req["support_values"]["pgth_divider"]["pgth_to_gnd_ohm"] = value
                self.assertFalse(self.run_case()["calculation_valid"])

    def test_wrong_fet_polarity_and_gate_map_are_rejected(self):
        self.req["parts"]["Q1"]["source"] = "EFUSE_IN"
        self.assertFalse(self.run_case()["calculation_valid"])
        self.req["parts"]["Q1"]["source"] = "RAW_FUSED"
        self.req["parts"]["Q2"]["pins"]["2"] = "localGND"
        self.assertFalse(self.run_case()["calculation_valid"])

    def test_two_times_pulse_variant_cannot_reuse_analysis(self):
        self.req["parts"]["U1"]["mpn"] = "TPS26631RGER"
        self.assertFalse(self.run_case()["calculation_valid"])

    def test_ground_join_or_branch_duplication_rejected(self):
        self.req["branches"][1]["ground"] = "LOGIC_GND"
        self.assertFalse(self.run_case()["calculation_valid"])
        self.req["branches"][1]["ground"] = "FIELD_GND"
        self.req["branches"][1]["id"] = "CORE"
        self.assertFalse(self.run_case()["calculation_valid"])

    def test_restoring_old18v_envelope_reports_converter_undervoltage(self):
        self.req["proposed_draft_envelope"]["entry_voltage_v"][0] = 18
        r = self.run_case()
        self.assertTrue(r["calculation_valid"])
        self.assertTrue(any("below existing18V" in x for x in r["issues"]))

    def test_old2a_source_cannot_pass_upper_current_screen(self):
        self.req["proposed_draft_envelope"]["core_qualified_source_and_wiring_capacity_target_a"] = 2
        r = self.run_case()
        self.assertTrue(any("CORE: proposed source/path capacity" in x for x in r["issues"]))

    def test_ledger_load_change_invalidates_frozen_budget(self):
        for row in self.ledger["power_loads"]:
            if row["id"] == "field_outputs":
                row["budget_a"] += .1
        self.assertFalse(self.run_case()["calculation_valid"])
        self.req["branches"][1]["normal_load_a"] += .1
        r = self.run_case()
        self.assertTrue(r["calculation_valid"], r["errors"])
        self.assertTrue(any("FIELD: assumed minimum limiter" in x for x in r["issues"]))

    def test_unwarranted_accuracy_or_certainty_rejected(self):
        self.req["support_values"]["rilim"]["current_tolerance_assumption_fraction"] = .07
        self.assertFalse(self.run_case()["calculation_valid"])
        self.req["support_values"]["rilim"]["current_tolerance_assumption_fraction"] = .1
        self.req["support_values"]["rilim"]["assumption_not_guaranteed_at_selected_r"] = False
        self.assertFalse(self.run_case()["calculation_valid"])

    def test_double_capacitance_doubles_charge_but_not_ramp(self):
        before = self.run_case()["startup"]
        self.req["support_values"]["decoupling"]["total_output_capacitance_max_f"] *= 2
        after = self.run_case()["startup"]
        self.assertEqual(after["rise_to_max_input_ms"], before["rise_to_max_input_ms"])
        self.assertAlmostEqual(after["capacitive_peak_a"], before["capacitive_peak_a"]*2)
        self.assertAlmostEqual(after["stored_energy_j"], before["stored_energy_j"]*2)

    def test_cli_overflow_literal_and_wrong_root_fail_structurally(self):
        with tempfile.TemporaryDirectory() as tmp:
            req = Path(tmp)/"input.json"
            for text in ('{"unexpected":1e999}', '[]', 'not json'):
                req.write_text(text)
                p = subprocess.run([sys.executable, str(ROOT/"tools/power_entry_analysis.py"),
                                    "--requirements", str(req)], capture_output=True, text=True)
                self.assertEqual(p.returncode, 1, p.stderr)
                payload = json.loads(p.stdout)
                self.assertFalse(payload["calculation_valid"])
                self.assertFalse(payload["manufacturing_ready"])


if __name__ == "__main__":
    unittest.main()
