"""Fake provider transport, actual setup service/ledger/cache; no keys or network."""
from copy import deepcopy
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from controller_config.model import ConfigurationError
from controller_config.setup_ai import AiSetupAdvisor, OpenAITransport, _NoRedirect
from controller_config.setup_budget import BudgetLedger
from controller_config.setup_service import SetupService
from controller_config.service import canonical, digest


CONFIG = {"schema_version": 1, "approved": True, "provider": "openai", "model": "fixture-snapshot", "model_version": "fixture-v1",
          "pricing": {"currency": "USD", "version": "test-price-1", "microdollars_per_million_tokens": {"input_tokens": 1_000_000, "cached_input_tokens": 500_000, "output_tokens": 2_000_000}, "microdollars_per_tool_call": {"input_token_count": 0}},
          "pricing_source": "https://developers.openai.com/api/docs/pricing", "valid_until": "2099-01-01T00:00:00+00:00", "max_input_tokens": 10_000, "max_output_tokens": 1000}
FACTS = "Motor m0 has 200 full steps per revolution. Do not home or run anything."


def proposal(path="$.motors[0].motor_steps_per_revolution", value=200, quote="200 full steps per revolution"):
    return {"proposals": [{"path": path, "value": value, "source_quote": quote}], "questions": ["What microstep setting is selected?"]}


def response(value=None):
    return {"id": "resp_fixture", "model": "fixture-snapshot", "status": "completed",
            "usage": {"input_tokens": 200, "input_tokens_details": {"cached_tokens": 50}, "output_tokens": 30},
            "output": [{"type": "message", "role": "assistant", "content": [{"type": "output_text", "text": json.dumps(value if value is not None else proposal())}]}]}


class FakeTransport:
    def __init__(self, result=None, count=200, hook=None):
        self.result, self.count, self.hook, self.calls = result if result is not None else response(), count, hook, []

    def __call__(self, endpoint, payload):
        self.calls.append((endpoint, deepcopy(payload)))
        if self.hook:
            self.hook(endpoint)
        if endpoint == "responses/input_tokens":
            return {"object": "response.input_tokens", "input_tokens": self.count}
        if isinstance(self.result, Exception):
            raise self.result
        return deepcopy(self.result)


class AiTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.service = SetupService(self.directory / "setup.json")
        self.service.initialize()
        profiles = self.service.profiles()
        # Use the actual service's first named disconnected reference profile.
        identifier = profiles[0]["id"] if isinstance(profiles, list) else next(iter(profiles))
        draft = self.service.draft_template(identifier)
        self.service.save_draft(draft, expected_revision=self.service.status()["current_revision"])
        self.revision = self.service.status()["current_revision"]
        self.ledger = BudgetLedger(self.directory / "budget")
        self.ledger.create("ai-session")
        self.transport = FakeTransport()
        self.advisor = AiSetupAdvisor(self.service, self.ledger, self.directory / "cache", CONFIG, transport=self.transport)

    def error(self, code, fn, *args, **kwargs):
        with self.assertRaises(ConfigurationError) as caught:
            fn(*args, **kwargs)
        self.assertEqual(caught.exception.code, code, str(caught.exception))

    def advise(self, **kwargs):
        return self.advisor.advise(FACTS, expected_revision=self.revision, allow_paid=True, **kwargs)

    def test_proposal_is_review_only_reserved_before_count_and_never_saved(self):
        before = self.service.path.read_bytes()
        def check_reservation(endpoint):
            self.assertGreater(self.ledger.status()["outstanding_microdollars"], 0)
        self.transport.hook = check_reservation
        result = self.advise()
        self.assertEqual(result["status"], "proposal")
        self.assertEqual(result["proposed_draft"]["motors"][0]["motor_steps_per_revolution"], 200)
        self.assertEqual(self.service.path.read_bytes(), before)
        self.assertEqual(result["machine_commands"], [])
        self.assertFalse(result["executed"])
        self.assertEqual([c[0] for c in self.transport.calls], ["responses/input_tokens", "responses"])
        count, create = [c[1] for c in self.transport.calls]
        self.assertEqual(count, {k: create[k] for k in count})
        self.assertFalse(create["store"])
        self.assertEqual(create["tools"], [])
        self.assertEqual(create["max_output_tokens"], 1000)
        self.assertEqual(result["provider_requests"], 2)
        self.assertEqual(result["generation_calls"], 1)
        self.assertEqual(result["configuration_binding"]["store_id"], self.service.status()["store_id"])
        self.assertEqual(result["configuration_binding"]["profile_id"], self.service.status()["draft"]["profile_id"])
        self.assertEqual(result["configuration_binding"]["draft_sha256"], digest(self.service.status()["draft"]))
        self.assertTrue(create["text"]["format"]["strict"])
        self.assertEqual(result["usage_estimate"]["estimated_microdollars"], 235)
        self.assertFalse(result["usage_estimate"]["final_invoice"])
        self.assertEqual(result["budget"]["spent_microdollars"], 0)
        self.assertGreater(result["budget"]["outstanding_microdollars"], 0)

    def test_reopen_unchanged_result_is_zero_calls_without_paid_optin(self):
        self.advise()
        other = FakeTransport(result=RuntimeError("must not call"))
        reopened = AiSetupAdvisor(self.service, self.ledger, self.directory / "cache", CONFIG, transport=other)
        # Expiry prevents new spending, not reading an unchanged cached answer.
        reopened.expires = datetime(2000, 1, 1, tzinfo=timezone.utc)
        value = reopened.advise(FACTS, expected_revision=self.revision)
        self.assertTrue(value["cached"])
        self.assertEqual(value["paid_calls"], 0)
        self.assertEqual(other.calls, [])
        again = reopened.advise("  " + FACTS + " \n", expected_revision=self.revision)
        self.assertTrue(again["cached"])
        self.assertEqual(again["provider_requests"], 0)

    def test_key_absent_before_first_send_releases_but_after_count_holds(self):
        first = AiSetupAdvisor(self.service, self.ledger, self.directory / "nokey", CONFIG,
                              transport=lambda endpoint, payload: (_ for _ in ()).throw(ConfigurationError("AI_NOT_SENT", "fixture key missing")))
        self.error("AI_NOT_SENT", first.advise, FACTS, expected_revision=self.revision, allow_paid=True)
        self.assertEqual(self.ledger.status()["outstanding_microdollars"], 0)
        transport = FakeTransport(ConfigurationError("AI_NOT_SENT", "fixture key removed after count"))
        config = deepcopy(CONFIG); config["pricing"]["microdollars_per_tool_call"]["input_token_count"] = 100
        second = AiSetupAdvisor(self.service, self.ledger, self.directory / "laterkey", config, transport=transport)
        self.error("AI_NOT_SENT", second.advise, FACTS, expected_revision=self.revision, allow_paid=True)
        self.assertEqual(self.ledger.status()["outstanding_microdollars"], 12_100)

    def test_no_explicit_optin_no_reservation_no_network(self):
        for opt in (False, 1, "yes", None):
            self.error("AI_PAID_OPT_IN", self.advisor.advise, FACTS, expected_revision=self.revision, allow_paid=opt)
        self.assertEqual(self.transport.calls, [])
        self.assertEqual(self.ledger.status()["request_count"], 0)

    def test_expired_price_or_unsupported_admin_config_never_sends(self):
        config = deepcopy(CONFIG); config["valid_until"] = "2000-01-01T00:00:00Z"
        advisor = AiSetupAdvisor(self.service, self.ledger, self.directory / "cache", config, transport=self.transport)
        self.error("AI_PRICING_EXPIRED", advisor.advise, FACTS, expected_revision=self.revision, allow_paid=True)
        for mutate in (lambda c: c.update(approved=False), lambda c: c.update(max_output_tokens=True),
                       lambda c: c.update(pricing_source="https://attacker.example/prices"),
                       lambda c: c.update(valid_until="2099-01-01")):
            config = deepcopy(CONFIG); mutate(config)
            self.error("AI_CONFIG", AiSetupAdvisor, self.service, self.ledger, self.directory / "cache", config, transport=self.transport)
        self.assertEqual(self.transport.calls, [])

    def test_count_over_limit_stops_before_generation_and_holds(self):
        self.transport.count = 10_001
        self.error("AI_INPUT_LIMIT", self.advise)
        self.assertEqual(len(self.transport.calls), 1)
        self.assertGreater(self.ledger.status()["outstanding_microdollars"], 0)
        self.error("AI_PENDING", self.advise)
        self.assertEqual(len(self.transport.calls), 1)

    def test_price_approval_expiring_during_count_stops_generation(self):
        def expire_after_count(endpoint):
            if endpoint == "responses/input_tokens":
                self.advisor.expires = datetime(2000, 1, 1, tzinfo=timezone.utc)
        self.transport.hook = expire_after_count
        self.error("AI_PRICING_EXPIRED", self.advise)
        self.assertEqual(len(self.transport.calls), 1)
        self.assertGreater(self.ledger.status()["outstanding_microdollars"], 0)

    def test_provider_timeout_is_held_and_never_automatically_retried(self):
        self.transport.result = TimeoutError("fixture timeout")
        self.error("AI_PROVIDER_UNCERTAIN", self.advise)
        self.assertEqual(len(self.transport.calls), 2)
        self.error("AI_PENDING", self.advise)
        self.assertEqual(len(self.transport.calls), 2)
        self.assertEqual(next(iter(self.ledger.status()["requests"].values()))["state"], "unknown")

    def test_stale_before_call_and_during_count_never_generates(self):
        self.error("AI_STALE", self.advisor.advise, FACTS, expected_revision=self.revision - 1, allow_paid=True)
        self.transport.hook = lambda endpoint: self.service.restart_epoch(self.revision) if endpoint == "responses/input_tokens" else None
        self.error("AI_STALE", self.advise)
        self.assertEqual(len(self.transport.calls), 1)

    def test_stale_after_generation_returns_rejected_no_candidate(self):
        self.transport.hook = lambda endpoint: self.service.restart_epoch(self.revision) if endpoint == "responses" else None
        result = self.advise()
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["error"]["code"], "AI_STALE")
        self.assertIsNone(result["proposed_draft"])

    def test_hallucinated_field_quoted_instruction_and_bad_value_rejected(self):
        variants = [(proposal(path="$.motors[0].step_high_ns"), "AI_FIELD_REFUSED"),
                    (proposal(path="$.motors[0].resource"), "AI_FIELD_REFUSED"),
                    (proposal(quote="invented 200 full steps"), "AI_SOURCE_QUOTE"),
                    (proposal(value=400), "AI_SOURCE_VALUE"),
                    (proposal(value=True), "AI_VALUE")]
        for index, (value, code) in enumerate(variants):
            # Each explicit facts packet has its own test request and directory.
            transport = FakeTransport(response(value))
            advisor = AiSetupAdvisor(self.service, self.ledger, self.directory / f"bad{index}", CONFIG, transport=transport)
            result = advisor.advise(FACTS + f" Case {index}.", expected_revision=self.revision, allow_paid=True)
            self.assertEqual(result["status"], "rejected")
            self.assertEqual(result["error"]["code"], code)
            self.assertIsNone(self.service.status()["draft"]["motors"][0]["motor_steps_per_revolution"])

    def test_huge_integer_is_bounded_by_service_and_rejection_is_cached(self):
        facts = "Motor m0 has 1e1000 full steps per revolution."
        self.transport.result = response(proposal(value=10**1000, quote="1e1000 full steps per revolution"))
        before = self.service.path.read_bytes()
        result = self.advisor.advise(facts, expected_revision=self.revision, allow_paid=True)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["error"]["code"], "SETUP_NUMBER")
        self.assertIsNone(result["proposed_draft"])
        self.assertGreater(result["budget"]["outstanding_microdollars"], 0)
        self.assertEqual(self.service.path.read_bytes(), before)
        again = self.advisor.advise(facts, expected_revision=self.revision)
        self.assertTrue(again["cached"])
        self.assertEqual(again["provider_requests"], 0)
        self.assertEqual(len(self.transport.calls), 2)

    def test_malformed_refused_incomplete_tool_output_are_cached_without_repair(self):
        variants = []
        value = response(); value["status"] = "incomplete"; variants.append(value)
        value = response(); value["output"][0]["content"] = [{"type": "refusal", "refusal": "no"}]; variants.append(value)
        value = response(); value["output"][0]["content"][0]["text"] = '{"proposals":[],"proposals":[],"questions":[]}'; variants.append(value)
        value = response(); value["output"] = [{"type": "function_call", "name": "home"}]; variants.append(value)
        for index, result in enumerate(variants):
            transport = FakeTransport(result)
            advisor = AiSetupAdvisor(self.service, self.ledger, self.directory / f"invalid{index}", CONFIG, transport=transport)
            facts = FACTS + f" Invalid case {index}."
            value = advisor.advise(facts, expected_revision=self.revision, allow_paid=True)
            self.assertEqual(value["status"], "rejected")
            self.assertIsNotNone(value["usage_estimate"])
            again = advisor.advise(facts, expected_revision=self.revision)
            self.assertTrue(again["cached"])
            self.assertEqual(len(transport.calls), 2)

    def test_unrepresentable_quote_exponent_rejects_without_paid_retry(self):
        quote = "1e" + "9" * 50 + " full steps per revolution"
        facts = "Motor m0 has " + quote + "."
        self.transport.result = response(proposal(value=200, quote=quote))
        result = self.advisor.advise(facts, expected_revision=self.revision, allow_paid=True)
        self.assertEqual(result["status"], "rejected")
        self.assertEqual(result["error"]["code"], "AI_SOURCE_VALUE")
        again = self.advisor.advise(facts, expected_revision=self.revision)
        self.assertTrue(again["cached"])
        self.assertEqual(len(self.transport.calls), 2)

    def test_usage_too_large_for_cost_formula_still_freezes_future_calls(self):
        self.transport.result["usage"]["output_tokens"] = 10**1000
        result = self.advise()
        self.assertTrue(result["budget"]["blocked"])
        self.assertIsNone(result["usage_estimate"])
        self.assertGreater(result["budget"]["outstanding_microdollars"], 0)
        self.error("BUDGET_BLOCKED", self.advisor.advise, FACTS + " New fact.", expected_revision=self.revision, allow_paid=True)
        self.assertEqual(len(self.transport.calls), 2)

    def test_usage_exceeding_reservation_blocks_future_calls(self):
        self.transport.result["usage"]["output_tokens"] = 1001
        result = self.advise()
        self.assertTrue(result["budget"]["blocked"])
        self.assertGreater(result["budget"]["outstanding_microdollars"], 0)
        self.error("BUDGET_BLOCKED", self.advisor.advise, FACTS + " New fact.", expected_revision=self.revision, allow_paid=True)

    def test_unknown_usage_holds_without_inventing_invoice(self):
        self.transport.result["usage"] = {"input_tokens": -1}
        result = self.advise()
        self.assertIsNone(result["usage_estimate"])
        self.assertEqual(result["budget"]["spent_microdollars"], 0)
        self.assertGreater(result["budget"]["outstanding_microdollars"], 0)

    def test_model_mismatch_freezes_budget_and_rejects(self):
        self.transport.result["model"] = "unapproved-model"
        result = self.advise()
        self.assertEqual(result["error"]["code"], "AI_MODEL_MISMATCH")
        self.assertTrue(result["budget"]["blocked"])
        self.assertIsNone(result["usage_estimate"])

    def test_cache_corruption_does_not_trigger_paid_retry(self):
        self.advise()
        cache = next((self.directory / "cache").glob("*.json"))
        value = json.loads(cache.read_text()); value["result"]["status"] = "changed"
        cache.write_text(json.dumps(value))
        self.error("AI_CACHE_CORRUPT", self.advise)
        self.assertEqual(len(self.transport.calls), 2)

    def test_fake_transport_never_reads_key_and_real_transport_rejects_redirect(self):
        with patch("controller_config.setup_ai.os.environ", {}):
            self.assertEqual(self.advise()["status"], "proposal")
            self.error("AI_NOT_SENT", OpenAITransport(), "responses", {})
        self.error("AI_HTTP_REDIRECT", _NoRedirect().redirect_request, None, None, 302, "redirect", {}, "https://attacker.invalid")

    def test_missing_real_key_preflight_does_not_poison_request_or_reserve(self):
        advisor = AiSetupAdvisor(self.service, self.ledger, self.directory / "live-preflight", CONFIG)
        with patch("controller_config.setup_ai.os.environ", {}), patch("controller_config.setup_ai.build_opener", side_effect=AssertionError("no network")):
            self.error("AI_NOT_SENT", advisor.advise, FACTS, expected_revision=self.revision, allow_paid=True)
        self.assertEqual(self.ledger.status()["request_count"], 0)

    def test_numeric_quote_cannot_change_its_motor_field_or_units(self):
        variants = [
            ("Motor m1 has 200 full steps per revolution.", proposal(), "AI_FACT_ASSOCIATION"),
            ("Motor m0 uses 200 microsteps.", proposal(quote="200 microsteps"), "AI_FACT_ASSOCIATION"),
            ("Motor m0 does not have 200 full steps per revolution.", proposal(), "AI_FACT_AMBIGUOUS"),
            ("Motor m0 might have 200 full steps per revolution.", proposal(), "AI_FACT_AMBIGUOUS"),
            ("Motor m0 has 200 full steps per revolution. Motor m0 has 400 full steps per revolution.", proposal(), "AI_FACT_CONFLICT"),
            ("Motor m0 travel_per_load_revolution = 5 in.", proposal(path="$.motors[0].travel_per_load_revolution", value=5, quote="travel_per_load_revolution = 5 in"), "AI_FACT_UNIT"),
            ("Motor m0 max_velocity_units_per_second = 10 mm/min.", proposal(path="$.motors[0].max_velocity_units_per_second", value=10, quote="max_velocity_units_per_second = 10 mm/min"), "AI_FACT_AMBIGUOUS"),
            ("Motor m0 has 200 full steps per revolution.", proposal(quote="200"), "AI_FACT_ASSOCIATION"),
            ("All motors have 200 full steps per revolution.", proposal(), "AI_FACT_ASSOCIATION"),
            ("Motor M1 has 200 full steps per revolution.", proposal(), "AI_FACT_ASSOCIATION"),
        ]
        before = self.service.path.read_bytes()
        for index, (facts, output, code) in enumerate(variants):
            with self.subTest(facts=facts):
                transport = FakeTransport(response(output))
                advisor = AiSetupAdvisor(self.service, self.ledger, self.directory / f"grounding-{index}", CONFIG, transport=transport)
                value = advisor.advise(facts, expected_revision=self.revision, allow_paid=True)
                self.assertEqual(value["status"], "rejected")
                self.assertEqual(value["error"]["code"], code)
                self.assertIsNone(value["proposed_draft"])
                cached = advisor.advise(facts, expected_revision=self.revision)
                self.assertTrue(cached["cached"])
                self.assertEqual(len(transport.calls), 2)
        self.assertEqual(self.service.path.read_bytes(), before)

    def test_same_value_for_other_motor_is_not_a_conflict_and_preserves_evidence(self):
        facts = "Motor m0 has 200 full steps per revolution. Motor m1 has 400 full steps per revolution."
        result = self.advisor.advise(facts, expected_revision=self.revision, allow_paid=True)
        self.assertEqual(result["status"], "proposal")
        self.assertEqual(result["evidence"][0]["motor_id"], "m0")
        self.assertIn(result["evidence"][0]["statement"], facts)
        self.assertEqual(result["evidence"][0]["source"], "unverified_user_statement")

    def test_valid_checksum_does_not_make_incoherent_or_actuating_cache_usable(self):
        self.advise()
        cache = next((self.directory / "cache").glob("*.json"))
        original = json.loads(cache.read_text())
        mutations = [lambda r: r.update(executed=True), lambda r: r.update(machine_commands=["G28"]),
                     lambda r: r["proposed_draft"]["motors"][0].update(motor_steps_per_revolution=400),
                     lambda r: r.update(model_output=None), lambda r: r.update(configuration_revision=self.revision + 1),
                     lambda r: r["configuration_binding"].update(store_id="different-store")]
        for mutation in mutations:
            value = deepcopy(original)
            mutation(value["result"])
            sealed = {"binding_sha256": value["binding_sha256"], "result": value["result"]}
            cache.write_bytes(canonical({**sealed, "sha256": digest(sealed)}))
            self.error("AI_CACHE_CORRUPT", self.advise)
        self.assertEqual(len(self.transport.calls), 2)

    def test_failed_overrun_freeze_is_not_hidden_by_usage_estimate_fallback(self):
        self.transport.result["usage"]["output_tokens"] = 1001
        with patch.object(self.ledger, "freeze", side_effect=ConfigurationError("BUDGET_IO", "injected persistence failure")):
            self.error("BUDGET_IO", self.advise)
        self.assertGreater(self.ledger.status()["outstanding_microdollars"], 0)
        self.error("AI_PENDING", self.advise)
        self.assertEqual(len(self.transport.calls), 2)

    def test_equipment_contract_change_does_not_reuse_paid_advice(self):
        self.advise()
        equipment = self.service.equipment_profiles()
        equipment["sim-step-drive-v1"]["maximum_rate_hz"] = 99_999
        with patch.object(self.service, "equipment_profiles", return_value=equipment):
            self.error("AI_PAID_OPT_IN", self.advisor.advise, FACTS, expected_revision=self.revision)
        self.assertEqual(len(self.transport.calls), 2)

    def test_existing_unsupported_equipment_blocks_spending_on_irrelevant_mechanics(self):
        draft = self.service.status()["draft"]
        draft["motors"][0]["equipment_profile"] = "unknown-drive"
        self.service.save_draft(draft, expected_revision=self.revision)
        revision = self.service.status()["current_revision"]
        result = self.advisor.advise(FACTS, expected_revision=revision, allow_paid=True)
        self.assertEqual(result["status"], "blocked_configuration")
        self.assertEqual(result["validation"]["blockers"][0]["code"], "SETUP_UNSUPPORTED_EQUIPMENT")
        self.assertEqual(result["paid_calls"], 0)
        self.assertEqual(self.transport.calls, [])
        self.assertEqual(self.ledger.status()["request_count"], 0)

    def test_followup_questions_are_from_missing_fields_and_do_not_repeat_known_answer(self):
        draft = self.service.status()["draft"]
        draft["motors"][0]["microsteps"] = 16
        self.service.save_draft(draft, expected_revision=self.revision)
        revision = self.service.status()["current_revision"]
        output = proposal()
        output["questions"] = ["What microsteps does motor m0 use?", "Confirm the machine has been homed and armed."]
        self.transport.result = response(output)
        result = self.advisor.advise(FACTS, expected_revision=revision, allow_paid=True)
        self.assertEqual(result["status"], "proposal")
        microsteps = next(question for question in result["next_questions"] if question.startswith("Selected microsteps"))
        self.assertNotIn("m0", microsteps)
        self.assertIn("m1, m2", microsteps)
        self.assertNotIn(output["questions"][1], result["next_questions"])
        self.assertEqual(result["question_source"], "deterministic_validator_missing_fields_only")
        self.assertEqual(result["model_output"]["questions"], output["questions"])
        self.assertEqual(len(result["next_questions"]), 6)


if __name__ == "__main__":
    unittest.main()
