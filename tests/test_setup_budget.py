"""Actual temporary-file accounting/restart/process races; no network or machine."""
from copy import deepcopy
import json
import multiprocessing
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import unittest
from unittest.mock import patch

from controller_config.model import ConfigurationError
from controller_config.service import canonical, digest, MAX_BYTES
from controller_config.setup_budget import (BudgetLedger, BudgetError, MAX_CAP_MICRODOLLARS,
                                             MAX_INTEGER, MAX_REQUESTS, estimate_microdollars)


ROOT = Path(__file__).resolve().parents[1]
PRICES = {"currency": "USD", "version": "approved-test-prices-1",
          "microdollars_per_million_tokens": {"input_tokens": 1_000_000, "cached_input_tokens": 100_000, "output_tokens": 2_000_000},
          "microdollars_per_tool_call": {"lookup": 50}}
LIMITS = {"input_tokens": 1000, "cached_input_tokens": 1000, "output_tokens": 500, "tool_calls": {"lookup": 2}}


def reservation(amount=2200):
    # Fixture produces exactly ``amount`` microdollars without rounding.
    return {"payload_sha256": "a" * 64, "provider": "fixture-provider", "model": "fixture-model", "model_version": "v1",
            "pricing": deepcopy(PRICES),
            "limits": {"input_tokens": amount, "cached_input_tokens": 0, "output_tokens": 0, "tool_calls": {}}}


def concurrent_reserve(path, request_id, start, results):
    start.wait(10)
    ledger = BudgetLedger(path)
    deadline = time.monotonic() + 10
    while time.monotonic() < deadline:
        try:
            value = ledger.reserve(request_id, **reservation(600_000))
            results.put((request_id, "reserved", value["dispatch_allowed"]))
            return
        except ConfigurationError as error:
            if error.code != "BUDGET_BUSY":
                results.put((request_id, error.code, False))
                return
            time.sleep(.005)
    results.put((request_id, "lock_timeout", False))


class BudgetTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.ledger = BudgetLedger(self.directory)
        self.ledger.create("setup-session")

    def error(self, code, function, *args, **kwargs):
        with self.assertRaises(ConfigurationError) as caught:
            function(*args, **kwargs)
        self.assertEqual(caught.exception.code, code, str(caught.exception))

    def test_create_is_explicit_and_cannot_reset_spend_or_top_up(self):
        self.ledger.reserve("r1", **reservation())
        self.ledger.settle("r1", actual_microdollars=2000, evidence_id="invoice-1")
        repeated = self.ledger.create("setup-session")
        self.assertEqual(repeated["spent_microdollars"], 2000)
        self.error("BUDGET_EXISTS", self.ledger.create, "new-session")
        self.error("BUDGET_EXISTS", self.ledger.create, "setup-session", cap_microdollars=1000)
        unopened = BudgetLedger(self.directory / "new")
        self.error("BUDGET_NOT_FOUND", unopened.status)
        self.assertFalse(unopened.path.exists())

    def test_explicit_file_path_and_zero_cap(self):
        ledger = BudgetLedger(self.directory / "other.json")
        status = ledger.create("other", cap_microdollars=0)
        self.assertEqual(ledger.path, self.directory / "other.json")
        self.assertEqual(status["remaining_microdollars"], 0)
        self.error("BUDGET_EXHAUSTED", ledger.reserve, "paid", **reservation(1))

    def test_invalid_caps_rejected_without_creating_ledger(self):
        for amount in (-1, 15_000_001, True, 15.0, "15", None):
            ledger = BudgetLedger(self.directory / "invalid")
            with self.subTest(amount=amount):
                self.error("BUDGET_INPUT", ledger.create, "s", cap_microdollars=amount)
                self.assertFalse(ledger.path.exists())

    def test_exact_token_cache_tool_estimate_and_conservative_rounding(self):
        self.assertEqual(estimate_microdollars(PRICES, LIMITS), 2200)
        prices = deepcopy(PRICES)
        prices["microdollars_per_million_tokens"] = dict.fromkeys(LIMITS.keys() - {"tool_calls"}, 1)
        prices["microdollars_per_tool_call"] = {"lookup": 7}
        limits = {"input_tokens": 1, "cached_input_tokens": 1, "output_tokens": 1, "tool_calls": {"lookup": 2}}
        self.assertEqual(estimate_microdollars(prices, limits), 17)

    def test_unknown_prices_currency_unbounded_and_float_usage_fail_closed(self):
        variants = []
        value = reservation(); value["pricing"]["currency"] = "CAD"; variants.append(("BUDGET_CURRENCY", value))
        value = reservation(); value["limits"]["tool_calls"]["unknown"] = 1; variants.append(("BUDGET_PRICING_UNKNOWN", value))
        for invalid in (True, 0.1, None, -1, float("nan"), float("inf"), MAX_INTEGER + 1):
            value = reservation(); value["limits"]["output_tokens"] = invalid; variants.append(("BUDGET_INPUT", value))
        value = reservation(); value["pricing"]["version"] = ""; variants.append(("BUDGET_INPUT", value))
        value = reservation(); del value["pricing"]["microdollars_per_million_tokens"]["output_tokens"]; variants.append(("BUDGET_INPUT", value))
        for code, value in variants:
            with self.subTest(value=value):
                self.error(code, self.ledger.reserve, "bad", **value)
        self.assertEqual(self.ledger.status()["request_count"], 0)

    def test_reservation_before_dispatch_and_reopen_is_not_dispatch(self):
        first = self.ledger.reserve("r1", **reservation())
        self.assertTrue(first["dispatch_allowed"])
        self.assertFalse(first["idempotent"])
        self.assertEqual(BudgetLedger(self.directory).status()["outstanding_microdollars"], 2200)
        again = BudgetLedger(self.directory).reserve("r1", **reservation())
        self.assertFalse(again["dispatch_allowed"])
        self.assertTrue(again["idempotent"])
        self.assertEqual(again["budget"]["revision"], first["budget"]["revision"])

    def test_idempotency_binds_payload_provider_model_version_price_and_limits(self):
        self.ledger.reserve("r1", **reservation())
        original = self.ledger.path.read_bytes()
        for field in ("payload_sha256", "provider", "model", "model_version", "pricing", "limits"):
            value = reservation()
            if field == "payload_sha256": value[field] = "b" * 64
            elif field == "pricing": value[field]["version"] = "new-price-version"
            elif field == "limits": value[field]["input_tokens"] += 1
            else: value[field] += "-changed"
            with self.subTest(field=field):
                self.error("BUDGET_REQUEST_CONFLICT", self.ledger.reserve, "r1", **value)
                self.assertEqual(original, self.ledger.path.read_bytes())

    def test_spent_plus_outstanding_never_overreserves(self):
        self.ledger.reserve("r1", **reservation(10_000_000))
        self.ledger.settle("r1", actual_microdollars=8_000_000, evidence_id="invoice-1")
        self.ledger.reserve("r2", **reservation(7_000_000))
        self.error("BUDGET_EXHAUSTED", self.ledger.reserve, "r3", **reservation(1))
        self.assertEqual(self.ledger.status()["remaining_microdollars"], 0)

    def test_unknown_timeout_restart_retains_reservation(self):
        self.ledger.reserve("r1", **reservation(15_000_000))
        self.ledger.mark_unknown("r1")
        value = BudgetLedger(self.directory).status()
        self.assertEqual(value["outstanding_microdollars"], 15_000_000)
        self.assertEqual(value["requests"]["r1"]["state"], "unknown")
        self.assertTrue(self.ledger.mark_unknown("r1")["idempotent"])
        self.error("BUDGET_EXHAUSTED", self.ledger.reserve, "r2", **reservation(1))

    def test_authoritative_no_charge_is_explicit_and_terminal(self):
        self.ledger.reserve("r1", **reservation())
        self.ledger.mark_unknown("r1")
        for disposition in ("timeout", "cancelled", "retry_exhausted", "", None):
            self.error("BUDGET_DISPOSITION", self.ledger.resolve_no_charge, "r1", evidence_id="e1", disposition=disposition)
        self.error("BUDGET_DISPOSITION", self.ledger.settle, "r1", actual_microdollars=0, evidence_id="guess")
        self.error("BUDGET_INPUT", self.ledger.resolve_no_charge, "r1", evidence_id="", disposition="provider_confirmed_no_charge")
        value = self.ledger.resolve_no_charge("r1", evidence_id="provider-reconciliation-1", disposition="provider_confirmed_no_charge")
        self.assertEqual(value["budget"]["outstanding_microdollars"], 0)
        self.assertFalse(self.ledger.reserve("r1", **reservation())["dispatch_allowed"])
        self.assertTrue(self.ledger.resolve_no_charge("r1", evidence_id="provider-reconciliation-1", disposition="provider_confirmed_no_charge")["idempotent"])
        self.error("BUDGET_SETTLEMENT_CONFLICT", self.ledger.settle, "r1", actual_microdollars=1, evidence_id="different")

    def test_cancelled_before_dispatch_requires_evidence(self):
        self.ledger.reserve("r1", **reservation())
        row = self.ledger.resolve_no_charge("r1", evidence_id="transport-proved-never-sent", disposition="cancelled_before_dispatch")
        self.assertEqual(row["state"], "no_charge")
        self.assertEqual(row["budget"]["remaining_microdollars"], 15_000_000)

    def test_final_settlement_idempotency_and_double_charge_conflicts(self):
        self.ledger.reserve("r1", **reservation())
        self.ledger.settle("r1", actual_microdollars=2000, evidence_id="invoice-1")
        again = BudgetLedger(self.directory).settle("r1", actual_microdollars=2000, evidence_id="invoice-1")
        self.assertTrue(again["idempotent"])
        self.assertEqual(again["budget"]["spent_microdollars"], 2000)
        for actual, evidence in ((2001, "invoice-1"), (2000, "invoice-2")):
            self.error("BUDGET_SETTLEMENT_CONFLICT", self.ledger.settle, "r1", actual_microdollars=actual, evidence_id=evidence)
        self.error("BUDGET_SETTLEMENT_CONFLICT", self.ledger.resolve_no_charge, "r1", evidence_id="invoice-1", disposition="provider_confirmed_no_charge")

    def test_overrun_below_cap_still_blocks_new_calls_but_allows_reconciliation(self):
        self.ledger.reserve("r1", **reservation(100))
        self.ledger.reserve("r2", **reservation(100))
        row = self.ledger.settle("r1", actual_microdollars=101, evidence_id="provider-overrun")
        self.assertTrue(row["budget"]["blocked"])
        self.assertEqual(row["budget"]["spent_microdollars"], 101)
        self.assertEqual(row["budget"]["outstanding_microdollars"], 100)
        self.error("BUDGET_BLOCKED", BudgetLedger(self.directory).reserve, "r3", **reservation(1))
        self.ledger.settle("r2", actual_microdollars=50, evidence_id="provider-second")
        self.assertTrue(self.ledger.status()["blocked"])
        self.assertEqual(self.ledger.status()["spent_microdollars"], 151)

    def test_charge_above_entire_cap_and_unexpected_tool_is_not_lost(self):
        self.ledger.reserve("r1", **reservation(1))
        usage = {"input_tokens": 0, "cached_input_tokens": 0, "output_tokens": 1, "tool_calls": {"unexpected-billed-tool": 1}}
        row = self.ledger.settle("r1", actual_microdollars=16_000_000, evidence_id="provider-final-bill", usage=usage)
        self.assertEqual(row["budget"]["spent_microdollars"], 16_000_000)
        self.assertEqual(row["budget"]["remaining_microdollars"], 0)
        self.assertTrue(BudgetLedger(self.directory).status()["blocked"])

    def test_administrative_freeze_survives_restart_and_does_not_drop_liability(self):
        self.ledger.reserve("r1", **reservation(100))
        self.ledger.freeze("uncertain_provider_usage_over_bound")
        reopened = BudgetLedger(self.directory)
        self.error("BUDGET_BLOCKED", reopened.reserve, "r2", **reservation(1))
        self.assertEqual(reopened.status()["outstanding_microdollars"], 100)
        reopened.resolve_no_charge("r1", evidence_id="provider-no-charge", disposition="provider_confirmed_no_charge")
        self.assertTrue(reopened.status()["blocked"])

    def test_missing_requests_and_invalid_charge_do_not_write(self):
        original = self.ledger.path.read_bytes()
        self.error("BUDGET_REQUEST_UNKNOWN", self.ledger.mark_unknown, "missing")
        self.error("BUDGET_REQUEST_UNKNOWN", self.ledger.settle, "missing", actual_microdollars=1, evidence_id="invoice")
        for value in (-1, True, 1.0, None):
            self.error("BUDGET_INPUT", self.ledger.settle, "missing", actual_microdollars=value, evidence_id="invoice")
        self.assertEqual(original, self.ledger.path.read_bytes())

    def test_checksum_corruption_and_duplicate_json_never_reset_ledger(self):
        value = self.ledger.path.read_text()
        self.ledger.path.write_text(value.replace('"cap_microdollars":15000000', '"cap_microdollars":15000001'))
        self.error("BUDGET_CORRUPT", self.ledger.status)
        self.error("BUDGET_CORRUPT", self.ledger.create, "setup-session")
        self.ledger.path.write_text('{"schema_version":1,"schema_version":1}')
        self.error("BUDGET_CORRUPT", self.ledger.status)

    def test_semantic_corruption_fails_even_with_valid_checksum(self):
        self.ledger.reserve("r1", **reservation())
        original = json.loads(self.ledger.path.read_text())
        for mutate in (lambda d: d["requests"]["r1"].update(reserved_microdollars=1),
                       lambda d: d.update(cap_microdollars=1),
                       lambda d: d["requests"]["r1"].update(state="unknown-state"),
                       lambda d: d.update(schema_version=True)):
            value = deepcopy(original); value.pop("sha256"); mutate(value)
            self.ledger.path.write_bytes(canonical({**value, "sha256": digest(value)}))
            self.error("BUDGET_CORRUPT", self.ledger.status)

    def test_failed_atomic_replace_preserves_previous_reservation_and_no_dispatch(self):
        self.ledger.reserve("r1", **reservation())
        before = self.ledger.path.read_bytes()
        with patch("controller_config.service._replace", side_effect=PermissionError("injected")):
            self.error("BUDGET_IO", self.ledger.reserve, "r2", **reservation())
        self.assertEqual(self.ledger.path.read_bytes(), before)
        self.assertEqual(self.ledger.status()["outstanding_microdollars"], 2200)
        self.assertEqual(list(self.directory.glob("*.tmp")), [])

    def test_lost_write_acknowledgement_cannot_duplicate_dispatch(self):
        from controller_config.setup_budget import atomic_write
        def write_then_fail(path, value):
            atomic_write(path, value)
            raise OSError("acknowledgement lost after durable replacement")
        with patch("controller_config.setup_budget.atomic_write", side_effect=write_then_fail):
            self.error("BUDGET_IO", self.ledger.reserve, "r1", **reservation())
        again = BudgetLedger(self.directory).reserve("r1", **reservation())
        self.assertFalse(again["dispatch_allowed"])
        self.assertEqual(again["budget"]["outstanding_microdollars"], 2200)

    def test_live_process_lock_refuses_and_process_death_releases_it(self):
        code = "from controller_config.setup_budget import BudgetLedger; import os,sys; l=BudgetLedger(sys.argv[1]);\nwith l._lock():\n print('locked',flush=True)\n sys.stdin.readline()\n os._exit(7)\n"
        process = subprocess.Popen([sys.executable, "-B", "-c", code, str(self.directory)], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(), "locked")
            self.error("BUDGET_BUSY", self.ledger.reserve, "r1", **reservation())
            process.stdin.write("exit\n"); process.stdin.flush()
            process.communicate(timeout=10)
            self.assertEqual(process.returncode, 7)
            self.assertTrue(self.ledger.reserve("r1", **reservation())["dispatch_allowed"])
        finally:
            if process.poll() is None: process.kill(); process.communicate()

    def test_empty_lock_file_is_not_written_before_ownership(self):
        lock_path = Path(str(self.ledger.path) + ".lock")
        lock_path.write_bytes(b"")
        code = "import os,sys; f=os.open(sys.argv[1],os.O_RDWR);\nif os.name=='nt':\n import msvcrt; msvcrt.locking(f,msvcrt.LK_NBLCK,1)\nelse:\n import fcntl; fcntl.flock(f,fcntl.LOCK_EX|fcntl.LOCK_NB)\nprint('locked',flush=True)\nsys.stdin.readline()\nos.close(f)\n"
        process = subprocess.Popen([sys.executable, "-B", "-c", code, str(lock_path)], cwd=ROOT, stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            self.assertEqual(process.stdout.readline().strip(), "locked")
            self.error("BUDGET_BUSY", self.ledger.reserve, "r1", **reservation())
            self.assertEqual(lock_path.stat().st_size, 0)
            process.stdin.write("release\n"); process.stdin.flush()
            process.communicate(timeout=10)
            self.assertEqual(process.returncode, 0)
            self.assertTrue(self.ledger.reserve("r1", **reservation())["dispatch_allowed"])
            self.assertEqual(lock_path.stat().st_size, 1)
        finally:
            if process.poll() is None: process.kill(); process.communicate()

    def test_process_death_after_reservation_retains_unknown_liability(self):
        args = reservation()
        code = "from controller_config.setup_budget import BudgetLedger; import json,os,sys; BudgetLedger(sys.argv[1]).reserve('r1', **json.loads(sys.argv[2])); os._exit(7)"
        result = subprocess.run([sys.executable, "-B", "-c", code, str(self.directory), json.dumps(args)], cwd=ROOT, capture_output=True, timeout=10)
        self.assertEqual(result.returncode, 7, result.stderr)
        self.assertEqual(self.ledger.status()["outstanding_microdollars"], 2200)
        self.assertFalse(self.ledger.reserve("r1", **args)["dispatch_allowed"])

    def test_concurrent_distinct_requests_cannot_overspend(self):
        ledger = BudgetLedger(self.directory / "concurrent")
        ledger.create("race", cap_microdollars=1_000_000)
        context = multiprocessing.get_context("spawn")
        start, results = context.Event(), context.Queue()
        processes = [context.Process(target=concurrent_reserve, args=(str(ledger.path), f"r{i}", start, results)) for i in range(6)]
        try:
            for process in processes: process.start()
            start.set()
            rows = [results.get(timeout=20) for _ in processes]
            for process in processes: process.join(20); self.assertEqual(process.exitcode, 0)
            self.assertEqual(sum(row[2] for row in rows), 1)
            self.assertEqual(sum(row[1] == "BUDGET_EXHAUSTED" for row in rows), 5)
            self.assertEqual(ledger.status()["outstanding_microdollars"], 600_000)
        finally:
            for process in processes:
                if process.is_alive(): process.terminate(); process.join(5)
            results.close(); results.join_thread()

    def test_concurrent_duplicate_id_grants_dispatch_once(self):
        context = multiprocessing.get_context("spawn")
        start, results = context.Event(), context.Queue()
        processes = [context.Process(target=concurrent_reserve, args=(str(self.ledger.path), "same", start, results)) for _ in range(4)]
        try:
            for process in processes: process.start()
            start.set()
            rows = [results.get(timeout=20) for _ in processes]
            for process in processes: process.join(20); self.assertEqual(process.exitcode, 0)
            self.assertEqual(sum(row[2] for row in rows), 1)
            self.assertEqual(self.ledger.status()["request_count"], 1)
            self.assertEqual(self.ledger.status()["outstanding_microdollars"], 600_000)
        finally:
            for process in processes:
                if process.is_alive(): process.terminate(); process.join(5)
            results.close(); results.join_thread()

    def test_maximum_inventory_leaves_room_for_all_settlements(self):
        # Bound actual serialized worst-case rows, including JSON escaping, so
        # accepting a reservation cannot fill storage needed for final bills.
        label = "\\\"" * 64
        tools = {str(i) + label[:126]: MAX_INTEGER for i in range(16)}
        row = {"binding": {"payload_sha256": "a" * 64, "provider": label, "model": label, "model_version": label,
               "pricing": {"currency": "USD", "version": label, "microdollars_per_million_tokens": dict.fromkeys(("input_tokens", "cached_input_tokens", "output_tokens"), MAX_INTEGER), "microdollars_per_tool_call": tools},
               "limits": {"input_tokens": MAX_INTEGER, "cached_input_tokens": MAX_INTEGER, "output_tokens": MAX_INTEGER, "tool_calls": tools}},
               "binding_sha256": "f" * 64, "reserved_microdollars": MAX_INTEGER, "state": "settled",
               "settlement": {"actual_microdollars": MAX_INTEGER, "evidence_id": label, "disposition": "provider_charge",
               "usage": {"input_tokens": MAX_INTEGER, "cached_input_tokens": MAX_INTEGER, "output_tokens": MAX_INTEGER, "tool_calls": tools}}}
        record = {"requests": {str(i) + label[:125]: row for i in range(MAX_REQUESTS)}, "session_id": label}
        self.assertLess(len(canonical(record)) + 2000, MAX_BYTES)

    def test_discovery_is_json_and_contains_no_provider_or_motion_authority(self):
        schema = BudgetLedger.schema()
        self.assertEqual(schema, BudgetLedger.discovery())
        self.assertEqual(schema["maximum_session_cap_microdollars"], MAX_CAP_MICRODOLLARS)
        self.assertFalse(schema["duplicate_dispatch_allowed"])
        self.assertFalse(self.ledger.status()["machine_authority"])
        json.dumps(schema, allow_nan=False)


if __name__ == "__main__":
    unittest.main()
