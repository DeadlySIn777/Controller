"""Independent examples and boundary checks for the demand model."""

import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("requirements_analyzer", ROOT / "tools" / "analyze_requirements.py")
MODEL = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODEL)


def linear_joint():
    return {
        "name": "X", "kind": "linear",
        "drive_input_pulses_per_motor_rev": 2000,
        "motor_revs_per_output_rev": 2,
        "output_mm_per_rev": 5,
        "maximum_speed_mm_min": 6000,
        "minimum_pulse_high_us": 2,
        "minimum_pulse_low_us": 3,
    }


def network():
    return {
        "link_capacity_mbit_s": 100,
        "capacity_mode": "full_duplex",
        "ip_mtu_bytes": 1500,
        "overhead_bytes": {
            "ethernet_header": 14, "ethernet_fcs": 4,
            "preamble_and_sfd": 8, "interpacket_gap": 12,
            "ip_header": 20, "transport_header": 8,
            "minimum_ethernet_payload": 46,
        },
        "streams": [{
            "name": "commands", "direction": "host_to_controller",
            "payload_bytes_per_packet": 128, "packets_per_update": 1,
            "update_period_ms": 1,
        }],
    }


class JointDemandTests(unittest.TestCase):
    def test_linear_gearing_known_example(self):
        # 100 mm/s / 5 mm = 20 output rev/s, 2:1 gear = 40 motor rev/s.
        result = MODEL.analyze_joint(linear_joint(), "joint")
        self.assertEqual(result["required_step_pulses_per_second"], 80000)
        self.assertEqual(result["command_pulses_per_mm"], 800)
        self.assertEqual(result["step_period_us_at_maximum_speed"], 12.5)
        self.assertEqual(result["required_step_pin_transitions_per_second"], 160000)

    def test_width_boundary_is_inclusive_and_excess_is_detected(self):
        config = linear_joint()
        config["maximum_speed_mm_min"] = 15000  # Exactly 200 kHz / 5 us period.
        result = MODEL.analyze_joint(config, "joint")
        self.assertTrue(result["pulse_width_limit_check"]["within_assumed_limit"])
        config["maximum_speed_mm_min"] = 15000.01
        result = MODEL.analyze_joint(config, "joint")
        self.assertFalse(result["pulse_width_limit_check"]["within_assumed_limit"])

    def test_rotary_ratio_is_motor_revolutions_per_output_revolution(self):
        config = linear_joint()
        del config["output_mm_per_rev"]
        del config["maximum_speed_mm_min"]
        config.update(kind="rotary", motor_revs_per_output_rev=20, maximum_output_speed_rpm=30)
        result = MODEL.analyze_joint(config, "joint")
        self.assertEqual(result["required_step_pulses_per_second"], 20000)

    def test_zero_speed_has_no_finite_pulse_period(self):
        config = linear_joint()
        config["maximum_speed_mm_min"] = 0
        result = MODEL.analyze_joint(config, "joint")
        self.assertEqual(result["required_step_pulses_per_second"], 0)
        self.assertIsNone(result["step_period_us_at_maximum_speed"])
        self.assertTrue(result["pulse_width_limit_check"]["within_assumed_limit"])

    def test_encoder_shaft_changes_rate_with_gearing(self):
        config = linear_joint()
        config.update(encoder_shaft="motor", encoder={"signal_definition": "quadrature_lines_per_rev", "resolution_per_rev": 1000})
        motor = MODEL.analyze_joint(config, "joint")["encoder"]
        config["encoder_shaft"] = "output"
        output = MODEL.analyze_joint(config, "joint")["encoder"]
        self.assertEqual(motor["decoded_count_or_rising_pulse_rate_hz"], 160000)
        self.assertEqual(output["decoded_count_or_rising_pulse_rate_hz"], 80000)


