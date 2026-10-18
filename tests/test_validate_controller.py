"""Evidence boundaries for the disconnected bench, using real command failures."""
from pathlib import Path
import importlib.util
import json
import sys
import tempfile
import unittest
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("controller_pre_hardware_bench", ROOT / "tools/validate_controller.py")
bench = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bench)


class EvidenceBoundaryTests(unittest.TestCase):
    def seeded_fixture(self):
        value = {"status": "PASS", "failure": None, "inputs_unchanged": True,
            "seed": "0x434e4333", "requested_trials": 1024, "completed_trials": 1024,
            "cases": [{"trial": i, "kind": i % 8, "checks": 57, "inhibit_cycles": 250000,
                       "passed": True} for i in range(1024)],
            "independently_decoded_responses": 21120,
            "response_sha256": {f"responses-{i}.txt": "a" * 64 for i in range(1024)},
            "input_sha256": {"source": "b" * 64},
            "precompile_input_sha256": {str(i): "c" * 64 for i in range(15)},
            "generated_sha256": {"actual.cpp": "d" * 64},
            "executions": [{"exit_code": 0} for _ in range(3)]}
        value.update({k: True for k in ("actual_SPI_and_motion_RTL",
            "ideal_power_permission_and_mechanics", "post_fault_correct_UPDATE_restart_rejected",
            "all_twelve_real_pins_exercised")})
        value.update({k: False for k in ("actual_LinuxCNC_HAL", "complete22fault_electrical_suite",
            "complete_nine_machine_suite", "physical20ms_qualified", "manufacturing_ready")})
        return value

    def test_seeded_faults_require_all_trials_all_classes_and_actual_response_records(self):
        value = self.seeded_fixture()
        self.assertTrue(bench.seeded_spi_accept(value))
        for delta in ({"completed_trials": 1023}, {"requested_trials": True},
                      {"cases": value["cases"][:-1]}, {"cases": [value["cases"][0]] * 1024},
                      {"response_sha256": {}}, {"precompile_input_sha256": {}},
                      {"executions": [{"exit_code": 1}] * 3}, {"independently_decoded_responses": 19},
                      {"inputs_unchanged": False}, {"generated_sha256": {}}):
            with self.subTest(delta=list(delta)):
                self.assertFalse(bench.seeded_spi_accept(dict(value, **delta)))
        for delta in ({"kind": 9}, {"inhibit_cycles": 250002}, {"checks": 56}, {"passed": False}):
            changed = dict(value, cases=[dict(value["cases"][0], **delta)] + value["cases"][1:])
            self.assertFalse(bench.seeded_spi_accept(changed))

    def test_seeded_faults_do_not_claim_HAL_whole_machine_or_physical_safety(self):
        value = self.seeded_fixture()
        for key in ("actual_LinuxCNC_HAL", "complete22fault_electrical_suite",
                    "complete_nine_machine_suite", "physical20ms_qualified", "manufacturing_ready"):
            self.assertFalse(bench.seeded_spi_accept(dict(value, **{key: True})))
        self.assertFalse(bench.seeded_spi_accept(dict(value, post_fault_correct_UPDATE_restart_rejected=False)))

    def test_missing_seeded_compiler_never_reuses_old_evidence(self):
        with tempfile.TemporaryDirectory() as temp:
            row = bench.run_seeded_spi_stage(Path(temp), {}, "unavailable")
            self.assertEqual(row["status"], "BLOCKED")
            self.assertEqual(list(Path(temp).iterdir()), [])

    def stateful_fixture(self):
        flags = {k: False for k in ("actual_physical_SPI_wire", "real_LinuxCNC_HAL",
            "full_CNC3_CAP3_pages_IOL1_events_output_chain", "complete_machine_or_vendor_T20_fit_timing",
            "physical_safety_or_new_ratings", "standalone_experimental_2MHz_authorized_runtime",
            "request_backpressure_queue_in_motion_scope")}
        flags.update(actual_simulated_SPI_edges_and_CRC=True, ideal_provider_inputs=True)
        return {"status": "PASS", "input_integrity": True, "inputs_unchanged": True,
            "counts": {"PASS": 11, "FAIL": 0, "BLOCKED": 0, "NOT_RUN": 0},
            "scope_flags": flags, "protocol_rate_max": 0x01000000,
            "exact_inputs": {"fixture": "a" * 64}, "bundle_manifest_sha256": "b" * 64,
            "stages": [{"name": n, "status": "PASS", "exit_code": 0, "receipt_sha256": "c" * 64}
                       for n in sorted(bench.STATEFUL_STAGES)]}

    def test_partial_stateful_passes_cannot_close_missing_stage(self):
        value = self.stateful_fixture()
        self.assertTrue(bench.stateful_accept(value))
        for delta in ({"status": "FAIL"}, {"input_integrity": False}, {"inputs_unchanged": False},
                      {"stages": value["stages"][:-1]}, {"stages": [value["stages"][0]] * 11},
                      {"protocol_rate_max": 0x7fffffff}, {"exact_inputs": {}},
                      {"counts": {"PASS": 10, "FAIL": 0, "BLOCKED": 1, "NOT_RUN": 0}}):
            with self.subTest(delta=delta):
                self.assertFalse(bench.stateful_accept(dict(value, **delta)))
        value["stages"][0]["exit_code"] = 1
        self.assertFalse(bench.stateful_accept(value))

    def test_stateful_simulation_never_claims_HAL_or_electrical_qualification(self):
        value = self.stateful_fixture()
        for name in value["scope_flags"]:
            changed = dict(value, scope_flags=dict(value["scope_flags"]))
            changed["scope_flags"][name] = not changed["scope_flags"][name]
            with self.subTest(flag=name):
                self.assertFalse(bench.stateful_accept(changed))

    def test_stateful_bundle_paths_cannot_escape_frozen_inputs(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            bundle = root / bench.STATEFUL_BUNDLE
            bundle.mkdir(parents=True)
            (bundle / "bundle-manifest.json").write_text(json.dumps({"files": {"../../foreign.v": "a" * 64}}))
            with self.assertRaises(ValueError):
                bench.stateful_inputs(root)

    def test_missing_stateful_compilers_do_not_reuse_old_receipts(self):
        with tempfile.TemporaryDirectory() as temp:
            row = bench.run_stateful_stage(Path(temp), {}, "unavailable")
            self.assertEqual(row["status"], "BLOCKED")
            self.assertEqual(list(Path(temp).iterdir()), [])

    def spi_fixture(self):
        checks = {k: True for k in ("actual_stopped_outputs", "all_twelve_pin_counts",
            "actual_encoder_waveform_drained", "actual_digital_analog_sources_unavailable",
            "four_actual_position_encoders", "continuity_preserved_after_clean_stop",
            "fault_continuity_invalid", "physical_encoder_differs_from_step_command",
            "hardware_counter_reset_is_not_mechanical_home")}
        return {"status": "PASS", "source_unchanged": True, "actual_FPGA_integration": True,
            "behavioral_FPGA_substitution": False, "actual_LinuxCNC_integration": False,
            "complete_nine_machine_suite": False, "complete_safety_chain": False,
            "physical_qualified": False, "manufacturing_ready": False, "gaps": ["ideal providers"],
            "post_fault_correct_UPDATE_restart_rejected": True,
            "input_sha256": {"fixture": "a" * 64},
            "cases": [{"scenario": name, "passed": True, "fixture_assertions": 65,
                       "checks": dict(checks)} for name in sorted(bench.SPI_PLANT_SCENARIOS)]}

    def test_actual_spi_plant_does_not_authorize_hardware_or_full_machine(self):
        value = self.spi_fixture()
        self.assertTrue(bench.spi_plant_accept(value))
        for delta in ({"status": "FAIL"}, {"source_unchanged": False},
            {"actual_FPGA_integration": False}, {"behavioral_FPGA_substitution": True},
            {"actual_LinuxCNC_integration": True}, {"complete_nine_machine_suite": True},
            {"complete_safety_chain": True}, {"physical_qualified": True},
            {"manufacturing_ready": True}, {"post_fault_correct_UPDATE_restart_rejected": False},
            {"gaps": []}, {"input_sha256": {}}):
            with self.subTest(delta=delta):
                self.assertFalse(bench.spi_plant_accept(dict(value, **delta)))

    def test_actual_spi_missing_fault_or_count_reconciliation_is_rejected(self):
        value = self.spi_fixture()
        self.assertFalse(bench.spi_plant_accept(dict(value, cases=value["cases"][:-1])))
        self.assertFalse(bench.spi_plant_accept(dict(value, cases=[value["cases"][0]] * 9)))
        for flag in ("all_twelve_pin_counts", "physical_encoder_differs_from_step_command",
                     "fault_continuity_invalid", "hardware_counter_reset_is_not_mechanical_home"):
            value = self.spi_fixture()
            for row in value["cases"]:
                row["checks"].pop(flag)
            self.assertFalse(bench.spi_plant_accept(value))
        value = self.spi_fixture()
        value["cases"][0]["checks"]["all_twelve_pin_counts"] = False
        self.assertFalse(bench.spi_plant_accept(value))

    def test_actual_spi_missing_compiler_does_not_reuse_old_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            row = bench.run_spi_plant_stage(Path(temp), {}, "unavailable")
            self.assertEqual(row["status"], "BLOCKED")
            self.assertEqual(list(Path(temp).iterdir()), [])

    def iol1_fixture(self):
        flags = {k: False for k in ("actual_ARM_DMA_IRQ_or_ADC", "commercial_ACTIVE_or_factory_identity",
            "outputs_ARM_CAP3_HAL", "full_machine_or_vendor_T20_fit_timing", "physical_qualification_or_new_ratings")}
        flags["actual_simulated_four_lane_SPI_and_same_C_protocol"] = True
        return {"status": "PASS", "bundle_integrity": True, "inputs_unchanged": True,
            "counts": {"PASS": 4, "FAIL": 0, "BLOCKED": 0, "NOT_RUN": 0},
            "scope_flags": flags, "exact_inputs": {"fixture": "a" * 64},
            "bundle_manifest_sha256": "b" * 64, "open_dependencies": ["actual ADC"],
            "stages": [{"name": n, "status": "PASS", "exit_code": 0, "receipt_sha256": "c" * 64}
                       for n in sorted(bench.IOL1_STAGES)]}

    def test_iol1_missing_or_duplicate_stage_is_rejected(self):
        value = self.iol1_fixture()
        self.assertTrue(bench.iol1_acquisition_accept(value))
        for delta in ({"status": "FAIL"}, {"bundle_integrity": False}, {"inputs_unchanged": False},
                      {"stages": value["stages"][:-1]}, {"stages": [value["stages"][0]] * 4},
                      {"exact_inputs": {}}, {"open_dependencies": []},
                      {"counts": {"PASS": 3, "FAIL": 0, "BLOCKED": 1, "NOT_RUN": 0}}):
            with self.subTest(delta=delta):
                self.assertFalse(bench.iol1_acquisition_accept(dict(value, **delta)))
        value["stages"][0]["exit_code"] = 1
        self.assertFalse(bench.iol1_acquisition_accept(value))

    def test_iol1_acquisition_cannot_claim_active_outputs_or_hardware(self):
        value = self.iol1_fixture()
        for name in value["scope_flags"]:
            changed = dict(value, scope_flags=dict(value["scope_flags"]))
            changed["scope_flags"][name] = not changed["scope_flags"][name]
            with self.subTest(flag=name):
                self.assertFalse(bench.iol1_acquisition_accept(changed))

    def test_iol1_missing_compiler_does_not_reuse_old_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            row = bench.run_iol1_acquisition_stage(Path(temp), {}, "unavailable")
            self.assertEqual(row["status"], "BLOCKED")
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_is2_discovery_requires_every_runtime_mutation_and_frozen_bundle(self):
        value = {"status": "PASS", "bundle_integrity": True, "inputs_unchanged": True,
            "counts": {"PASS": 5, "FAIL": 0, "BLOCKED": 0, "NOT_RUN": 0},
            "bundle_manifest_sha256": bench.IS2_MANIFEST_SHA, "exact_inputs": {"fixture": "a" * 64},
            "open_dependencies": ["actual providers"], "scope_flags": {
                "actual_compiled_C_to_actual_simulated_RTL_SPI_CAP3": True,
                "explicit_IS2_integrated12_class0_four_encoder_inventory": True,
                "PROFILE_COMPLETE": False, "ACTUAL_physical_providers_identity_or_full_output_authority": False,
                "commissioning_ARM_12joint_HAL_physical_qualification": False,
                "product_rate_frame_layout_shared_sources_changed": False},
            "stages": [{"name": n, "status": "PASS", "exit_code": 0, "receipt_sha256": "b" * 64}
                       for n in sorted(bench.IS2_STAGES)]}
        self.assertTrue(bench.is2_profile_accept(value))
        for delta in ({"stages": value["stages"][:-1]}, {"stages": [value["stages"][0]] * 5},
                      {"inputs_unchanged": False}, {"bundle_manifest_sha256": "c" * 64},
                      {"exact_inputs": {}}, {"open_dependencies": []}):
            with self.subTest(delta=delta):
                self.assertFalse(bench.is2_profile_accept(dict(value, **delta)))
        for key in value["scope_flags"]:
            flags = dict(value["scope_flags"])
            flags[key] = not flags[key]
            with self.subTest(flag=key):
                self.assertFalse(bench.is2_profile_accept(dict(value, scope_flags=flags)))
        value["stages"][0]["exit_code"] = 1
        self.assertFalse(bench.is2_profile_accept(value))

    def test_is2_missing_compiler_never_reuses_old_receipt(self):
        with tempfile.TemporaryDirectory() as temp:
            row = bench.run_is2_profile_stage(Path(temp), {}, "unavailable")
            self.assertEqual(row["status"], "BLOCKED")
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_isolated_mechanics_cannot_claim_integrated_machine(self):
        value = {"status": "PASS", "source_unchanged": True,
                 "actual_FPGA_integration": False, "actual_LinuxCNC_integration": False,
                 "complete_nine_machine_suite": False, "physical_qualified": False,
                 "manufacturing_ready": False, "baseline_checks": 1114,
                 "compiled_negative_controls": 12,
                 "cases": [{"name": str(i), "passed": True} for i in range(13)],
                 "input_sha256": {"source": "a" * 64}}
        self.assertTrue(bench.isolated_plant_accept(value))
        for delta in ({"status": "FAIL"}, {"source_unchanged": False},
                      {"actual_FPGA_integration": True}, {"actual_LinuxCNC_integration": True},
                      {"complete_nine_machine_suite": True}, {"physical_qualified": True},
                      {"manufacturing_ready": True}, {"compiled_negative_controls": 0},
                      {"baseline_checks": 3}, {"cases": [{"name": "duplicated", "passed": True}] * 13},
                      {"input_sha256": {}}):
            with self.subTest(delta=delta):
                self.assertFalse(bench.isolated_plant_accept(dict(value, **delta)))
        self.assertEqual(next(s for s in bench.required_blockers()
                              if s["name"] == "twelve_joint_simultaneous_machine")["status"], "BLOCKED")

    def test_missing_plant_compiler_cannot_reuse_old_pass(self):
        with tempfile.TemporaryDirectory() as temp:
            value = bench.run_isolated_plant_stage(Path(temp), {}, "unavailable")
            self.assertEqual(value["status"], "BLOCKED")
            self.assertEqual(list(Path(temp).iterdir()), [])

    def test_partial_analog_result_cannot_close_missing_chain(self):
        value = {"passed": True, "source_unchanged": True, "whole_analog_chain_passed": False,
                 "physical_qualified": False, "manufacturing_ready": False,
                 "cases": [{"passed": True}] * 12, "source_channels": [0, 1, 2, 3],
                 "scope": "Actual manufacturer buffer model; ideal upstream and approximate ADC",
                 "input_sha256": {"source": "a" * 64}}
        self.assertTrue(bench.partial_spice_accept(value, 12))
        for delta in ({"whole_analog_chain_passed": True}, {"physical_qualified": True},
                      {"manufacturing_ready": True}, {"source_unchanged": False},
                      {"cases": [{"passed": True}] * 11}, {"cases": [{"passed": False}] * 12},
                      {"source_channels": [0]}, {"input_sha256": {}}, {"passed": False}):
            with self.subTest(delta=delta):
                self.assertFalse(bench.partial_spice_accept(dict(value, **delta), 12))
        self.assertEqual(next(s for s in bench.required_blockers()
                              if s["name"] == "critical_circuit_spice_corners")["status"], "BLOCKED")

    def test_missing_simulator_does_not_replay_old_analog_receipts(self):
        with tempfile.TemporaryDirectory() as temp:
            rows = bench.run_partial_spice_stages(Path(temp), {}, "unavailable")
            self.assertEqual([r["status"] for r in rows], ["BLOCKED", "BLOCKED"])
            self.assertEqual(list(Path(temp).iterdir()), [])

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

    def test_orphan_and_native_independent_count_mismatch_are_failed(self):
        healthy = {"source_net_checks_pass": True, "complete_source_population_pass": True,
                   "orphan_copper_items": [], "uncapped_unconnected_ratsnest_edges": 12,
                   "independent_physical_cluster_missing_joins": 12}
        self.assertTrue(bench.connectivity_integrity(healthy))
        for delta in ({"orphan_copper_items": ["actual-orphan-uuid"]},
                      {"uncapped_unconnected_ratsnest_edges": 13},
                      {"source_net_checks_pass": False},
                      {"complete_source_population_pass": False},
                      {"uncapped_unconnected_ratsnest_edges": -1, "independent_physical_cluster_missing_joins": -1},
                      {"uncapped_unconnected_ratsnest_edges": True, "independent_physical_cluster_missing_joins": True}):
            with self.subTest(delta=delta):
                self.assertFalse(bench.connectivity_integrity(dict(healthy, **delta)))

    def test_zero_join_does_not_hide_failed_source_integrity(self):
        value = {"independent_physical_cluster_missing_joins": 0}
        failed = bench.stage("source_physical_connectivity", "NATIVE", "FAIL", "orphan")
        self.assertEqual(bench.full_route_stage(value, failed)["status"], "FAIL")
        good = bench.stage("source_physical_connectivity", "NATIVE", "PASS", "")
        self.assertEqual(bench.full_route_stage(value, good)["status"], "PASS")
        self.assertEqual(bench.full_route_stage({"independent_physical_cluster_missing_joins": 20}, good)["status"], "BLOCKED")

    def test_native_erc_nested_sheet_error_and_ignored_checks_are_rejected(self):
        healthy = {"ignored_checks": [], "sheets": [{"path": "/", "violations": []},
                   {"path": "/actual-child/", "violations": [{"severity": "warning"}]}]}
        self.assertTrue(bench.native_erc_accept(healthy))
        self.assertEqual(len(bench.native_violations(healthy, "ERC")), 1)
        bad = dict(healthy, sheets=healthy["sheets"] + [{"path": "/late-child/", "violations": [{"severity": "error"}]}])
        self.assertFalse(bench.native_erc_accept(bad))
        self.assertFalse(bench.native_erc_accept(dict(healthy, ignored_checks=["pin_to_pin"])))
        excluded = dict(healthy, sheets=[{"violations": [{"severity": "exclusion"}]}])
        self.assertFalse(bench.native_erc_accept(excluded))
        for malformed in ({"ignored_checks": [], "violations": []}, {"ignored_checks": [], "sheets": []}):
            with self.subTest(malformed=malformed), self.assertRaises((ValueError, KeyError)):
                bench.native_erc_accept(malformed)


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

    def test_real_copy_retains_nested_relative_paths_and_original_bytes(self):
        source, dest = self.path / "original", self.path / "copy"
        (source / "src").mkdir(parents=True)
        (source / "evidence").mkdir()
        (source / "src/startup.S").write_bytes(b"actual source bytes\n")
        (source / "evidence/historical.json").write_bytes(b"historical untouched\n")
        result = bench.copied_tree(source, dest)
        self.assertEqual(result, {"src/startup.S": bench.sha(source / "src/startup.S")})
        self.assertEqual((dest / "src/startup.S").read_bytes(), (source / "src/startup.S").read_bytes())
        self.assertEqual((source / "evidence/historical.json").read_bytes(), b"historical untouched\n")
        self.assertFalse((dest / "evidence").exists())

    def test_compiler_tables_research_notes_and_primary_inputs_are_hashed(self):
        names = ("firmware/startup.S", "firmware/stm32.ld", "firmware/template.in",
                 "hardware/fp-lib-table", "research/user-notes/request.txt", "research/primary.pdf")
        for name in names:
            p = self.path / name
            p.parent.mkdir(parents=True, exist_ok=True)
            p.write_bytes(b"engineering input")
        self.assertEqual(set(bench.snapshot(self.path)), set(names))

    def test_staging_exception_leaves_an_explicit_failed_completion_record(self):
        out = self.path / "exception"
        out.mkdir()
        bench.write(out / "source-before.json", {})
        with patch.dict(bench.CONTEXT, {"output": out, "stage": "actual_copy"}, clear=True), \
             patch.object(bench, "main", side_effect=ValueError("actual staging failure")), \
             patch.object(bench, "snapshot", return_value={}):
            self.assertEqual(bench.guarded_main([]), 1)
        receipt = json.loads((out / "report.json").read_text())
        self.assertEqual(receipt["status"], "FAIL")
        self.assertEqual(receipt["stage_of_exception"], "actual_copy")
        self.assertTrue(receipt["execution_aborted"])
        self.assertFalse(receipt["manufacturing_ready"])


if __name__ == "__main__":
    unittest.main()
