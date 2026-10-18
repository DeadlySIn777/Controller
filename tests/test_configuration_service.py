import copy
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from controller_config import ConfigurationError, ConfigurationService, RuntimeState
from controller_config.service import _exclusive_lock, atomic_write, digest, export_json, read_json


class ConfigurationServiceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.path = Path(self.temporary.name) / "state.json"
        self.runtime = RuntimeState()
        self.service = ConfigurationService(self.path, lambda: self.runtime)
        self.service.initialize("test")
        self.config = self.service.select_profile("sim-mill-3axis")

    def assert_error(self, code, call):
        with self.assertRaises(ConfigurationError) as caught:
            call()
        self.assertEqual(code, caught.exception.code)

    def applied(self):
        return self.service.apply(self.service.preview(self.config), "test")

    def test_shared_api_select_validate_wire_preview_apply_reopen(self):
        self.assertTrue(self.service.validate(self.config)["valid"])
        wiring = self.service.wiring(self.config)
        self.assertEqual(6, len(wiring["connections"]))
        self.assertTrue(all(row["resource"].startswith("SIM.") for row in wiring["connections"]))
        self.assertTrue(all(not row["physical_wiring_verified"] for row in wiring["connections"]))
        plan = self.service.preview(self.config)
        self.assertEqual(0, self.service.show()["revision"])
        self.assertTrue(plan["changes"])
        self.assertEqual(1, self.service.apply(plan)["revision"])
        self.assertEqual(self.config, ConfigurationService(self.path).show()["configuration"])
        self.assertEqual("apply", self.service.audit()["entries"][-1]["action"])

    def test_latched_pending_checks_and_readiness(self):
        self.applied()
        device = self.service.show()["configuration"]["devices"][0]
        self.assertEqual("none_simulation_only", device["output_owner"])
        self.assertEqual({"requested": False, "observed": "unverified"}, device["readiness"])
        self.assertEqual("unverified", device["calibration"][0]["status"])
        self.assertTrue(all(check["status"] == "pending" for check in device["commissioning_checks"]))

    def test_unknown_key_and_version_rejected(self):
        self.config["run"] = True
        self.assert_error("SCHEMA_KEYS", lambda: self.service.validate(self.config))
        del self.config["run"]
        self.config["schema_version"] = 2
        self.assert_error("SCHEMA_CONST", lambda: self.service.validate(self.config))

    def test_bool_and_nonfinite_quantities_rejected(self):
        for value in (True, False, float("nan"), float("inf"), -float("inf")):
            with self.subTest(value=value):
                config = copy.deepcopy(self.config)
                config["devices"][0]["required_connections"][0]["rate_hz"] = value
                self.assert_error("SCHEMA_TYPE", lambda: self.service.validate(config))

    def test_malformed_direct_api_inputs_have_structured_errors(self):
        for value in (None, [], True, 17, "configuration"):
            with self.subTest(value=value):
                self.assert_error("SCHEMA_TYPE", lambda: self.service.validate(value))
                self.assert_error("PLAN_INVALID", lambda: self.service.apply(value))
                self.assert_error("BACKUP_CORRUPT", lambda: self.service.restore_preview(value))
        for value in ([], {}, None, True):
            self.assert_error("UNKNOWN_PROFILE", lambda: self.service.select_profile(value))
        self.config["devices"][0]["required_connections"][0]["rate_hz"] = 10 ** 1000
        self.assert_error("SCHEMA_RANGE", lambda: self.service.validate(self.config))

    def test_negative_and_wrong_unit_rejected(self):
        self.config["devices"][0]["calibration"][0]["steps_per_unit"] = -1
        self.assert_error("SCHEMA_RANGE", lambda: self.service.validate(self.config))
        self.config = self.service.select_profile("sim-mill-3axis")
        self.config["machine"]["units"] = "inch"
        self.assert_error("SCHEMA_CONST", lambda: self.service.validate(self.config))

    def test_resource_collision_rejected(self):
        self.config["devices"][2]["required_connections"][0]["resource"] = "SIM.M0"
        self.assert_error("RESOURCE_CONFLICT", lambda: self.service.validate(self.config))

    def test_duplicate_device_and_connection_rejected(self):
        self.config["devices"][2]["identity"]["instance_id"] = "x-drive"
        self.assert_error("DEVICE_CONFLICT", lambda: self.service.validate(self.config))
        self.config = self.service.select_profile("sim-mill-3axis")
        self.config["devices"][0]["required_connections"] *= 2
        self.assert_error("CONNECTION_ROLE", lambda: self.service.validate(self.config))

    def test_unknown_resource_rejected(self):
        self.config["devices"][0]["required_connections"][0]["resource"] = "J1.1"
        self.assert_error("UNKNOWN_RESOURCE", lambda: self.service.validate(self.config))

    def test_rating_voltage_rate_and_current_rejected(self):
        for field, value, code in (("voltage_v", 24, "ELECTRICAL_VOLTAGE"),
                                   ("rate_hz", 200000, "ELECTRICAL_LIMIT"),
                                   ("current_a", 0.021, "ELECTRICAL_LIMIT")):
            with self.subTest(field=field):
                config = copy.deepcopy(self.config)
                config["devices"][0]["required_connections"][0][field] = value
                self.assert_error(code, lambda: self.service.validate(config))

    def test_signal_type_rejected(self):
        self.config["devices"][0]["required_connections"][0]["resource"] = "SIM.DI0"
        self.assert_error("ELECTRICAL_TYPE", lambda: self.service.validate(self.config))

    def test_import_cannot_raise_capabilities(self):
        self.config["devices"][0]["electrical_capabilities"]["maximum_rate_hz"] = 2000000
        self.assert_error("CAPABILITY_MISMATCH", lambda: self.service.validate(self.config))

    def test_physical_identity_and_firmware_mismatch_rejected(self):
        self.config["board_identity"]["simulation_only"] = False
        self.assert_error("SCHEMA_CONST", lambda: self.service.validate(self.config))
        self.config = self.service.select_profile("sim-mill-3axis")
        self.config["devices"][0]["identity"]["firmware_revision"] = "physical-2.0"
        self.assert_error("SCHEMA_CONST", lambda: self.service.validate(self.config))

    def test_profile_device_consistency(self):
        self.config["machine"]["profile_id"] = "sim-lathe-2axis"
        self.assert_error("PROFILE_TOPOLOGY", lambda: self.service.validate(self.config))
        self.assertEqual(4, self.service.validate(self.service.select_profile("sim-lathe-2axis"))["assigned_resources"])

    def test_commands_and_commissioning_cannot_be_imported(self):
        self.config["devices"][0]["permitted_commands"].append("run")
        self.assert_error("SCHEMA_LENGTH", lambda: self.service.validate(self.config))
        self.config = self.service.select_profile("sim-mill-3axis")
        self.config["devices"][0]["commissioning_checks"][0]["status"] = "passed"
        self.assert_error("SCHEMA_CONST", lambda: self.service.validate(self.config))

    def test_stale_apply_and_replay_refused(self):
        plan = self.service.preview(self.config)
        self.service.apply(plan)
        self.assert_error("STALE_PLAN", lambda: self.service.apply(plan))
        self.assertEqual(1, self.service.show()["revision"])

    def test_changed_candidate_or_diff_refused(self):
        plan = self.service.preview(self.config)
        plan["configuration"]["machine"]["name"] = "Modified after preview"
        self.assert_error("PLAN_CHANGED", lambda: self.service.apply(plan))
        plan = self.service.preview(self.config)
        plan["changes"] = []
        self.assert_error("PLAN_CHANGED", lambda: self.service.apply(plan))

    def test_state_epoch_invalidates_plan(self):
        plan = self.service.preview(self.config)
        self.runtime = RuntimeState(epoch="restarted")
        self.assert_error("STALE_PLAN", lambda: self.service.apply(plan))

    def test_armed_running_connected_and_physical_mutation_refused(self):
        plan = self.service.preview(self.config)
        for state in (RuntimeState(armed=True), RuntimeState(running=True), RuntimeState(connected=True), RuntimeState(simulation_only=False)):
            with self.subTest(state=state):
                self.runtime = state
                self.assert_error("UNSAFE_SIMULATION_STATE", lambda: self.service.apply(plan))
                self.assertEqual(0, self.service.show()["revision"])

    def test_malformed_runtime_boolean_refused(self):
        self.runtime = RuntimeState(armed=0)
        self.assert_error("RUNTIME_STATE", lambda: self.service.preview(self.config))

    def test_state_rechecked_immediately_before_persist(self):
        plan = self.service.preview(self.config)
        states = iter((RuntimeState(), RuntimeState(running=True)))
        self.service.state_provider = lambda: next(states)
        self.assert_error("UNSAFE_SIMULATION_STATE", lambda: self.service.apply(plan))
        self.assertEqual(0, self.service.show()["revision"])

    def test_backups_restore_as_new_revision_and_keep_audit(self):
        self.applied()
        backup = self.service.backup()
        self.config["devices"][0]["calibration"][0]["steps_per_unit"] = 250
        self.applied()
        plan = self.service.restore_preview(backup)
        self.assertTrue(plan["changes"])
        self.assertEqual(3, self.service.apply(plan, "restore-test")["revision"])
        self.assertEqual(200, self.service.show()["configuration"]["devices"][0]["calibration"][0]["steps_per_unit"])
        audit = self.service.audit()
        self.assertEqual("restore", audit["entries"][-1]["action"])
        self.assertEqual(3, audit["retained_prior_configurations"])
        self.assertFalse(self.service.show()["physical_commissioning_complete"])

    def test_corrupt_backup_and_foreign_backup_rejected(self):
        self.applied()
        backup = self.service.backup()
        backup["configuration"]["machine"]["name"] = "Corrupt"
        self.assert_error("BACKUP_CORRUPT", lambda: self.service.restore_preview(backup))
        other = ConfigurationService(Path(self.temporary.name) / "other.json")
        other.initialize()
        other.apply(other.preview(self.config))
        self.assert_error("BACKUP_IDENTITY", lambda: self.service.restore_preview(other.backup()))

    def test_rechecks_schema_even_with_recomputed_backup_hash(self):
        self.applied()
        backup = self.service.backup()
        backup["configuration"]["devices"][0]["readiness"]["observed"] = "ready"
        backup["integrity_sha256"] = digest({k: v for k, v in backup.items() if k != "integrity_sha256"})
        self.assert_error("SCHEMA_CONST", lambda: self.service.restore_preview(backup))

    def test_restore_while_armed_and_stale_restore_refused(self):
        self.applied()
        backup = self.service.backup()
        self.config["machine"]["name"] = "Edited"
        self.applied()
        plan = self.service.restore_preview(backup)
        self.runtime = RuntimeState(armed=True)
        self.assert_error("UNSAFE_SIMULATION_STATE", lambda: self.service.apply(plan))
        self.runtime = RuntimeState()
        self.config["machine"]["name"] = "Newer"
        self.applied()
        self.assert_error("STALE_PLAN", lambda: self.service.apply(plan))

    def test_failed_atomic_replace_leaves_old_state_and_no_temp(self):
        before = self.path.read_bytes()
        with patch("controller_config.service.os.replace", side_effect=OSError("injected failure")):
            with self.assertRaises(OSError):
                self.applied()
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual([], list(self.path.parent.glob("*.tmp")))
        self.assertFalse(Path(str(self.path) + ".lock").exists())

    def test_store_corruption_and_busy_fail_closed(self):
        lock = Path(str(self.path) + ".lock")
        lock.write_text("another writer")
        self.assert_error("STORE_BUSY", self.applied)
        lock.unlink()
        state = json.loads(self.path.read_text())
        state["revision"] = 55
        self.path.write_text(json.dumps(state))
        self.assert_error("STORE_CORRUPT", self.service.show)

    def test_init_and_export_preserve_existing_files(self):
        before = self.path.read_bytes()
        self.assert_error("STORE_EXISTS", self.service.initialize)
        self.assert_error("FILE_EXISTS", lambda: export_json(self.path, self.config))
        self.assertEqual(before, self.path.read_bytes())

    def test_duplicate_json_keys_and_nonfinite_json_rejected(self):
        bad = self.path.parent / "bad.json"
        bad.write_text('{"schema_version": 1, "schema_version": 1}')
        self.assert_error("DUPLICATE_KEY", lambda: read_json(bad))
        bad.write_text('{"value": NaN}')
        self.assert_error("NONFINITE", lambda: read_json(bad))

    def test_noop_preview_does_not_create_revision(self):
        changed = self.applied()
        audit_before = self.service.audit()
        result = self.applied()
        self.assertFalse(result["changed"])
        self.assertEqual(1, result["revision"])
        # A no-op apply has the same result keys as a changing apply.
        self.assertEqual(set(changed), set(result))
        self.assertIs(True, result["simulation_only"])
        self.assertEqual("unchanged; no revision created", result["commissioning"])
        self.assertEqual(audit_before, self.service.audit())

    def test_numeric_representation_change_is_reported_and_consistent_with_digest(self):
        self.config["devices"][0]["required_connections"][0]["voltage_v"] = 5
        self.applied()
        edited = copy.deepcopy(self.config)
        edited["devices"][0]["required_connections"][0]["voltage_v"] = 5.0
        plan = self.service.preview(edited)
        self.assertNotEqual(plan["base_sha256"], plan["candidate_sha256"])
        self.assertEqual([{"path": "/devices/0/required_connections/0/voltage_v", "before": 5, "after": 5.0}],
                         plan["changes"])
        result = self.service.apply(plan, "test")
        self.assertTrue(result["changed"])
        self.assertEqual(plan["candidate_sha256"], self.service.show()["configuration_sha256"])
        # An identical document still previews as empty with equal digests.
        same = self.service.preview(edited)
        self.assertEqual([], same["changes"])
        self.assertEqual(same["base_sha256"], same["candidate_sha256"])

    def record_event(self, *args):
        # The event writer is internal: recovery calls it while holding the
        # store lock after its own binding/inventory checks. Tests mirror that.
        with _exclusive_lock(self.service.path):
            return self.service._record_event_locked(*args)

    def test_audit_event_writer_is_not_public_service_contract(self):
        # Review of R1-014: a public free-text event method would let any
        # service caller forge module-swap records no recovery performed.
        public = {name for name in dir(ConfigurationService) if not name.startswith("_")}
        self.assertFalse({name for name in public if "event" in name}, public)
        self.assertNotIn("record_event", public)
        help_text = subprocess.run([sys.executable, "-m", "controller_config", "--help"], cwd=Path(__file__).resolve().parents[1],
                                   text=True, capture_output=True, timeout=30).stdout
        self.assertNotIn("event", help_text.lower())

    def test_record_event_appends_same_revision_audit_without_changing_configuration(self):
        self.applied()
        before = self.service.show()
        raw_configuration = before["configuration"]
        entry = self.record_event("replace_module", "recovery-test", before["revision"], before["configuration_sha256"])
        self.assertEqual(before, self.service.show())
        self.assertEqual(raw_configuration, ConfigurationService(self.path).show()["configuration"])
        audit = self.service.audit()
        self.assertEqual(entry, audit["entries"][-1])
        self.assertEqual({"revision": 1, "action": "replace_module", "actor": "recovery-test",
                          "before_sha256": before["configuration_sha256"], "after_sha256": before["configuration_sha256"]},
                         {key: value for key, value in entry.items() if key != "timestamp"})
        self.assertEqual(1, audit["retained_prior_configurations"])
        # Ordinary apply continues after an event entry.
        self.config["machine"]["name"] = "After event"
        self.assertEqual(2, self.applied()["revision"])
        self.assertEqual("apply", self.service.audit()["entries"][-1]["action"])

    def test_record_event_refuses_unknown_action_stale_store_and_unsafe_runtime(self):
        self.applied()
        state = self.service.show()
        before = self.path.read_bytes()
        for action in ("apply", "restore", "initialize", "run", None):
            with self.subTest(action=action):
                self.assert_error("AUDIT_ACTION", lambda: self.record_event(action, "t", state["revision"], state["configuration_sha256"]))
        self.assert_error("STALE_PLAN", lambda: self.record_event("replace_module", "t", 0, state["configuration_sha256"]))
        self.assert_error("STALE_PLAN", lambda: self.record_event("replace_module", "t", state["revision"], digest(None)))
        self.assert_error("ACTOR", lambda: self.record_event("replace_module", "x" * 121, state["revision"], state["configuration_sha256"]))
        self.runtime = RuntimeState(armed=True)
        self.assert_error("UNSAFE_SIMULATION_STATE", lambda: self.record_event("replace_module", "t", state["revision"], state["configuration_sha256"]))
        self.assertEqual(before, self.path.read_bytes())

    def test_forged_audit_actions_are_store_corruption(self):
        self.applied()
        state = self.service.show()
        self.record_event("replace_module", "t", state["revision"], state["configuration_sha256"])
        original = read_json(self.path)
        # An unknown action, or an event entry that claims a configuration change.
        for action, before_sha256 in (("unknown", None), ("replace_module", digest(None))):
            with self.subTest(action=action):
                data = copy.deepcopy(original)
                del data["integrity_sha256"]
                data["audit"][-1]["action"] = action
                if before_sha256:
                    data["audit"][-1]["before_sha256"] = before_sha256
                atomic_write(self.path, {**data, "integrity_sha256": digest(data)})
                self.assert_error("STORE_CORRUPT", self.service.show)

    def test_atomic_replace_retries_transient_windows_sharing_refusal(self):
        attempts = []
        real_replace = os.replace
        def busy_twice(source, destination):
            attempts.append(destination)
            if len(attempts) <= 2:
                raise PermissionError(13, "Access is denied (reader holds the store open)")
            return real_replace(source, destination)
        with patch("controller_config.service.os.replace", side_effect=busy_twice), \
                patch("controller_config.service.time.sleep") as sleep:
            self.assertEqual(1, self.applied()["revision"])
        self.assertEqual(3, len(attempts))
        self.assertEqual(2, sleep.call_count)
        self.assertEqual(1, self.service.show()["revision"])
        self.assertEqual([], list(self.path.parent.glob("*.tmp")))

    def test_persistent_sharing_refusal_fails_closed_with_old_state(self):
        before = self.path.read_bytes()
        with patch("controller_config.service.os.replace", side_effect=PermissionError(13, "Access is denied")) as replace, \
                patch("controller_config.service.time.sleep"):
            with self.assertRaises(PermissionError):
                self.applied()
        self.assertEqual(6, replace.call_count)
        self.assertEqual(before, self.path.read_bytes())
        self.assertEqual([], list(self.path.parent.glob("*.tmp")))
        self.assertFalse(Path(str(self.path) + ".lock").exists())

    def test_windows_reader_holding_store_open_does_not_fail_apply(self):
        # A concurrent `config show` reader opens the store without FILE_SHARE_DELETE.
        # Release it during the bounded retry window; on POSIX the rename succeeds at once.
        import threading
        stream = self.path.open("rb")
        releaser = threading.Timer(0.03, stream.close)
        releaser.start()
        try:
            self.assertEqual(1, self.applied()["revision"])
        finally:
            releaser.cancel()
            stream.close()
        self.assertEqual(1, self.service.show()["revision"])

    def test_catalog_copies_do_not_change_authority(self):
        catalog = self.service.capabilities()
        catalog["resources"][0]["maximum_rate_hz"] = 2000000
        self.assertEqual(195312.5, self.service.capabilities()["resources"][0]["maximum_rate_hz"])

    def test_cli_full_flow_and_structured_error(self):
        root = Path(__file__).resolve().parents[1]
        def cli(*args, expected=0):
            result = subprocess.run([sys.executable, "-m", "controller_config", "--store", str(self.path), *args], cwd=root, capture_output=True, text=True, timeout=10)
            self.assertEqual(expected, result.returncode, result.stderr + result.stdout)
            return json.loads(result.stdout)
        config = self.path.parent / "profile.json"
        plan = self.path.parent / "plan.json"
        backup = self.path.parent / "backup.json"
        cli("profile", "select", "sim-lathe-2axis", "--output", str(config))
        self.assertTrue(cli("config", "validate", str(config))["result"]["valid"])
        cli("config", "diff", str(config), "--output", str(plan))
        self.assertEqual(1, cli("config", "apply", str(plan))["result"]["revision"])
        cli("backup", "create", str(backup))
        self.assertEqual("STALE_PLAN", cli("config", "apply", str(plan), expected=2)["error"]["code"])
        unchanged = self.path.parent / "unchanged-plan.json"
        cli("config", "diff", str(config), "--output", str(unchanged))
        noop = cli("config", "apply", str(unchanged))["result"]
        self.assertEqual({"changed": False, "revision": 1, "simulation_only": True,
                          "commissioning": "unchanged; no revision created"},
                         {key: value for key, value in noop.items() if key != "configuration_sha256"})
        self.assertTrue(cli("wiring", "plan", str(config))["result"]["simulation_only"])
        self.assertEqual("disconnected_configuration_plan", cli("backup", "restore-plan", str(backup))["result"]["kind"])


if __name__ == "__main__":
    unittest.main()