class EncoderTests(unittest.TestCase):
    def test_quadrature_lines_counts_and_index_are_distinct(self):
        # 6000 rev/min -> 100 rev/s; 2048 lines -> 8192 decoded counts/rev.
        result = MODEL.analyze_encoder({"signal_definition": "quadrature_lines_per_rev", "resolution_per_rev": 2048, "index_pulses_per_rev": 1}, 100, "encoder")
        self.assertEqual(result["decoded_count_or_rising_pulse_rate_hz"], 819200)
        self.assertEqual(result["quadrature_channel_cycle_rate_hz"], 204800)
        self.assertEqual(result["index_rising_pulse_rate_hz"], 100)

    def test_already_decoded_counts_are_not_quadrupled(self):
        result = MODEL.analyze_encoder({"signal_definition": "decoded_counts_per_rev", "resolution_per_rev": 8192}, 100, "encoder")
        self.assertEqual(result["decoded_count_or_rising_pulse_rate_hz"], 819200)
        self.assertIsNone(result["quadrature_channel_cycle_rate_hz"])

    def test_single_channel_pulses_are_not_quadrupled(self):
        result = MODEL.analyze_encoder({"signal_definition": "single_channel_rising_pulses_per_rev", "resolution_per_rev": 1}, 100, "encoder")
        self.assertEqual(result["decoded_count_or_rising_pulse_rate_hz"], 100)


class NetworkTests(unittest.TestCase):
    def test_known_packet_slot_and_bandwidth(self):
        # 128 payload + 20 IP + 8 transport + 38 frame/gap = 194 byte slots.
        result = MODEL.analyze_network(network(), "network")
        stream = result["streams"][0]
        self.assertEqual(stream["modeled_wire_slot_bytes_per_packet"], 194)
        self.assertEqual(stream["wire_slot_bits_per_second"], 1552000)
        self.assertAlmostEqual(stream["serialization_and_gap_us_per_packet"], 15.52)
        self.assertAlmostEqual(result["capacity_utilization"], 0.01552)
        self.assertFalse(result["deadline_guaranteed"])

    def test_minimum_frame_padding(self):
        config = network()
        config["streams"][0]["payload_bytes_per_packet"] = 0
        result = MODEL.analyze_network(config, "network")
        self.assertEqual(result["streams"][0]["modeled_wire_slot_bytes_per_packet"], 84)

    def test_full_duplex_is_not_erroneously_added_for_utilization(self):
        config = network()
        config["link_capacity_mbit_s"] = 2
        feedback = copy.deepcopy(config["streams"][0])
        feedback.update(name="feedback", direction="controller_to_host")
        config["streams"].append(feedback)
        full = MODEL.analyze_network(config, "network")
        self.assertTrue(full["within_assumed_capacity"])
        self.assertEqual(full["aggregate_wire_slot_bits_per_second_both_directions"], 3104000)
        self.assertAlmostEqual(full["capacity_utilization"], 0.776)
        config["capacity_mode"] = "shared"
        shared = MODEL.analyze_network(config, "network")
        self.assertFalse(shared["within_assumed_capacity"])
        self.assertAlmostEqual(shared["capacity_utilization"], 1.552)

    def test_packet_mtu_exact_boundary_and_one_byte_over(self):
        config = network()
        config["streams"][0]["payload_bytes_per_packet"] = 1472
        MODEL.analyze_network(config, "network")
        config["streams"][0]["payload_bytes_per_packet"] = 1473
        with self.assertRaisesRegex(MODEL.InputError, "MTU"):
            MODEL.analyze_network(config, "network")


class StoppingTests(unittest.TestCase):
    def test_idealized_known_example(self):
        result = MODEL.analyze_stopping({"name": "example", "speed_mm_min": 18000, "assumed_reaction_time_ms": 10, "assumed_constant_deceleration_mm_s2": 1500}, "stop")
        self.assertEqual(result["ideal_reaction_distance_mm"], 3)
        self.assertEqual(result["ideal_braking_distance_mm"], 30)
        self.assertEqual(result["ideal_total_distance_mm"], 33)
        self.assertAlmostEqual(result["ideal_reaction_plus_braking_time_s"], 0.21)
        self.assertFalse(result["safety_validated"])

    def test_zero_speed_and_zero_reaction_are_valid(self):
        result = MODEL.analyze_stopping({"name": "stationary", "speed_mm_min": 0, "assumed_reaction_time_ms": 0, "assumed_constant_deceleration_mm_s2": 1}, "stop")
        self.assertEqual(result["ideal_total_distance_mm"], 0)


