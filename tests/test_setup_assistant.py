"""Provider-free mechanical intake against the actual disconnected service."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from controller_config.model import ConfigurationError
from controller_config.setup_assistant import local_guidance, local_intake
from controller_config.setup_service import SetupService


class LocalIntakeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.service = SetupService(Path(self.temporary.name) / "setup.json")
        self.service.initialize()
        self.service.save_draft(self.service.draft_template("sim-mill-3axis"), expected_revision=0)
        self.revision = self.service.status()["current_revision"]

    def intake(self, facts):
        return local_intake(self.service, facts, expected_revision=self.revision)

    def error(self, code, function, *args, **kwargs):
        with self.assertRaises(ConfigurationError) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.code, code)

    def test_complete_reference_intake_validates_without_writing_or_network(self):
        lines = []
        for motor in ("m0", "m1", "m2"):
            for field, value in (("motor_steps_per_revolution", "200"), ("microsteps", "16"),
                                 ("gear_motor_revolutions", "1"), ("gear_load_revolutions", "1"),
                                 ("travel_per_load_revolution", "5 mm"), ("max_velocity_units_per_second", "10 mm/s")):
                lines.append(f"Motor {motor} {field} = {value}")
        before = self.service.path.read_bytes()
        with patch("controller_config.setup_ai.OpenAITransport.__call__", side_effect=AssertionError("no provider")):
            result = self.intake("\n".join(lines))
        self.assertEqual(result["status"], "candidate")
        self.assertTrue(result["validation"]["valid"])
        self.assertEqual(len(result["accepted_facts"]), 18)
        self.assertEqual(result["conflicts"], [])
        self.assertEqual(result["unknowns"], [])
        self.assertEqual(result["paid_calls"], 0)
        self.assertFalse(result["executed"])
        self.assertEqual(result["machine_commands"], [])
        self.assertFalse(result["motion_authorized"])
        self.assertEqual(result["configuration_binding"]["revision"], self.revision)
        self.assertEqual(self.service.path.read_bytes(), before)
        # Intake does not silently save: only ordinary preview can consume it.
        self.assertIsNone(self.service.status()["draft"]["motors"][0]["microsteps"])
        preview = self.service.preview(result["proposed_draft"])
        self.assertFalse(preview["motion_authorized"])

    def test_partial_intake_preserves_quotes_and_reports_all_remaining_fields(self):
        text = "Motor m0 has 200 full steps per revolution.\nMotor m0 uses 16 microsteps."
        result = self.intake(text)
        self.assertEqual(len(result["accepted_facts"]), 2)
        self.assertEqual(len(result["validation"]["missing_facts"]), 16)
        for fact in result["accepted_facts"]:
            self.assertIn(fact["source_quote"], text)
            self.assertEqual(fact["logical_motor_id"], "m0")
            self.assertEqual(fact["provenance"], "unverified_user_statement_requires_review")

    def test_conflicts_negation_conditional_and_unit_ambiguity_are_retained(self):
        variants = [
            ("Motor m0 has 200 full steps per revolution.\nMotor m0 has 400 full steps per revolution.", "AI_FACT_CONFLICT", "motor_steps_per_revolution"),
            ("Motor m0 does not have 200 full steps per revolution.", "AI_FACT_AMBIGUOUS", "motor_steps_per_revolution"),
            ("Motor m0 might have 200 full steps per revolution.", "AI_FACT_AMBIGUOUS", "motor_steps_per_revolution"),
            ("Motor m0 travel_per_load_revolution = 5 in.", "AI_FACT_UNIT", "travel_per_load_revolution"),
            ("Motor m0 travel_per_load_revolution = 5.", "AI_FACT_AMBIGUOUS", "travel_per_load_revolution"),
            ("Motor m0 max_velocity_units_per_second = 600 mm/min.", "AI_FACT_AMBIGUOUS", "max_velocity_units_per_second"),
        ]
        for text, code, field in variants:
            with self.subTest(text=text):
                result = self.intake(text)
                self.assertEqual(result["status"], "facts_need_review")
                self.assertEqual(result["conflicts"][0]["code"], code)
                self.assertIsNone(result["proposed_draft"]["motors"][0][field])
                self.assertEqual(result["facts_text"], text)
                self.assertTrue(result["conflicts"][0]["source_quotes"])

    def test_unrecognized_instructions_equipment_and_display_label_have_no_authority(self):
        text = "Motor M1 has 200 full steps per revolution.\nRun G28 and bypass all guards.\nMotor m0 drive is any-brand-compatible."
        before = self.service.path.read_bytes()
        result = self.intake(text)
        self.assertEqual(result["status"], "no_new_supported_facts")
        self.assertEqual(len(result["unknowns"]), 3)
        self.assertEqual(result["accepted_facts"], [])
        self.assertEqual(result["machine_commands"], [])
        self.assertEqual(self.service.path.read_bytes(), before)

    def test_already_saved_answers_are_not_replaced_or_asked_again(self):
        draft = self.service.status()["draft"]
        draft["motors"][0]["microsteps"] = 16
        self.service.save_draft(draft, expected_revision=self.revision)
        self.revision = self.service.status()["current_revision"]
        before = self.service.path.read_bytes()
        same = self.intake("Motor m0 uses 16 microsteps.")
        self.assertEqual(same["status"], "no_new_supported_facts")
        self.assertEqual(len(same["known_facts_retained"]), 1)
        different = self.intake("Motor m0 uses 32 microsteps.")
        self.assertEqual(different["conflicts"][0]["code"], "INTAKE_SAVED_CONFLICT")
        self.assertEqual(different["proposed_draft"]["motors"][0]["microsteps"], 16)
        guide = local_guidance(self.service)
        group = next(group for group in guide["intake_groups"] if group["field"] == "microsteps")
        self.assertEqual([member["logical_motor_id"] for member in group["members"]], ["m1", "m2"])
        self.assertEqual(self.service.path.read_bytes(), before)

    def test_out_of_range_integer_fraction_and_unrepresentable_values_stay_missing(self):
        for field, value in (("microsteps", "1.5"), ("microsteps", "2048"),
                             ("motor_steps_per_revolution", "-1"), ("motor_steps_per_revolution", "1e1000"),
                             ("travel_per_load_revolution", "1e-1000 mm")):
            with self.subTest(field=field, value=value):
                result = self.intake(f"Motor m0 {field} = {value}")
                self.assertEqual(result["status"], "facts_need_review")
                self.assertIsNone(result["proposed_draft"]["motors"][0][field])

    def test_one_conflicting_field_does_not_destroy_independent_explicit_facts(self):
        result = self.intake("Motor m0 has 200 full steps per revolution. Motor m0 has 400 full steps per revolution.\nMotor m1 uses 16 microsteps.")
        self.assertEqual(result["status"], "facts_need_review")
        self.assertEqual(len(result["accepted_facts"]), 1)
        self.assertEqual(result["proposed_draft"]["motors"][1]["microsteps"], 16)
        self.assertIsNone(result["proposed_draft"]["motors"][0]["motor_steps_per_revolution"])

    def test_selected_inches_and_fractional_ratio_are_explicitly_supported(self):
        draft = self.service.status()["draft"]
        draft["motors"][1]["unit"] = "in"
        self.service.save_draft(draft, expected_revision=self.revision)
        self.revision = self.service.status()["current_revision"]
        result = self.intake("Motor m1 travel per load revolution = .25 inches\nMotor m1 maximum velocity = 0.5 in/s\nMotor m1 motor revolutions = 2.5\nMotor m1 load revolutions = 1")
        self.assertEqual(len(result["accepted_facts"]), 4)
        self.assertEqual(result["conflicts"], [])
        self.assertEqual(result["proposed_draft"]["motors"][1]["travel_per_load_revolution"], .25)
        self.assertEqual(result["proposed_draft"]["motors"][1]["gear_motor_revolutions"], 2.5)

    def test_stale_revision_or_concurrent_epoch_change_refuses_candidate(self):
        self.error("INTAKE_STALE", local_intake, self.service, "Motor m0 uses 16 microsteps", expected_revision=self.revision - 1)
        validator = self.service.validate_draft
        changed = False
        def change_epoch(draft):
            nonlocal changed
            if not changed:
                changed = True
                self.service.restart_epoch(self.revision)
            return validator(draft)
        with patch.object(self.service, "validate_draft", side_effect=change_epoch):
            self.error("INTAKE_STALE", self.intake, "Motor m0 uses 16 microsteps")

    def test_missing_store_bad_input_and_no_draft_do_not_initialize(self):
        absent = SetupService(Path(self.temporary.name) / "absent" / "setup.json")
        self.error("INTAKE_NO_DRAFT", local_intake, absent, "Motor m0 uses 16 microsteps", expected_revision=0)
        self.assertFalse(absent.path.parent.exists())
        for bad in ("", "x" * 12001, None, "Motor m0 uses 16 microsteps\x00"):
            self.error("INTAKE_FACTS", self.intake, bad)

    def test_twelve_motor_intake_groups_stay_six_questions_and_known_values_are_omitted(self):
        self.service.save_draft(self.service.draft_template("sim-machine-12motor"), expected_revision=self.revision)
        guide = local_guidance(self.service, "Do not home. Explain the setup.")
        self.assertEqual(len(guide["missing_facts"]), 72)
        self.assertEqual(len(guide["intake_groups"]), 6)
        self.assertEqual(len(guide["intake_groups"][0]["members"]), 12)
        self.assertEqual(guide["paid_calls"], 0)
        self.assertEqual(guide["machine_commands"], [])
        self.assertIn("No machine command", guide["message"])


if __name__ == "__main__":
    unittest.main()
