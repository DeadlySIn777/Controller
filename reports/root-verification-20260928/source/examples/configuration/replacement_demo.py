"""Run: python -m examples.configuration.replacement_demo

Everything is in a fresh temporary directory; no physical transport is imported.
"""

import copy
import json
from pathlib import Path
import tempfile

from controller_config import ConfigurationError, ConfigurationService
from controller_config.recovery import Cartridge, RecoveryService, SLOT


def run():
    machine_id = "736751dc-1347-457f-ab4e-ef8973a359b9"
    with tempfile.TemporaryDirectory(prefix="controller-replacement-") as temporary:
        root = Path(temporary)
        original = ConfigurationService(root / "original-compute.json")
        original.initialize("replacement-demo")
        configuration = original.select_profile("sim-mill-3axis")
        cartridge = Cartridge(root / "machine-cartridge")
        first = cartridge.save(machine_id, configuration, 0)
        second = cartridge.save(machine_id, configuration, 1)
        inventory = {SLOT: "input-original"}
        recovery = RecoveryService(original, cartridge, machine_id, lambda: inventory)
        commissioned_fixture = recovery.apply(recovery.preview("bootstrap"))
        before = original.show()["configuration"]
        inventory[SLOT] = "input-replacement"
        replaced = recovery.apply(recovery.preview("replace_input_bank"))
        assert original.show()["configuration"] == before
        refusals = []
        inventory[SLOT] = "input-wrong-voltage"
        try:
            recovery.preview("replace_input_bank")
            raise AssertionError("Incompatible module was accepted")
        except ConfigurationError as error:
            refusals.append(error.code)
        inventory[SLOT] = "input-replacement"

        changed = copy.deepcopy(configuration)
        changed["machine"]["name"] = "Interrupted new configuration"
        cartridge.save(machine_id, changed, 2, interrupt_after_bytes=100)
        after_interruption = cartridge.load(machine_id)
        assert after_interruption["record"]["generation"] == 2
        cartridge.save(machine_id, changed, 2)
        corrupt = json.loads(cartridge.slot_path(0).read_text())
        corrupt["configuration"]["machine"]["name"] = "Corrupted after save"
        cartridge.slot_path(0).write_text(json.dumps(corrupt))
        after_corruption = cartridge.load(machine_id)
        assert after_corruption["record"]["generation"] == 2

        replacement_compute = ConfigurationService(root / "replacement-compute.json")
        replacement_compute.initialize("replacement-demo")
        try:
            replacement_compute.restore_preview(original.backup())
            raise AssertionError("Foreign store backup was accepted")
        except ConfigurationError as error:
            refusals.append(error.code)
        bootstrap = RecoveryService(replacement_compute, cartridge, machine_id, lambda: inventory)
        imported = bootstrap.apply(bootstrap.preview("bootstrap"))
        assert replacement_compute.show()["configuration"] == configuration
        assert replacement_compute.show()["store_id"] != original.show()["store_id"]
        return {"simulation_only": True, "physical_commands": 0,
                "cartridge": {"record_bytes": [first["encoded_bytes"], second["encoded_bytes"]],
                              "two_record_bytes": first["encoded_bytes"] + second["encoded_bytes"],
                              "modeled_capacity_bytes": 32768,
                              "fallback_generation_after_torn_write": after_interruption["record"]["generation"],
                              "fallback_generation_after_corruption": after_corruption["record"]["generation"]},
                "input_bank_replacement": {"assignments_unchanged": original.show()["configuration"] == before,
                    "old_factory_metadata": commissioned_fixture["replacement_module"]["factory_calibration"],
                    "new_factory_metadata": replaced["replacement_module"]["factory_calibration"],
                    "verification_required": replaced["verification_required"],
                    "outputs_inhibited": replaced["outputs_inhibited"], "homed": replaced["homed"],
                    "run_permission": replaced["run_permission"]},
                "new_compute": {"different_store_identity": True, "same_machine_identity": imported["machine_id"] == machine_id,
                                "configuration_retained": replacement_compute.show()["configuration"] == before,
                                "store_revision": replacement_compute.show()["revision"],
                                "verification_required_count": len(imported["verification_required"]),
                                "outputs_inhibited": imported["outputs_inhibited"], "homed": imported["homed"],
                                "run_permission": imported["run_permission"]},
                "refused": refusals, "temporary_files_removed_on_return": True}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