class StudyAndValidationTests(unittest.TestCase):
    def setUp(self):
        self.study = json.loads((ROOT / "config" / "machine-study.json").read_text(encoding="utf-8"))

    def test_aggregate_rate_differs_from_single_joint_rate(self):
        report = MODEL.analyze(self.study)
        router, mill, lathe = report["scenarios"]
        self.assertEqual(router["aggregate_step_pulses_per_second_at_simultaneous_joint_maxima"], 440000)
        self.assertEqual(router["largest_single_joint_step_pulses_per_second"], 120000)
        self.assertEqual(mill["aggregate_step_pulses_per_second_at_simultaneous_joint_maxima"], 1020000)
        self.assertEqual(mill["assumed_limit_violations"], ["joint X: pulse_width_limit_check", "joint Y: pulse_width_limit_check", "aggregate joint step pulse rate"])
        self.assertEqual(lathe["aggregate_step_pulses_per_second_at_simultaneous_joint_maxima"], 400000)

    def test_units_cannot_silently_change(self):
        self.study["units"]["linear_speed"] = "inch/min"
        with self.assertRaisesRegex(MODEL.InputError, "conversions are not implicit"):
            MODEL.analyze(self.study)

    def test_unknown_fields_are_errors(self):
        self.study["scenarios"][0]["joints"][0]["speed_rpm"] = 1
        with self.assertRaisesRegex(MODEL.InputError, "unknown fields"):
            MODEL.analyze(self.study)

    def test_duplicate_joint_names_are_errors(self):
        joints = self.study["scenarios"][0]["joints"]
        joints[1]["name"] = joints[0]["name"]
        with self.assertRaisesRegex(MODEL.InputError, "duplicate name"):
            MODEL.analyze(self.study)

    def test_positive_inputs_reject_zero_negative_nonfinite_boolean_and_string(self):
        for invalid in (0, -1, float("nan"), float("inf"), True, "5", None):
            with self.subTest(invalid=invalid):
                joint = linear_joint()
                joint["output_mm_per_rev"] = invalid
                with self.assertRaises(MODEL.InputError):
                    MODEL.analyze_joint(joint, "joint")

    def test_encoder_ambiguity_and_fractional_resolution_are_rejected(self):
        for definition, resolution in (("ppr", 1000), ("quadrature_lines_per_rev", 1000.5)):
            with self.subTest(definition=definition, resolution=resolution):
                with self.assertRaises(MODEL.InputError):
                    MODEL.analyze_encoder({"signal_definition": definition, "resolution_per_rev": resolution}, 1, "encoder")

    def test_zero_network_period_and_stopping_deceleration_are_rejected(self):
        config = network()
        config["streams"][0]["update_period_ms"] = 0
        with self.assertRaises(MODEL.InputError):
            MODEL.analyze_network(config, "network")
        with self.assertRaises(MODEL.InputError):
            MODEL.analyze_stopping({"name": "invalid", "speed_mm_min": 1, "assumed_reaction_time_ms": 0, "assumed_constant_deceleration_mm_s2": 0}, "stop")

    def test_cli_report_and_nonzero_limit_mode(self):
        with tempfile.TemporaryDirectory() as directory:
            destination = Path(directory) / "report.json"
            result = subprocess.run([sys.executable, str(ROOT / "tools" / "analyze_requirements.py"), str(ROOT / "config" / "machine-study.json"), "--output", str(destination), "--fail-on-limit"], capture_output=True, text=True)
            self.assertEqual(result.returncode, 1, result.stderr)
            self.assertEqual(json.loads(result.stdout), json.loads(destination.read_text(encoding="utf-8")))
            self.assertFalse(json.loads(result.stdout)["all_scenarios_within_configured_assumed_limits"])

    def test_cli_invalid_json_and_duplicate_keys_return_input_error(self):
        for content in ('{"schema_version": 1, "schema_version": 2}', '{"bad": NaN}', '{'):
            with self.subTest(content=content), tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / "bad.json"
                source.write_text(content, encoding="utf-8")
                result = subprocess.run([sys.executable, str(ROOT / "tools" / "analyze_requirements.py"), str(source)], capture_output=True, text=True)
                self.assertEqual(result.returncode, 2)
                self.assertIn("Input error:", result.stderr)
                self.assertEqual(result.stdout, "")


if __name__ == "__main__":
    unittest.main()
