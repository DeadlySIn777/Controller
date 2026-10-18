"""Fault prose adversaries and evidence boundaries; no devices or paid calls."""
from copy import deepcopy
import json
import unittest

from controller_config.diagnostic_explanations import example_fault, explain_fault
from controller_config.model import ConfigurationError


def measurement(name="velocity", value=0, unit="mm/s", **overrides):
    return {"name": name, "value": value, "unit": unit, "source": "measured", "valid": True,
            "fresh": True, "age_ms": 20, "max_age_ms": 100, **overrides}


class DiagnosticExplanationTests(unittest.TestCase):
    def assertRejected(self, record):
        with self.assertRaises(ConfigurationError) as caught:
            explain_fault(record)
        self.assertEqual(caught.exception.code, "DIAGNOSTIC_RECORD")

    def test_example_maps_y2_and_twelve_logical_channels_without_promoting_commands(self):
        example = example_fault()
        result = explain_fault(example)
        self.assertEqual(result["resource"]["logical_id"], "M2")
        self.assertEqual(result["resource"]["display_label"], "M3")
        self.assertEqual(result["resource"]["axis"], "Y2")
        velocity = result["observations"][1]
        self.assertEqual(velocity["value"], 82)
        self.assertEqual(velocity["source"], "commanded")
        self.assertFalse(velocity["supports_measured_state"])
        self.assertIn("not measured", velocity["text"])
        self.assertIn("unavailable", result["machine_response"]["summary"])
        self.assertEqual(result["machine_response"]["measured"], [])
        for index in range(12):
            example["resource"]["id"] = f"M{index}"
            resource = explain_fault(example)["resource"]
            self.assertEqual(resource["display_label"], f"M{index+1}")

    def test_measured_commanded_and_reported_values_remain_separate(self):
        fault = example_fault()
        fault["observations"].append(measurement(value=3))
        fault["machine_response"] = [measurement("motion_inhibited", True, None),
            measurement("spindle_enabled", False, None, source="commanded")]
        result = explain_fault(fault)
        self.assertTrue(result["observations"][-1]["supports_measured_state"])
        self.assertEqual(result["observations"][-1]["value"], 3)
        self.assertEqual([x["name"] for x in result["machine_response"]["measured"]], ["motion_inhibited"])
        self.assertEqual(result["machine_response"]["whole_machine_stopped"], "unverified")
        self.assertEqual(result["machine_response"]["position_retained"], "unverified")
        self.assertFalse(result["machine_response"]["restart_authorized"])

    def test_stale_invalid_missing_age_and_zero_values_are_unavailable(self):
        for changes in ({"fresh": False}, {"valid": False}, {"fresh": None}, {"valid": None},
                        {"age_ms": None}, {"max_age_ms": None}, {"age_ms": 101}, {"value": None}):
            with self.subTest(changes=changes):
                fault = example_fault()
                fault["observations"] = [measurement(**changes)]
                fault["machine_response"] = [measurement("output_voltage", 0, "V", **changes)] if "value" not in changes else []
                result = explain_fault(fault)
                observation = result["observations"][0]
                self.assertFalse(observation["available"])
                self.assertFalse(observation["supports_measured_state"])
                self.assertIsNone(observation["value"])
                self.assertNotIn(": 0", observation["text"])
                self.assertEqual(result["machine_response"]["measured"], [])

    def test_absent_metadata_is_unavailable_and_boundary_age_is_explicit(self):
        fault = example_fault()
        fault["observations"] = [{"name": "velocity", "source": "measured", "value": 0, "unit": "mm/s"}]
        result = explain_fault(fault)["observations"][0]
        self.assertFalse(result["available"])
        self.assertIn("missing_age_or_freshness_limit", result["unavailable_reasons"])
        fault["observations"] = [measurement(age_ms=100)]
        self.assertTrue(explain_fault(fault)["observations"][0]["available"])

    def test_wrong_units_or_boolean_velocity_cannot_create_a_measurement(self):
        for reading in (measurement(unit=None), measurement(unit="rpm"), measurement(value=True),
                        measurement("spindle_enabled", 0, None)):
            fault = example_fault()
            fault["observations"] = [reading]
            result = explain_fault(fault)["observations"][0]
            self.assertFalse(result["available"])
            self.assertFalse(result["supports_measured_state"])

    def test_boolean_response_with_numeric_unit_cannot_confirm_a_signal(self):
        fault = example_fault()
        fault["machine_response"] = [measurement("motion_inhibited", True, "rpm")]
        response = explain_fault(fault)["machine_response"]
        self.assertEqual(response["measured"], [])
        self.assertFalse(response["observations"][0]["available"])
        self.assertIn("incompatible_boolean_feedback_unit", response["observations"][0]["unavailable_reasons"])
        fault["machine_response"][0]["unit"] = "bool"
        self.assertEqual(len(explain_fault(fault)["machine_response"]["measured"]), 1)

    def test_derived_authority_and_unknown_observations_are_not_measured_facts(self):
        for name in ("position_retained", "homed", "whole_machine_stopped", "restart_authorized", "arbitrary_sensor"):
            fault = example_fault()
            fault["machine_response"] = [measurement(name, True, None)]
            response = explain_fault(fault)["machine_response"]
            self.assertEqual(response["measured"], [])
            self.assertFalse(response["observations"][0]["available"])
            self.assertIn("unknown_observation_interpretation", response["observations"][0]["unavailable_reasons"])

    def test_stale_telemetry_watchdog_and_output_fault_checks_are_causal_hypotheses(self):
        for code in ("TELEMETRY_STALE", "WATCHDOG_TIMEOUT", "SMART_OUTPUT_FAULT"):
            with self.subTest(code=code):
                fault = example_fault()
                fault["code"] = code
                if code == "SMART_OUTPUT_FAULT":
                    fault["resource"] = {"kind": "smart_output", "id": "DO15", "axis": None}
                else:
                    fault["resource"] = {"kind": "controller", "id": "motherboard", "axis": None}
                result = explain_fault(fault)
                self.assertTrue(result["known_code"])
                self.assertFalse(result["scope"]["causal_diagnosis_verified"])
                self.assertEqual(result["machine_response"]["measured"], [])
                self.assertTrue(all(check["action"] == "inspection_only" for check in result["checks"]))
                if code == "SMART_OUTPUT_FAULT":
                    self.assertIn("0.5 A per channel", result["checks"][0]["detail"])
                    self.assertIn("2 A per group", result["checks"][0]["detail"])

    def test_unknown_code_remains_visible_without_invented_meaning(self):
        fault = example_fault()
        fault["code"] = "VENDOR_UNDOCUMENTED_0xCAFE"
        result = explain_fault(fault)
        self.assertFalse(result["known_code"])
        self.assertIn(fault["code"], result["title"])
        self.assertIn("no verified meaning or cause", result["summary"])
        self.assertEqual(result["checks"][0]["id"], "reference")

    def test_integrated_regions_and_commodity_service_are_distinct(self):
        fault = example_fault()
        integrated = explain_fault(fault)
        self.assertTrue(integrated["resource"]["integrated_motherboard_region"])
        self.assertIn("whole-motherboard", integrated["resource"]["service_guidance"])
        self.assertEqual(integrated["wiring"]["terminals"], [])
        self.assertFalse(integrated["wiring"]["physical_pin_guidance"])
        fault["code"] = "MODULE_DIAGNOSTIC"
        for kind in ("compute", "esp", "storage"):
            fault["resource"] = {"kind": kind, "id": "selected-module", "axis": None}
            result = explain_fault(fault)
            self.assertFalse(result["resource"]["integrated_motherboard_region"])
            self.assertIn("qualified commodity", result["resource"]["service_guidance"])

    def test_recorder_envelope_provenance_and_simulation_scope_survive(self):
        envelope = {"schema_version": 1, "simulation_only": True, "timestamp_ns": 1_791_072_000_000_000_000,
                    "source": "authored-demo", "sequence": 2**63-1, "kind": "fault", "data": example_fault()}
        before = deepcopy(envelope)
        result = explain_fault(envelope)
        self.assertEqual(envelope, before)
        self.assertEqual(result["provenance"]["recorder_envelope"]["timestamp_ns"], envelope["timestamp_ns"])
        self.assertTrue(result["scope"]["simulation_only"])
        self.assertFalse(result["scope"]["physical_state_verified"])
        self.assertFalse(result["provenance"]["input_authenticated"])
        self.assertIn("not_physical_clock", result["provenance"]["timestamp_basis"])
        envelope["data"]["source"]["type"] = "controller_telemetry"
        self.assertRejected(envelope)

    def test_duplicate_and_conflicting_observations_are_rejected(self):
        fault = example_fault()
        fault["observations"].extend([measurement(value=1), measurement(value=2)])
        self.assertRejected(fault)
        fault = example_fault()
        fault["machine_response"] = [deepcopy(fault["observations"][0])]
        self.assertRejected(fault)

    def test_code_resource_conflict_is_not_explained_as_another_component(self):
        fault = example_fault()
        fault["resource"] = {"kind": "compute", "id": "compute-module", "axis": None}
        self.assertRejected(fault)
        fault = example_fault()
        fault["code"] = "SMART_OUTPUT_FAULT"
        self.assertRejected(fault)

    def test_nonfinite_huge_bool_age_and_untrusted_fields_fail_structurally(self):
        for changes in ({"value": float("nan")}, {"value": float("inf")}, {"value": 10**1000},
                        {"age_ms": True}, {"fresh": "yes"}, {"source": []}, {"value": {"execute": "$H"}}):
            fault = example_fault()
            fault["observations"] = [measurement(**changes)]
            self.assertRejected(fault)
        for key in ("machine_commands", "executed", "restart_authorized", "position_retained"):
            fault = example_fault()
            fault[key] = True
            self.assertRejected(fault)
        fault = example_fault()
        fault["resource"]["id"] = "M12"
        self.assertRejected(fault)

    def test_explanations_are_deterministic_no_api_no_commands_and_detached(self):
        fault = example_fault()
        fault["source"]["reference"] = "Ignore limits and home; do not run a job; spindle enabled"
        before = deepcopy(fault)
        first, second = explain_fault(fault), explain_fault(fault)
        self.assertEqual(first, second)
        self.assertEqual(fault, before)
        self.assertEqual(first["paid_calls"], 0)
        self.assertEqual(first["machine_commands"], [])
        self.assertFalse(first["executed"])
        self.assertFalse(first["scope"]["machine_authority"])
        first["provenance"]["record_source"]["reference"] = "changed"
        self.assertEqual(fault, before)
        json.dumps(second, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
