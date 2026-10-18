"""Disconnected, temporary-only IS-2 setup workflow and adversarial checks."""
from copy import deepcopy
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import threading
import unittest
from unittest.mock import patch

from controller_config.model import ConfigurationError, capabilities as legacy_capabilities
from controller_config.service import _seal, canonical, digest
from controller_config.setup_service import (SetupService, capabilities, draft_template,
    equipment_profiles, example_draft, schema, validate_draft, _exclusive_lock as real_exclusive_lock)


class SetupServiceTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.path = Path(self.temp.name) / "setup.json"
        self.service = SetupService(self.path)

    def assertCode(self, code, callback):
        with self.assertRaises(ConfigurationError) as caught:
            callback()
        self.assertEqual(caught.exception.code, code)

    def ready(self, profile="sim-mill-3axis"):
        self.service.initialize()
        draft = example_draft(profile)
        self.service.save_draft(draft, self.service.status()["revision"])
        return draft

    @contextmanager
    def after_first_unlock(self, callback):
        """Deterministically schedule another client before the first call returns."""
        fired = False
        @contextmanager
        def interleave(path):
            nonlocal fired
            with real_exclusive_lock(path):
                yield
            if not fired:
                fired = True
                callback()
        with patch("controller_config.setup_service._exclusive_lock", interleave):
            yield
        self.assertTrue(fired)

    def test_status_discovery_never_creates_store(self):
        self.assertFalse(self.service.status()["initialized"])
        self.assertFalse(self.path.exists())
        self.assertFalse(capabilities()["identity"]["observed"])
        self.assertFalse(capabilities()["physical_pin_guidance"])

    def test_full_resource_manifest_preserves_all_motors_and_io(self):
        caps = capabilities()
        resources = caps["resources"]
        self.assertEqual({k: sum(r["kind"] == k for r in resources)
                          for k in ("step_dir", "abz", "digital_input", "digital_output")},
                         {"step_dir": 12, "abz": 4, "digital_input": 24, "digital_output": 16})
        motors = [r for r in resources if r["kind"] == "step_dir"]
        self.assertEqual(motors[0]["id"], "SIM.M0")
        self.assertEqual(motors[-1]["label"], "M12")
        self.assertEqual(len({r["enable_resource"] for r in motors}), 12)
        self.assertEqual(len({r["alarm_resource"] for r in motors}), 12)
        self.assertTrue(all(t.startswith("SIM.") for r in resources for t in r["terminals"]))
        self.assertTrue(all(not r["observed"] and not r["physically_qualified"] for r in resources))
        caps["resources"].clear()
        self.assertEqual(len(capabilities()["resources"]), 56)
        self.assertEqual(sum(r["function"] == "step_dir" for r in legacy_capabilities()["resources"]), 6)

    def test_template_facts_missing_examples_opt_in_and_profiles(self):
        for profile, count in (("sim-mill-3axis", 3), ("sim-gantry-4motor", 4),
                               ("sim-machine-8motor", 8), ("sim-machine-12motor", 12)):
            with self.subTest(profile=profile):
                empty = validate_draft(draft_template(profile))
                self.assertEqual(len(empty["missing_facts"]), count * 6)
                full = validate_draft(example_draft(profile), require_complete=True)
                self.assertTrue(full["valid"])
                self.assertEqual(len(full["calculations"]), count)
                self.assertFalse(full["physical_commissioning_complete"])
        gantry = example_draft("sim-gantry-4motor")
        self.assertEqual([m["axis"] for m in gantry["motors"]], ["x", "x", "y", "z"])

    def test_deterministic_scale_ratio_units_and_per_drive_settings(self):
        draft = example_draft("sim-mill-3axis")
        draft["motors"][0].update(gear_motor_revolutions=3, gear_load_revolutions=2)
        draft["motors"][1].update(unit="in", travel_per_load_revolution=1, max_velocity_units_per_second=0.25,
                                   dir_inverted=True, step_high_ns=10000)
        checked = validate_draft(draft, require_complete=True)
        self.assertEqual(checked["calculations"][0]["steps_per_unit"], 960)
        self.assertEqual(checked["calculations"][0]["required_step_rate_hz"], 9600)
        self.assertAlmostEqual(checked["calculations"][1]["steps_per_mm"], 3200/25.4)
        self.assertEqual(checked["calculations"][1]["maximum_velocity_mm_per_second"], 6.35)
        self.assertEqual(checked["calculations"][2]["steps_per_unit"], 640)

    def test_unknown_equipment_and_machine_not_faked(self):
        draft = example_draft("sim-mill-3axis")
        draft["motors"][0]["equipment_profile"] = "real-drive-by-similar-name"
        checked = validate_draft(draft)
        self.assertEqual(checked["blockers"][0]["code"], "SETUP_UNSUPPORTED_EQUIPMENT")
        self.assertCode("SETUP_UNSUPPORTED_EQUIPMENT", lambda: validate_draft(draft, True))
        draft["profile_id"] = "real-machine"
        self.assertEqual(validate_draft(draft)["blockers"][0]["code"], "SETUP_UNSUPPORTED_PROFILE")
        self.assertCode("SETUP_UNSUPPORTED_PROFILE", lambda: draft_template("real-machine"))

    def test_resource_and_topology_conflicts(self):
        draft = example_draft("sim-gantry-4motor")
        draft["motors"][1]["resource"] = "SIM.M0"
        self.assertIn("SETUP_RESOURCE_CONFLICT", [i["code"] for i in validate_draft(draft)["blockers"]])
        draft["motors"][1]["resource"] = "XM1"
        self.assertIn("SETUP_RESOURCE", [i["code"] for i in validate_draft(draft)["blockers"]])
        draft["motors"].pop()
        self.assertIn("SETUP_TOPOLOGY", [i["code"] for i in validate_draft(draft)["blockers"]])

    def test_timing_rate_boundaries_and_no_rounding_bypass(self):
        draft = example_draft("sim-mill-3axis")
        motor = draft["motors"][0]
        motor["max_velocity_units_per_second"] = 156.25  # 640 * 156.25 = 100000
        self.assertTrue(validate_draft(draft)["valid"])
        motor["max_velocity_units_per_second"] = 156.2500000001
        self.assertCode("SETUP_RATE_LIMIT", lambda: validate_draft(draft, True))
        motor["max_velocity_units_per_second"] = 10
        motor["step_high_ns"] = 2499
        self.assertCode("SETUP_TIMING", lambda: validate_draft(draft, True))
        motor["step_high_ns"] = 1000000
        self.assertCode("SETUP_RATE_LIMIT", lambda: validate_draft(draft, True))

    def test_all_output_groups_input_voltage_and_encoder_counts(self):
        draft = example_draft("sim-machine-12motor")
        draft["outputs"] = [{"resource": f"SIM.DO{i}", "role": f"load{i}",
            "equipment_profile": "sim-smart-output-v1", "voltage_v": 24, "current_a": 0.5} for i in range(16)]
        draft["inputs"] = [{"resource": "SIM.DI0", "role": "home", "equipment_profile": "sim-24v-switch-v1", "voltage_v": 24}]
        draft["encoders"] = [{"resource": "SIM.ABZ0", "role": "x_feedback", "equipment_profile": "sim-abz-5v-v1", "counts_per_revolution": 4000}]
        self.assertTrue(validate_draft(draft)["valid"])
        self.assertTrue(all(g["selected_current_a"] == 2 for g in validate_draft(draft)["output_groups"]))
        draft["outputs"][0]["current_a"] = 0.5000001
        codes = [i["code"] for i in validate_draft(draft)["blockers"]]
        self.assertIn("SETUP_CURRENT", codes)
        self.assertIn("SETUP_GROUP_CURRENT", codes)
        draft["inputs"][0]["voltage_v"] = 12
        self.assertIn("SETUP_VOLTAGE", [i["code"] for i in validate_draft(draft)["blockers"]])
        draft["encoders"][0]["counts_per_revolution"] = None
        self.assertEqual(validate_draft(draft)["missing_facts"][0]["path"], "$.encoders[0].counts_per_revolution")

    def test_strict_values_and_invented_authority(self):
        for field, value, code in (("microsteps", True, "SETUP_NUMBER"), ("microsteps", 16.0, "SETUP_NUMBER"),
            ("gear_load_revolutions", 0, "SETUP_NUMBER"), ("motor_steps_per_revolution", 10**1000, "SETUP_NUMBER"),
            ("max_velocity_units_per_second", float("nan"), "SETUP_NUMBER"), ("dir_inverted", 1, "SETUP_BOOLEAN"),
            ("unit", "inch?", "SETUP_UNIT")):
            with self.subTest(field=field, value=str(value)[:30]):
                draft = example_draft("sim-mill-3axis")
                draft["motors"][0][field] = value
                self.assertCode(code, lambda: validate_draft(draft))
        for field in ("physical_commissioning_complete", "homed", "motion_authorized", "commands"):
            draft = example_draft("sim-mill-3axis")
            draft[field] = True
            self.assertCode("SETUP_SCHEMA", lambda: validate_draft(draft))

    def test_draft_resume_missing_facts_and_revision_conflict(self):
        self.service.initialize()
        draft = draft_template("sim-mill-3axis")
        draft["motors"][0]["microsteps"] = 16
        result = self.service.save_draft(draft, 0)
        self.assertEqual(result["revision"], 1)
        reopened = SetupService(self.path).status()
        self.assertEqual(reopened["draft"], draft)
        self.assertEqual(len(reopened["validation"]["missing_facts"]), 17)
        self.assertCode("SETUP_STALE", lambda: self.service.save_draft(draft, 0))
        self.assertCode("SETUP_MISSING_FACT", lambda: self.service.preview())

    def test_preview_read_only_commit_idempotent_restart_and_restore(self):
        draft = self.ready()
        original = self.path.read_bytes()
        plan = self.service.preview()
        self.assertEqual(self.path.read_bytes(), original)
        one = self.service.commit(plan, "request-1")
        saved = self.path.read_bytes()
        repeated = SetupService(self.path).commit(plan, "request-1")
        self.assertTrue(repeated["replayed"])
        self.assertEqual(repeated["generation"], one["generation"])
        self.assertEqual(self.path.read_bytes(), saved)
        self.assertFalse(repeated["motion_authorized"])
        changed = deepcopy(draft)
        changed["motors"][0]["microsteps"] = 8
        self.service.save_draft(changed, one["revision"])
        two = self.service.commit(self.service.preview(), "request-2")
        restore = self.service.restore_preview(1)
        self.assertEqual(restore["candidate"], draft)
        three = self.service.commit(restore, "request-3")
        self.assertEqual((one["generation"], two["generation"], three["generation"]), (1, 2, 3))
        self.assertEqual(self.service.status()["active"]["draft"], draft)
        self.assertEqual(self.service.request_result("request-1")["current_revision"], three["revision"])
        self.assertCode("SETUP_IDEMPOTENCY_CONFLICT", lambda: self.service.commit(restore, "request-1"))
        self.assertCode("SETUP_GENERATION_UNKNOWN", lambda: self.service.restore_preview(99))

    def test_tampered_preview_and_resealed_invalid_candidate(self):
        self.ready()
        plan = self.service.preview()
        plan["candidate"]["motors"][0]["microsteps"] = 8
        self.assertCode("SETUP_PLAN_CHANGED", lambda: self.service.commit(plan, "edited"))
        plan["candidate"]["physical_commissioning_complete"] = True
        plan["plan_sha256"] = digest({k: v for k, v in plan.items() if k != "plan_sha256"})
        self.assertCode("SETUP_SCHEMA", lambda: self.service.commit(plan, "injected"))
        plan = self.service.preview()
        plan["validation"]["calculations"][0]["steps_per_unit"] = 1
        plan["plan_sha256"] = digest({k: v for k, v in plan.items() if k != "plan_sha256"})
        self.assertCode("SETUP_PLAN_CHANGED", lambda: self.service.commit(plan, "forged-derived"))

    def test_epoch_and_foreign_store_reject_old_plans(self):
        self.ready()
        plan = self.service.preview()
        self.service.restart_epoch(self.service.status()["revision"])
        self.assertCode("SETUP_STALE", lambda: self.service.commit(plan, "old-epoch"))
        other = SetupService(Path(self.temp.name) / "other.json")
        other.initialize()
        self.assertCode("SETUP_STALE", lambda: other.commit(plan, "other"))

    def test_invalid_actor_no_write_and_interrupted_atomic_commit_keeps_old_state(self):
        self.ready()
        plan = self.service.preview()
        before = self.path.read_bytes()
        self.assertCode("ACTOR", lambda: self.service.commit(plan, "bad-actor", actor=""))
        self.assertEqual(self.path.read_bytes(), before)
        with patch("controller_config.service._replace", side_effect=OSError("simulated failed replacement")):
            with self.assertRaises(OSError):
                self.service.commit(plan, "interrupted")
        self.assertEqual(self.path.read_bytes(), before)
        self.assertFalse(Path(str(self.path) + ".lock").exists())
        self.assertEqual(list(self.path.parent.glob("*.tmp")), [])
        self.assertEqual(self.service.commit(plan, "interrupted")["generation"], 1)

    def test_concurrent_clients_cannot_commit_twice(self):
        self.ready()
        plan = self.service.preview()
        start = threading.Barrier(2)
        def worker(request_id):
            start.wait()
            try:
                return SetupService(self.path).commit(plan, request_id)
            except ConfigurationError as error:
                return error.code
        with ThreadPoolExecutor(max_workers=2) as pool:
            results = list(pool.map(worker, ("client-a", "client-b")))
        successes = [r for r in results if isinstance(r, dict)]
        failures = [r for r in results if isinstance(r, str)]
        self.assertEqual(len(successes), 1)
        self.assertEqual(len(failures), 1)
        self.assertIn(failures[0], ("STORE_BUSY", "SETUP_STALE"))
        self.assertEqual(self.service.status()["generation"], 1)

    def test_live_lock_refuses_writer_and_process_death_allows_resume(self):
        draft = self.ready()
        # A real child retains the OS lock until forcibly terminated. No mocked
        # unlock/finally runs, so this proves release on death on the host OS.
        script = """
import sys
from controller_config.setup_service import _exclusive_lock
with _exclusive_lock(sys.argv[1]):
    print('locked', flush=True)
    sys.stdin.read()
"""
        child = subprocess.Popen([sys.executable, "-B", "-c", script, str(self.path)],
            cwd=Path(__file__).resolve().parents[1], stdin=subprocess.PIPE,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        try:
            # A bounded waiter prevents a broken child from hanging the suite.
            with ThreadPoolExecutor(max_workers=1) as pool:
                line = pool.submit(child.stdout.readline)
                try:
                    self.assertEqual(line.result(timeout=10), "locked\n")
                except Exception:
                    child.kill()
                    raise
            before = self.path.read_bytes()
            lock_path = Path(str(self.path) + ".setup.lock")
            original_lock = lock_path.stat()
            changed = deepcopy(draft)
            changed["machine_name"] = "Resumed after process death"
            revision = self.service.status()["revision"]
            self.assertCode("STORE_BUSY", lambda: self.service.save_draft(changed, revision))
            self.assertEqual(self.path.read_bytes(), before)
            child.kill()
            child.wait(timeout=10)
            # The stable file remains, but its old process owns no OS lock.
            self.assertTrue(lock_path.exists())
            self.assertEqual(lock_path.stat().st_ino, original_lock.st_ino)
            result = SetupService(self.path).save_draft(changed, revision)
            self.assertEqual(result["draft"], changed)
            self.assertEqual(result["revision"], revision + 1)
            self.assertEqual(lock_path.stat().st_ino, original_lock.st_ino)
        finally:
            if child.poll() is None:
                child.kill()
            child.communicate(timeout=10)

    def test_previous_sentinel_lock_fails_closed_without_deleting_it(self):
        self.ready()
        before = self.path.read_bytes()
        legacy = Path(str(self.path) + ".lock")
        legacy.write_text("older-writer", encoding="ascii")
        self.assertCode("STORE_BUSY", lambda: self.service.restart_epoch(self.service.status()["revision"]))
        self.assertEqual(legacy.read_text(encoding="ascii"), "older-writer")
        self.assertEqual(self.path.read_bytes(), before)

    def test_save_reply_is_own_snapshot_when_another_client_writes_after_unlock(self):
        original = self.ready()
        rival = SetupService(self.path)
        for no_change in (False, True):
            with self.subTest(no_change=no_change):
                mine = deepcopy(self.service.status()["draft"])
                if not no_change:
                    mine["machine_name"] = "Client A"
                other = deepcopy(original)
                other["machine_name"] = "Client B latest" if no_change else "Client B"
                before = self.service.status()["revision"]
                def write_other():
                    rival.save_draft(other, rival.status()["revision"])
                with self.after_first_unlock(write_other):
                    reply = self.service.save_draft(mine, before)
                self.assertEqual(reply["draft"], mine)
                self.assertEqual(reply["revision"], before + (0 if no_change else 1))
                self.assertEqual(rival.status()["draft"], other)
                self.assertCode("SETUP_STALE", lambda: self.service.save_draft(mine, reply["revision"]))
                self.assertEqual(rival.status()["draft"], other)

    def test_initialize_reply_cannot_adopt_a_later_clients_draft_or_revision(self):
        rival = SetupService(self.path)
        for existing in (False, True):
            with self.subTest(existing=existing):
                before = self.service.status()
                other = example_draft("sim-mill-3axis")
                other["machine_name"] = "Client B existing" if existing else "Client B first"
                def write_other():
                    rival.save_draft(other, rival.status()["revision"])
                with self.after_first_unlock(write_other):
                    reply = self.service.initialize()
                self.assertEqual(reply["revision"], before["revision"])
                self.assertEqual(reply["draft"], before["draft"])
                self.assertCode("SETUP_STALE", lambda: self.service.save_draft(other, reply["revision"]))

    def test_restart_reply_is_own_epoch_when_another_restart_follows_unlock(self):
        self.ready()
        rival = SetupService(self.path)
        before = self.service.status()
        def restart_other():
            rival.restart_epoch(rival.status()["revision"])
        with self.after_first_unlock(restart_other):
            reply = self.service.restart_epoch(before["revision"])
        current = rival.status()
        self.assertEqual(reply["revision"], before["revision"] + 1)
        self.assertNotEqual(reply["epoch"], current["epoch"])
        self.assertCode("SETUP_STALE", lambda: self.service.save_draft(reply["draft"], reply["revision"]))

    def test_restore_current_generation_discards_pending_draft_without_new_generation(self):
        original = self.ready()
        first = self.service.commit(self.service.preview(), "first")
        changed = deepcopy(original)
        changed["machine_name"] = "Pending uncommitted edit"
        self.service.save_draft(changed, first["revision"])
        restored = self.service.commit(self.service.restore_preview(1), "discard-draft")
        self.assertTrue(restored["changed"])
        self.assertTrue(restored["draft_changed"])
        self.assertFalse(restored["configuration_changed"])
        self.assertEqual(restored["generation"], 1)
        self.assertEqual(self.service.status()["draft"], original)

    def test_foreign_or_corrupt_existing_store_never_overwritten(self):
        self.path.write_bytes(b'user machine configuration')
        before = self.path.read_bytes()
        with self.assertRaises(ConfigurationError):
            self.service.initialize()
        self.assertEqual(self.path.read_bytes(), before)
        self.path.write_text(json.dumps(_seal({"schema": "old-schema"})), encoding="utf-8")
        before = self.path.read_bytes()
        with self.assertRaises(ConfigurationError):
            self.service.initialize()
        self.assertEqual(self.path.read_bytes(), before)

    def test_catalog_changes_and_store_derived_tampering_are_refused(self):
        self.ready()
        self.service.commit(self.service.preview(), "first")
        state = json.loads(self.path.read_text(encoding="utf-8"))
        state.pop("integrity_sha256")
        state["active"]["calculations"][0]["steps_per_unit"] = 1
        self.path.write_bytes(canonical(_seal(state)))
        self.assertCode("SETUP_STORE_FORMAT", self.service.status)
        state["catalog_sha256"] = "0" * 64
        self.path.write_bytes(canonical(_seal(state)))
        self.assertCode("SETUP_CATALOG_CHANGED", self.service.status)

    def test_numeric_representation_changes_are_not_silently_lost(self):
        draft = self.ready()
        self.service.commit(self.service.preview(), "first")
        revision = self.service.status()["revision"]
        draft["motors"][0]["gear_motor_revolutions"] = 1.0
        self.assertEqual(self.service.save_draft(draft, revision)["revision"], revision + 1)
        result = self.service.commit(self.service.preview(), "numeric-representation")
        self.assertTrue(result["changed"])
        self.assertEqual(result["configuration_sha256"], digest(self.service.status()["active"]["draft"]))

    def test_switching_profiles_retains_all_twelve_drive_answers_after_reopen(self):
        twelve = self.ready("sim-machine-12motor")
        for index, motor in enumerate(twelve["motors"]):
            motor["microsteps"] = index + 1
        self.service.save_draft(twelve, self.service.status()["revision"])
        smaller = example_draft("sim-mill-3axis")
        self.service.save_draft(smaller, self.service.status()["revision"])
        reopened = SetupService(self.path)
        status = reopened.status()
        self.assertEqual(status["retained_profile_drafts"]["sim-machine-12motor"], twelve)
        restored = status["retained_profile_drafts"]["sim-machine-12motor"]
        reopened.save_draft(restored, status["revision"])
        self.assertEqual(reopened.status()["draft"], twelve)
        self.assertEqual(reopened.status()["retained_profile_drafts"]["sim-mill-3axis"], smaller)
        # Public snapshots are detached from the actual retained store.
        restored["motors"].clear()
        self.assertEqual(len(reopened.status()["draft"]["motors"]), 12)

    def test_direct_commit_profile_switch_retains_pending_answers(self):
        twelve = self.ready("sim-machine-12motor")
        smaller = example_draft("sim-mill-3axis")
        self.service.commit(self.service.preview(smaller), "switch-via-preview")
        self.assertEqual(self.service.status()["retained_profile_drafts"]["sim-machine-12motor"], twelve)

    def test_retained_profile_drafts_validate_identity_and_authority(self):
        self.ready()
        original = json.loads(self.path.read_text(encoding="utf-8"))
        original.pop("integrity_sha256")
        for key, draft, code in (
                ("real-machine", example_draft("sim-mill-3axis"), "SETUP_STORE_FORMAT"),
                ("sim-machine-12motor", example_draft("sim-mill-3axis"), "SETUP_STORE_FORMAT"),
                ("sim-mill-3axis", {**example_draft("sim-mill-3axis"), "homed": True}, "SETUP_SCHEMA")):
            with self.subTest(key=key, code=code):
                state = deepcopy(original)
                state["retained_profile_drafts"] = {key: draft}
                self.path.write_bytes(canonical(_seal(state)))
                self.assertCode(code, self.service.status)

    def test_early_schema_one_without_retained_drafts_has_read_only_compatibility(self):
        self.ready()
        state = json.loads(self.path.read_text(encoding="utf-8"))
        state.pop("integrity_sha256")
        state.pop("retained_profile_drafts")
        self.path.write_bytes(canonical(_seal(state)))
        before = self.path.read_bytes()
        self.assertEqual(self.service.status()["retained_profile_drafts"], {})
        plan = self.service.preview()
        self.assertEqual(self.path.read_bytes(), before)
        self.service.commit(plan, "compatible-commit")
        self.assertEqual(json.loads(self.path.read_text(encoding="utf-8"))["retained_profile_drafts"], {})

    def test_emitted_schema_matches_supported_example_and_has_no_authority_fields(self):
        document = schema()
        self.assertFalse(document["additionalProperties"])
        self.assertEqual(set(document["properties"]), set(example_draft("sim-mill-3axis")))
        self.assertNotIn("homed", document["properties"])
        self.assertTrue(all(not p["physical_qualified"] for p in equipment_profiles().values()))


if __name__ == "__main__":
    unittest.main()
