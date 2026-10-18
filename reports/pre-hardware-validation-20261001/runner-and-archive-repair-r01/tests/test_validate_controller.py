"""Evidence boundaries for the disconnected bench, using real command failures."""
from pathlib import Path
import importlib.util
import json
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("controller_pre_hardware_bench", ROOT / "tools/validate_controller.py")
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class EvidenceBoundaryTests(unittest.TestCase):
    def test_failure_dominates_blocked_and_success(self):
        rows = [bench.stage("a", "HOST", "PASS", ""), bench.stage("b", "RTL", "BLOCKED", "")]
        self.assertEqual(bench.result_status(rows, True), "BLOCKED")
        rows.append(bench.stage("c", "NATIVE", "FAIL", ""))
        self.assertEqual(bench.result_status(rows, True), "FAIL")
        self.assertEqual(bench.result_status(rows, False), "FAIL")

    def test_inventory_does_not_claim_executed_bench(self):
        self.assertEqual(bench.result_status(bench.required_blockers(), False), "NOT_RUN")
        self.assertEqual(bench.result_status(bench.required_blockers(), True), "BLOCKED")
        for row in bench.required_blockers():
            self.assertFalse(row["hardware_qualified"])
            self.assertFalse(row["physical_hardware_connected"])
        names = {r["name"] for r in bench.required_blockers()}
        self.assertTrue({"cnc3_actual_rtl_transport", "twelve_joint_simultaneous_machine",
                         "critical_circuit_spice_corners", "efinity_vendor_fit_timing",
                         "physical_qualification"}.issubset(names))

    def test_reject_unknown_status(self):
        with self.assertRaises(ValueError):
            bench.stage("fake", "hardware", "probably", "")

    def test_no_simulator_means_no_numerical_ratings(self):
        value = bench.characterization([], "source", "board")
        self.assertFalse(value["manufacturing_ready"])
        self.assertFalse(value["simulation_is_hardware_qualification"])
        for row in value["entries"]:
            self.assertIsNone(row["hardware_qualified_limit"])
            self.assertIsNone(row["conservative_provisional_product_rating"])
            self.assertIsNone(row["measured_simulated_failure_limit"])

    def test_standalone_rtl_is_not_twelve_axis_machine_or_product_rating(self):
        receipt = {"status": "PASS", "source_hashes_unchanged": True,
                   "profiles": [{"name": "12_12", "first_adversarial_failure_hz": 2000000.001,
                                 "design_pulse_ceiling_hz": 1999999.990}]}
        value = bench.characterization([], "source", "board", receipt)
        row = value["entries"][-1]
        self.assertEqual(row["limit_class"], "SIMULATED LIMIT")
        self.assertFalse(row["CNC3_full_machine"])
        self.assertIsNone(row["conservative_provisional_product_rating"])
        self.assertIsNone(row["hardware_qualified_limit"])
        self.assertFalse(value["requested_motion_target"]["qualified"])

    def test_failed_or_changed_rtl_cannot_supply_simulated_limit(self):
        for receipt in ({"status": "FAIL", "source_hashes_unchanged": True},
                        {"status": "PASS", "source_hashes_unchanged": False}):
            with self.assertRaises(ValueError):
                bench.characterization([], "source", "board", receipt)

    def test_design_current_limit_not_thermal_or_physical_qualification(self):
        contract = {"continuous_limit_a_per_channel": 0.5, "continuous_limit_a_per_quad": 2.0,
                    "source_sha256": "a" * 64}
        value = bench.characterization([], "source", "board", do_contract=contract)
        self.assertEqual([r["configured_design_limit_a"] for r in value["entries"][-2:]], [0.5, 2.0])
        for row in value["entries"][-2:]:
            self.assertEqual(row["limit_class"], "DESIGN LIMIT")
            self.assertIsNone(row["hardware_qualified_limit"])
            self.assertEqual(row["source_contract_sha256"], "a" * 64)


class ActualExecutionTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name)

    def run_case(self, script, name="case", **kwargs):
        return bench.command_stage(name, "HOST_FIXTURE", [sys.executable, "-c", script], self.path,
                                   cwd=self.path, **kwargs)

    def test_literal_argv_and_exact_log_hash(self):
        text = "$(never_run_this) `literal` ; $HOME"
        result = bench.execute([sys.executable, "-c", "import sys;print(sys.argv[1])", text],
                               self.path / "literal", cwd=self.path)
        self.assertEqual(result["exit_code"], 0)
        self.assertEqual(Path(result["log"]).read_text().strip(), text)
        self.assertEqual(result["log_sha256"], bench.sha(result["log"]))

    def test_real_nonzero_exit_is_failed(self):
        result = self.run_case("raise SystemExit(7)")
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["execution"]["exit_code"], 7)

    def test_missing_receipt_after_zero_exit_is_failed(self):
        result = self.run_case("pass", artifact=self.path / "absent.json")
        self.assertEqual(result["status"], "FAIL")
        self.assertTrue(result["missing_artifact"])

    def test_malformed_receipt_after_zero_exit_is_failed(self):
        artifact = self.path / "malformed.json"
        artifact.write_text("{broken")
        result = self.run_case("pass", artifact=artifact)
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("artifact_error", result)

    def test_negative_receipt_is_failed_even_when_command_passes(self):
        artifact = self.path / "negative.json"
        artifact.write_text(json.dumps({"passed": False}))
        result = self.run_case("pass", artifact=artifact, predicate=lambda v: v["passed"])
        self.assertEqual(result["status"], "FAIL")
        self.assertEqual(result["artifact_sha256"], bench.sha(artifact))

    def test_wrong_receipt_schema_is_failed(self):
        artifact = self.path / "wrong-schema.json"
        artifact.write_text("{}")
        result = self.run_case("pass", artifact=artifact, predicate=lambda v: v["passed"])
        self.assertEqual(result["status"], "FAIL")
        self.assertIn("artifact_error", result)

    def test_actual_timeout_is_failed(self):
        result = self.run_case("import time;time.sleep(10)", timeout=0.05)
        self.assertEqual(result["status"], "FAIL")
        self.assertIsNone(result["execution"]["exit_code"])
        self.assertTrue(result["execution"]["error"])

    def test_evidence_cannot_overwrite_prior_or_escape_reports(self):
        reports = self.path / "reports"
        original = bench.fresh_output(reports / "first", self.path)
        (original / "old.json").write_text("immutable")
        with self.assertRaises(ValueError):
            bench.fresh_output(original, self.path)
        with self.assertRaises(ValueError):
            bench.fresh_output(self.path / "elsewhere", self.path)
        self.assertEqual((original / "old.json").read_text(), "immutable")

    def test_source_mutation_detection_includes_new_and_deleted_inputs(self):
        (self.path / "hardware").mkdir()
        src = self.path / "hardware/source.json"
        src.write_text("original")
        before = bench.snapshot(self.path)
        src.write_text("changed")
        (self.path / "hardware/added.json").write_text("new")
        delta = bench.differences(before, bench.snapshot(self.path))
        self.assertEqual(set(delta), {"hardware/source.json", "hardware/added.json"})
        src.unlink()
        self.assertIsNone(bench.differences(before, bench.snapshot(self.path))["hardware/source.json"]["after"])


if __name__ == "__main__":
    unittest.main()
