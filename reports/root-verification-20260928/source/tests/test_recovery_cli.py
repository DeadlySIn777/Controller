"""Subprocess acceptance checks of the public, disconnected recovery CLI."""

import copy
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
import uuid


ROOT = Path(__file__).resolve().parents[1]
SLOT = "SIM.INPUT_BANK0"


class RecoveryCliTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.directory = Path(self.temporary.name)
        self.store = self.directory / "compute.json"
        self.cartridge = self.directory / "cartridge"
        self.configuration = self.directory / "machine.json"
        self.inventory = self.directory / "inventory.json"
        self.machine = str(uuid.uuid4())
        self.cli("profile", "select", "sim-mill-3axis", "--output", self.configuration)
        # Persist a nondefault user value so replacement cannot silently reset it.
        value = self.read(self.configuration)
        value["devices"][0]["calibration"][0]["steps_per_unit"] = 321
        self.write(self.configuration, value)
        self.save(0)
        self.cli("recovery", "inventory", "--input-bank", "input-original", "--output", self.inventory)
        self.cli("init")

    def cli(self, *arguments, error=None, store=None):
        result = subprocess.run([sys.executable, "-m", "controller_config", "--store", str(store or self.store),
                                 *map(str, arguments)], cwd=ROOT, capture_output=True, text=True,
                                encoding="utf-8", timeout=15)
        self.assertEqual("", result.stderr, result.stderr)
        try:
            response = json.loads(result.stdout)
        except ValueError:
            self.fail(f"CLI did not return JSON: {result.stdout!r}")
        self.assertEqual(2 if error else 0, result.returncode, response)
        self.assertIs(response["ok"], error is None)
        self.assertIs(response["simulation_only"], True)
        if error:
            self.assertEqual(error, response["error"]["code"], response)
            return response["error"]
        return response["result"]

    @staticmethod
    def read(path):
        return json.loads(path.read_text(encoding="utf-8"))

    @staticmethod
    def write(path, value):
        path.write_text(json.dumps(value), encoding="utf-8")

    def cartridge_args(self, machine=None):
        return ("--directory", self.cartridge, "--machine-id", machine or self.machine)

    def recovery_args(self, inventory=None, machine=None):
        return (*self.cartridge_args(machine), "--fixture-inventory", inventory or self.inventory)

    def save(self, generation, error=None, machine=None):
        return self.cli("cartridge", "save", *self.cartridge_args(machine), "--configuration", self.configuration,
                        "--expected-generation", generation, error=error)

    def preview(self, filename="bootstrap.json", operation="bootstrap-preview", inventory=None, error=None):
        plan = self.directory / filename
        self.cli("recovery", operation, *self.recovery_args(inventory), "--output", plan, error=error)
        return plan

    def apply(self, plan, inventory=None, error=None, machine=None):
        return self.cli("recovery", "apply", plan, *self.recovery_args(inventory, machine), error=error)

    def bootstrap(self):
        return self.apply(self.preview())

    def snapshot(self):
        return {str(path.relative_to(self.directory)): path.read_bytes()
                for path in self.directory.rglob("*") if path.is_file()}

    def assert_inhibited(self, receipt):
        self.assertIs(receipt["outputs_inhibited"], True)
        self.assertIs(receipt["homed"], False)
        self.assertIs(receipt["run_permission"], False)
        self.assertEqual(0, receipt["physical_commands"])

    def test_bootstrap_and_replace_preserve_assignments_and_own_module_metadata(self):
        source = self.configuration.read_bytes()
        cartridge_before = {path.name: path.read_bytes() for path in self.cartridge.iterdir()}
        original = self.bootstrap()
        self.assert_inhibited(original)
        self.assertEqual(15, original["replacement_module"]["factory_calibration"]["input_filter_clock_correction_ppm"])
        before = self.cli("config", "show")
        replacement = self.directory / "replacement-inventory.json"
        self.cli("recovery", "inventory", "--input-bank", "input-replacement", "--output", replacement)
        plan = self.preview("replacement-plan.json", "replace-preview", replacement)
        plan_before = plan.read_bytes()
        result = self.apply(plan, replacement)
        self.assert_inhibited(result)
        self.assertIs(result["assignments_retained"], True)
        self.assertEqual(-22, result["replacement_module"]["factory_calibration"]["input_filter_clock_correction_ppm"])
        self.assertEqual("SIM-IN-002", result["replacement_module"]["serial"])
        self.assertEqual(["x-home", "y-home", "z-home"], [row["device"] for row in result["verification_required"]])
        self.assertTrue(all(row["checks"] == ["wiring", "polarity"] and row["status"] == "pending"
                            for row in result["verification_required"]))
        after = self.cli("config", "show")
        self.assertEqual(before, after)
        self.assertEqual(self.read(self.configuration), after["configuration"])
        self.assertEqual(source, self.configuration.read_bytes())
        self.assertEqual(plan_before, plan.read_bytes())
        self.assertEqual(cartridge_before, {path.name: path.read_bytes() for path in self.cartridge.iterdir()})
        binding = self.read(Path(str(self.store) + ".machine-binding.json"))
        self.assertEqual("SIM-IN-002", binding["inventory"][SLOT]["serial"])
        self.assertEqual("applied", binding["stage"])
        self.assertIn("cartridge-recovery:" + self.machine, self.cli("audit")["entries"][-1]["actor"])

    def test_inspect_has_no_import_or_creation_side_effects(self):
        before = self.snapshot()
        missing_store = self.directory / "uninitialized.json"
        result = self.cli("cartridge", "inspect", *self.cartridge_args(), store=missing_store)
        self.assertEqual(1, result["record"]["generation"])
        self.assertEqual(before, self.snapshot())
        absent = self.directory / "absent-cartridge"
        self.cli("cartridge", "inspect", "--directory", absent, "--machine-id", self.machine,
                 error="CARTRIDGE_NO_VALID_RECORD")
        self.assertFalse(absent.exists())
        self.assertFalse(missing_store.exists())

    def test_save_uses_generation_and_machine_identity_without_overwriting_sources(self):
        result = self.save(1)
        self.assertEqual(2, result["generation"])
        before = self.snapshot()
        self.save(1, error="CARTRIDGE_STALE")
        self.save(2, machine=str(uuid.uuid4()), error="CARTRIDGE_MACHINE")
        self.assertEqual(before, self.snapshot())
        inspect = self.cli("cartridge", "inspect", *self.cartridge_args())
        self.assertEqual([], inspect["invalid_slots"])
        self.assertEqual(2, inspect["record"]["generation"])

    def test_inventory_is_authored_not_imported_electrical_authority(self):
        for fixture in ("input-wrong-voltage", "input-wrong-abi", "input-short-bank"):
            with self.subTest(fixture=fixture):
                inventory = self.directory / (fixture + ".json")
                self.cli("recovery", "inventory", "--input-bank", fixture, "--output", inventory)
                self.preview(fixture + "-plan.json", inventory=inventory, error="MODULE_INCOMPATIBLE")
        invented = copy.deepcopy(self.read(self.inventory))
        invented["modules"][SLOT] = {"fixture_id": "input-original", "voltage_v": 1000}
        forged = self.directory / "forged.json"
        self.write(forged, invented)
        self.preview("forged-plan.json", inventory=forged, error="MODULE_UNKNOWN")
        invented["modules"][SLOT] = "input-original"
        invented["physical_discovery"] = True
        self.write(forged, invented)
        self.preview("physical-plan.json", inventory=forged, error="FIXTURE_INVENTORY")
        self.assertIsNone(self.cli("config", "show")["configuration"])
        self.assertFalse(Path(str(self.store) + ".machine-binding.json").exists())

    def test_changed_inventory_and_mutated_plan_are_rejected_at_apply(self):
        plan = self.preview()
        original_inventory = self.read(self.inventory)
        changed = copy.deepcopy(original_inventory)
        changed["modules"][SLOT] = "input-replacement"
        self.write(self.inventory, changed)
        before = self.snapshot()
        self.apply(plan, error="RECOVERY_STALE")
        self.assertEqual(before, self.snapshot())
        self.write(self.inventory, original_inventory)
        edited = self.read(plan)
        edited["outputs_inhibited"] = False
        edited["run_permission"] = True
        self.write(plan, edited)
        before = self.snapshot()
        self.apply(plan, error="RECOVERY_STALE")
        self.assertEqual(before, self.snapshot())

    def test_changed_cartridge_or_store_invalidates_preview(self):
        plan = self.preview()
        self.save(1)
        self.apply(plan, error="RECOVERY_STALE")
        fresh = self.preview("fresh.json")
        ordinary_plan = self.directory / "ordinary.json"
        self.cli("config", "diff", self.configuration, "--output", ordinary_plan)
        self.cli("config", "apply", ordinary_plan)
        before = self.snapshot()
        self.apply(fresh, error="RECOVERY_NOT_BLANK")
        self.assertEqual(before, self.snapshot())

    def test_wrong_machine_and_other_compute_store_cannot_apply_plan(self):
        plan = self.preview()
        self.apply(plan, machine=str(uuid.uuid4()), error="CARTRIDGE_MACHINE")
        other_store = self.directory / "other-compute.json"
        self.cli("init", store=other_store)
        before = self.snapshot()
        self.cli("recovery", "apply", plan, *self.recovery_args(), store=other_store, error="RECOVERY_STALE")
        self.assertEqual(before, self.snapshot())

    def test_ordinary_backups_remain_store_bound(self):
        self.bootstrap()
        backup = self.directory / "ordinary-backup.json"
        self.cli("backup", "create", backup)
        original = backup.read_bytes()
        other = self.directory / "fresh-compute.json"
        self.cli("init", store=other)
        self.cli("backup", "restore-plan", backup, store=other, error="BACKUP_IDENTITY")
        plan = self.directory / "fresh-bootstrap.json"
        self.cli("recovery", "bootstrap-preview", *self.recovery_args(), "--output", plan, store=other)
        result = self.cli("recovery", "apply", plan, *self.recovery_args(), store=other)
        self.assert_inhibited(result)
        self.assertEqual(self.read(self.configuration), self.cli("config", "show", store=other)["configuration"])
        self.assertEqual(original, backup.read_bytes())

    def test_existing_export_files_are_preserved(self):
        plan = self.preview()
        before = self.snapshot()
        self.preview(error="FILE_EXISTS")
        self.cli("recovery", "inventory", "--input-bank", "input-replacement", "--output", self.inventory,
                 error="FILE_EXISTS")
        self.assertEqual(before, self.snapshot())
        self.assertEqual("bootstrap", self.read(plan)["operation"])

    def test_invalid_arguments_and_documents_produce_structured_errors(self):
        self.cli("recovery", "bootstrap-preview", error="ARGUMENT_ERROR")
        self.cli("cartridge", "save", *self.cartridge_args(), "--configuration", self.configuration,
                 "--expected-generation", "nonsense", error="ARGUMENT_ERROR")
        self.cli("recovery", "inventory", "--input-bank", "unknown", "--output", self.directory / "unknown.json",
                 error="MODULE_UNKNOWN")
        bad = self.directory / "bad-plan.json"
        bad.write_text('{"operation":"bootstrap","operation":"bootstrap"}', encoding="utf-8")
        self.apply(bad, error="DUPLICATE_KEY")
        self.cli("cartridge", "save", *self.cartridge_args(), "--configuration", self.cartridge / "record-0.json",
                 "--expected-generation", 1, error="SOURCE_CONFLICT")


if __name__ == "__main__":
    unittest.main()
