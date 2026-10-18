import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import uuid

from controller_config import ConfigurationError, ConfigurationService, RuntimeState
from controller_config.recovery import (CARTRIDGE_BYTES, MAX_GENERATION, RECORD_BYTES,
                                        SLOT, Cartridge, RecoveryService, module_fixture)
from controller_config.service import canonical, digest, read_json


def seal(data):
    return {**data, "integrity_sha256": digest(data)}


class ConfigurationRecoveryTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.machine_id = str(uuid.uuid4())
        self.runtime = RuntimeState()
        self.service = ConfigurationService(self.root / "compute.json", lambda: self.runtime)
        self.service.initialize("test")
        self.configuration = self.service.select_profile("sim-mill-3axis")
        self.configuration["devices"][0]["calibration"][0]["steps_per_unit"] = 321
        self.cartridge = Cartridge(self.root / "cartridge")
        self.cartridge.save(self.machine_id, self.configuration, 0)
        self.cartridge.save(self.machine_id, self.configuration, 1)
        self.inventory = {SLOT: "input-original"}
        self.recovery = RecoveryService(self.service, self.cartridge, self.machine_id, lambda: self.inventory)

    def assert_error(self, code, call):
        with self.assertRaises(ConfigurationError) as caught:
            call()
        self.assertEqual(code, caught.exception.code)

    def bootstrap(self):
        return self.recovery.apply(self.recovery.preview("bootstrap"))

    def mutate_record(self, index, mutation):
        data = read_json(self.cartridge.slot_path(index))
        del data["integrity_sha256"]
        mutation(data)
        self.cartridge.slot_path(index).write_bytes(canonical(seal(data)) + b"\n")

    def test_two_records_are_self_contained_bounded_and_have_no_module_calibration(self):
        selected = self.cartridge.load(self.machine_id)
        self.assertEqual(2, selected["record"]["generation"])
        self.assertEqual(self.configuration, selected["record"]["configuration"])
        self.assertLessEqual(sum(self.cartridge.slot_path(i).stat().st_size for i in (0, 1)), CARTRIDGE_BYTES)
        raw = self.cartridge.slot_path(1).read_text()
        for excluded in ("factory_calibration", "SIM-IN-001", "store_id", "run_permission", "homed"):
            self.assertNotIn(excluded, raw)

    def test_interrupted_newest_save_keeps_previous_valid_configuration(self):
        previous = self.cartridge.slot_path(1).read_bytes()
        changed = copy.deepcopy(self.configuration)
        changed["machine"]["name"] = "Changed"
        result = self.cartridge.save(self.machine_id, changed, 2, interrupt_after_bytes=100)
        self.assertFalse(result["committed"])
        self.assertEqual(previous, self.cartridge.slot_path(1).read_bytes())
        self.assertEqual(self.configuration, self.cartridge.load(self.machine_id)["record"]["configuration"])
        self.assertEqual(3, self.cartridge.save(self.machine_id, changed, 2)["generation"])

    def test_corrupt_newest_falls_back(self):
        data = read_json(self.cartridge.slot_path(1))
        data["configuration"]["machine"]["name"] = "corrupt"
        self.cartridge.slot_path(1).write_text(json.dumps(data))
        selected = self.cartridge.load(self.machine_id)
        self.assertEqual(1, selected["record"]["generation"])
        self.assertEqual("CARTRIDGE_DIGEST", selected["invalid_slots"][0]["code"])

    def test_two_equal_generation_different_valid_records_refused(self):
        self.mutate_record(0, lambda data: data.update(generation=2))
        self.mutate_record(0, lambda data: data["configuration"]["machine"].update(name="Other valid settings"))
        self.assert_error("CARTRIDGE_AMBIGUOUS", lambda: self.cartridge.load(self.machine_id))

    def test_mixed_machine_records_and_wrong_expected_identity_refused(self):
        self.assert_error("CARTRIDGE_MACHINE", lambda: self.cartridge.load(str(uuid.uuid4())))
        self.mutate_record(0, lambda data: data.update(machine_id=str(uuid.uuid4())))
        self.assert_error("CARTRIDGE_MACHINE", lambda: self.cartridge.load(self.machine_id))

    def test_valid_future_schema_is_not_treated_as_torn_record(self):
        self.mutate_record(1, lambda data: data.update(schema_version=2, future_field="new"))
        self.assert_error("CARTRIDGE_VERSION", lambda: self.cartridge.load(self.machine_id))

    def test_future_embedded_schema_is_not_downgraded(self):
        self.mutate_record(1, lambda data: data["configuration"].update(schema_version=2, future_field="new"))
        self.assert_error("CARTRIDGE_VERSION", lambda: self.cartridge.load(self.machine_id))

    def test_final_newline_is_required_so_final_byte_interruption_is_incomplete(self):
        length = len(self.cartridge.slot_path(1).read_bytes())
        result = self.cartridge.save(self.machine_id, self.configuration, 2, interrupt_after_bytes=length - 1)
        self.assertFalse(result["committed"])
        selected = self.cartridge.load(self.machine_id)
        self.assertEqual(2, selected["record"]["generation"])
        self.assertEqual("CARTRIDGE_FRAMING", selected["invalid_slots"][0]["code"])

    def test_bool_generation_and_overflow_refused(self):
        for value in (True, 0, -1, MAX_GENERATION + 1):
            with self.subTest(value=value):
                self.mutate_record(1, lambda data: data.update(generation=value))
                self.assertEqual(1, self.cartridge.load(self.machine_id)["record"]["generation"])
        self.assert_error("CARTRIDGE_GENERATION", lambda: self.cartridge.save(self.machine_id, self.configuration, True))
        self.mutate_record(0, lambda data: data.update(generation=MAX_GENERATION))
        self.assert_error("CARTRIDGE_GENERATION", lambda: self.cartridge.save(self.machine_id, self.configuration, MAX_GENERATION))

    def test_duplicate_keys_and_oversize_records_are_not_accepted(self):
        self.cartridge.slot_path(1).write_text('{"schema_version":1,"schema_version":1}')
        self.assertEqual("DUPLICATE_KEY", self.cartridge.load(self.machine_id)["invalid_slots"][0]["code"])
        self.cartridge.slot_path(1).write_bytes(b" " * (RECORD_BYTES + 1))
        self.assertEqual("CARTRIDGE_SIZE", self.cartridge.load(self.machine_id)["invalid_slots"][0]["code"])

    def test_all_corrupt_records_are_never_overwritten(self):
        for index in (0, 1):
            self.cartridge.slot_path(index).write_text("broken")
        self.assert_error("CARTRIDGE_NO_VALID_RECORD", lambda: self.cartridge.load(self.machine_id))
        self.assert_error("CARTRIDGE_NO_VALID_RECORD", lambda: self.cartridge.save(self.machine_id, self.configuration, 0))
        self.assertEqual("broken", self.cartridge.slot_path(0).read_text())

    def test_size_cap_checked_before_write_and_stale_save_refused(self):
        before = self.cartridge.slot_path(0).read_bytes()
        with patch("controller_config.recovery.RECORD_BYTES", 128):
            empty = Cartridge(self.root / "small")
            self.assert_error("CARTRIDGE_SIZE", lambda: empty.save(self.machine_id, self.configuration, 0))
            self.assertFalse(empty.slot_path(0).exists())
        self.assert_error("CARTRIDGE_STALE", lambda: self.cartridge.save(self.machine_id, self.configuration, 1))
        self.assertEqual(before, self.cartridge.slot_path(0).read_bytes())

    def test_imported_capabilities_and_permission_claims_rejected_even_when_sealed(self):
        for index in (0, 1):
            self.mutate_record(index, lambda data: data["configuration"]["devices"][0]["readiness"].update(observed="ready"))
        self.assert_error("CARTRIDGE_NO_VALID_RECORD", lambda: self.cartridge.load(self.machine_id))
        invalid = copy.deepcopy(self.configuration)
        invalid["devices"][0]["electrical_capabilities"]["maximum_rate_hz"] = 10000000
        self.assert_error("CAPABILITY_MISMATCH", lambda: self.cartridge.save(self.machine_id, invalid, 2))

    def test_outside_fixture_topology_refused(self):
        self.configuration["devices"][1]["required_connections"][0]["resource"] = "SIM.DI9"
        self.assert_error("RECOVERY_TOPOLOGY", lambda: self.cartridge.save(self.machine_id, self.configuration, 2))

    def test_preview_does_not_bind_or_write_store(self):
        before = self.service.path.read_bytes()
        plan = self.recovery.preview("bootstrap")
        self.assertEqual(before, self.service.path.read_bytes())
        self.assertFalse(self.recovery.binding_path.exists())
        self.assertTrue(plan["outputs_inhibited"])
        self.assertFalse(plan["homed"])
        self.assertFalse(plan["run_permission"])

    def test_bootstrap_uses_shared_apply_binds_machine_and_keeps_checks_pending(self):
        result = self.bootstrap()
        self.assertEqual(self.configuration, self.service.show()["configuration"])
        binding = read_json(self.recovery.binding_path)
        self.assertEqual(self.machine_id, binding["machine_id"])
        self.assertEqual(self.service.show()["store_id"], binding["store_id"])
        self.assertEqual("applied", binding["stage"])
        self.assertEqual(0, result["physical_commands"])
        self.assertEqual("apply", self.service.audit()["entries"][-1]["action"])
        self.assertIn("cartridge-recovery:", self.service.audit()["entries"][-1]["actor"])
        self.assertTrue(all(item["status"] == "pending" for item in result["verification_required"]))

    def test_replacement_preserves_assignments_and_machine_scale_uses_new_module_calibration(self):
        self.bootstrap()
        before = self.service.show()
        self.inventory[SLOT] = "input-replacement"
        result = self.recovery.apply(self.recovery.preview("replace_input_bank"))
        self.assertEqual(before, self.service.show())
        self.assertEqual(-22, result["replacement_module"]["factory_calibration"]["input_filter_clock_correction_ppm"])
        self.assertEqual(321, self.service.show()["configuration"]["devices"][0]["calibration"][0]["steps_per_unit"])
        self.assertEqual({"x-home", "y-home", "z-home"}, {item["device"] for item in result["verification_required"]})
        self.assertTrue(all(item["checks"] == ["wiring", "polarity"] for item in result["verification_required"]))
        self.assertTrue(result["outputs_inhibited"])
        self.assertFalse(result["homed"])
        self.assertFalse(result["run_permission"])

    def test_new_compute_has_new_store_identity_and_ordinary_foreign_backup_is_refused(self):
        self.bootstrap()
        replacement = ConfigurationService(self.root / "new-compute.json")
        replacement.initialize()
        self.assert_error("BACKUP_IDENTITY", lambda: replacement.restore_preview(self.service.backup()))
        recovery = RecoveryService(replacement, self.cartridge, self.machine_id, lambda: self.inventory)
        recovery.apply(recovery.preview("bootstrap"))
        self.assertNotEqual(self.service.show()["store_id"], replacement.show()["store_id"])
        self.assertEqual(self.service.show()["configuration"], replacement.show()["configuration"])

    def test_incompatible_voltage_abi_capacity_and_unknown_module_refused(self):
        for fixture in ("input-wrong-voltage", "input-wrong-abi", "input-short-bank"):
            self.inventory[SLOT] = fixture
            self.assert_error("MODULE_INCOMPATIBLE", lambda: self.recovery.preview("bootstrap"))
        self.inventory[SLOT] = {"fixture_id": "input-replacement", "voltage_v": 24}
        self.assert_error("MODULE_UNKNOWN", lambda: self.recovery.preview("bootstrap"))

    def test_fixture_metadata_cannot_mutate_authoritative_registry(self):
        module_fixture("input-replacement")["maximum_current_a"] = 999
        self.assertEqual(0.005, module_fixture("input-replacement")["maximum_current_a"])

    def test_cartridge_or_inventory_change_invalidates_preview(self):
        plan = self.recovery.preview("bootstrap")
        self.cartridge.save(self.machine_id, self.configuration, 2)
        self.assert_error("RECOVERY_STALE", lambda: self.recovery.apply(plan))
        plan = self.recovery.preview("bootstrap")
        self.inventory[SLOT] = "input-replacement"
        self.assert_error("RECOVERY_STALE", lambda: self.recovery.apply(plan))
        self.assertEqual(0, self.service.show()["revision"])

    def test_inventory_rechecked_immediately_before_apply(self):
        plan = self.recovery.preview("bootstrap")
        observations = iter(({SLOT: "input-original"}, {SLOT: "input-replacement"}))
        self.recovery.inventory_provider = lambda: next(observations)
        self.assert_error("RECOVERY_STALE", lambda: self.recovery.apply(plan))
        self.assertEqual(0, self.service.show()["revision"])

    def test_runtime_epoch_and_unsafe_state_refuse_recovery(self):
        plan = self.recovery.preview("bootstrap")
        self.runtime = RuntimeState(epoch="changed")
        self.assert_error("RECOVERY_STALE", lambda: self.recovery.apply(plan))
        for state in (RuntimeState(armed=True), RuntimeState(running=True), RuntimeState(connected=True), RuntimeState(simulation_only=False)):
            self.runtime = state
            self.assert_error("UNSAFE_SIMULATION_STATE", lambda: self.recovery.apply(plan))
        self.assertFalse(self.recovery.binding_path.exists())

    def test_plan_mutation_and_invalid_api_inputs_are_refused(self):
        plan = self.recovery.preview("bootstrap")
        plan["run_permission"] = True
        self.assert_error("RECOVERY_STALE", lambda: self.recovery.apply(plan))
        for value in (None, [], True, {"operation": None}):
            self.assert_error("RECOVERY_PLAN", lambda: self.recovery.apply(value))
        self.assert_error("MACHINE_ID", lambda: Cartridge(self.root).load("My machine"))

    def test_existing_config_without_reservation_is_never_overwritten(self):
        self.service.apply(self.service.preview(self.configuration))
        before = self.service.path.read_bytes()
        self.assert_error("RECOVERY_NOT_BLANK", lambda: self.recovery.preview("bootstrap"))
        self.assertEqual(before, self.service.path.read_bytes())

    def test_reservation_before_failed_config_write_can_retry(self):
        plan = self.recovery.preview("bootstrap")
        with patch.object(self.service, "apply", side_effect=OSError("injected config write failure")):
            with self.assertRaises(OSError):
                self.recovery.apply(plan)
        self.assertEqual("reserved", read_json(self.recovery.binding_path)["stage"])
        self.assertEqual(0, self.service.show()["revision"])
        self.bootstrap()
        self.assertEqual(1, self.service.show()["revision"])

    def test_failed_receipt_after_config_commit_can_finish_without_duplicate_revision(self):
        from controller_config.recovery import atomic_write as real_write
        def interrupted(path, value):
            if path == self.recovery.binding_path and value.get("stage") == "applied":
                raise OSError("injected final binding failure")
            return real_write(path, value)
        with patch("controller_config.recovery.atomic_write", side_effect=interrupted):
            with self.assertRaises(OSError):
                self.bootstrap()
        self.assertEqual(1, self.service.show()["revision"])
        self.assertEqual("reserved", read_json(self.recovery.binding_path)["stage"])
        self.bootstrap()
        self.assertEqual(1, self.service.show()["revision"])
        self.assertEqual("applied", read_json(self.recovery.binding_path)["stage"])

    def test_reserved_retry_refuses_different_record_inventory_or_later_store_revision(self):
        with patch.object(self.service, "apply", side_effect=OSError("failure")):
            with self.assertRaises(OSError):
                self.bootstrap()
        self.inventory[SLOT] = "input-replacement"
        self.assert_error("RECOVERY_RESERVATION", lambda: self.recovery.preview("bootstrap"))
        self.inventory[SLOT] = "input-original"
        changed = copy.deepcopy(self.configuration)
        changed["machine"]["name"] = "unrelated edit"
        self.service.apply(self.service.preview(changed))
        self.service.apply(self.service.preview(self.configuration))
        self.assert_error("RECOVERY_RESERVATION", lambda: self.recovery.preview("bootstrap"))

    def test_corrupt_or_foreign_binding_refused(self):
        self.bootstrap()
        data = read_json(self.recovery.binding_path)
        data["machine_id"] = str(uuid.uuid4())
        self.recovery.binding_path.write_text(json.dumps(data))
        self.assert_error("BINDING_CORRUPT", lambda: self.recovery.preview("replace_input_bank"))
        del data["integrity_sha256"]
        self.recovery.binding_path.write_bytes(canonical(seal(data)))
        self.assert_error("BINDING_IDENTITY", lambda: self.recovery.preview("replace_input_bank"))

    def test_module_replacement_cannot_silently_restore_older_machine_configuration(self):
        self.bootstrap()
        changed = copy.deepcopy(self.configuration)
        changed["devices"][0]["calibration"][0]["steps_per_unit"] = 999
        self.service.apply(self.service.preview(changed))
        self.inventory[SLOT] = "input-replacement"
        self.assert_error("RECOVERY_RECONCILE", lambda: self.recovery.preview("replace_input_bank"))
        self.assertEqual(changed, self.service.show()["configuration"])

    def test_replacement_refuses_older_newer_or_equal_generation_changed_cartridge(self):
        self.bootstrap()
        self.inventory[SLOT] = "input-replacement"
        old_slot = self.cartridge.slot_path(1).read_bytes()
        self.cartridge.slot_path(1).write_text("broken newest")
        self.assert_error("RECOVERY_RECONCILE", lambda: self.recovery.preview("replace_input_bank"))
        self.cartridge.slot_path(1).write_bytes(old_slot)
        self.cartridge.save(self.machine_id, self.configuration, 2)
        self.assert_error("RECOVERY_RECONCILE", lambda: self.recovery.preview("replace_input_bank"))
        self.cartridge.slot_path(0).write_text("broken alternate")
        self.mutate_record(1, lambda data: data["configuration"]["machine"].update(name="Changed at same generation"))
        self.assert_error("RECOVERY_RECONCILE", lambda: self.recovery.preview("replace_input_bank"))

    def test_intervening_shared_service_edit_prevents_binding_finalization(self):
        real_apply = self.service.apply
        def intervening(plan, actor):
            result = real_apply(plan, actor)
            changed = copy.deepcopy(self.configuration)
            changed["machine"]["name"] = "Concurrent ordinary edit"
            real_apply(self.service.preview(changed), "other-client")
            return result
        with patch.object(self.service, "apply", side_effect=intervening):
            self.assert_error("RECOVERY_STALE", self.bootstrap)
        self.assertEqual("reserved", read_json(self.recovery.binding_path)["stage"])
        self.assertEqual(2, self.service.show()["revision"])
        self.assert_error("RECOVERY_RESERVATION", lambda: self.recovery.preview("bootstrap"))


if __name__ == "__main__":
    unittest.main()
