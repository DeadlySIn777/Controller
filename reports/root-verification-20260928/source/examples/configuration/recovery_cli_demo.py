"""Run recovery end to end through public CLI subprocesses, with no devices."""

import json
from pathlib import Path
import subprocess
import sys
import tempfile
import uuid


def run():
    repository = Path(__file__).resolve().parents[2]
    with tempfile.TemporaryDirectory(prefix="controller-recovery-cli-") as directory:
        root = Path(directory)
        store = root / "compute.json"
        cartridge = root / "cartridge"
        configuration = root / "machine.json"
        inventory = root / "input-original.json"
        replacement = root / "input-replacement.json"
        bootstrap = root / "bootstrap-plan.json"
        replace = root / "replacement-plan.json"
        machine = str(uuid.uuid4())
        executed = []

        def cli(*arguments, expected_error=None):
            result = subprocess.run([sys.executable, "-m", "controller_config", "--store", str(store),
                                     *map(str, arguments)], cwd=repository, capture_output=True,
                                    text=True, encoding="utf-8", timeout=15)
            if result.stderr:
                raise RuntimeError(result.stderr)
            response = json.loads(result.stdout)
            if expected_error:
                if result.returncode != 2 or response.get("ok") is not False or response.get("error", {}).get("code") != expected_error:
                    raise RuntimeError(response)
                executed.append({"command": " ".join(map(str, arguments[:2])), "refused": expected_error})
                return response["error"]
            if result.returncode != 0 or response.get("ok") is not True:
                raise RuntimeError(response)
            executed.append({"command": " ".join(map(str, arguments[:2])), "ok": True})
            return response["result"]

        cartridge_arguments = ("--directory", cartridge, "--machine-id", machine)
        original_arguments = (*cartridge_arguments, "--fixture-inventory", inventory)
        replacement_arguments = (*cartridge_arguments, "--fixture-inventory", replacement)
        cli("profile", "select", "sim-mill-3axis", "--output", configuration)
        source = configuration.read_bytes()
        cli("cartridge", "save", *cartridge_arguments, "--configuration", configuration, "--expected-generation", 0)
        cli("cartridge", "save", *cartridge_arguments, "--configuration", configuration, "--expected-generation", 1)
        selected = cli("cartridge", "inspect", *cartridge_arguments)
        if store.exists():
            raise RuntimeError("Inspection created a compute store")
        cli("init")
        cli("recovery", "inventory", "--input-bank", "input-original", "--output", inventory)
        cli("recovery", "bootstrap-preview", *original_arguments, "--output", bootstrap)
        imported = cli("recovery", "apply", bootstrap, *original_arguments)
        before = cli("config", "show")
        cli("recovery", "inventory", "--input-bank", "input-replacement", "--output", replacement)
        cli("recovery", "replace-preview", *replacement_arguments, "--output", replace)
        cli("recovery", "apply", replace, *original_arguments, expected_error="RECOVERY_NO_REPLACEMENT")
        exchanged = cli("recovery", "apply", replace, *replacement_arguments)
        after = cli("config", "show")
        if before != after or source != configuration.read_bytes():
            raise RuntimeError("Configuration or source changed during replacement")
        if any(receipt["outputs_inhibited"] is not True or receipt["homed"] is not False or
               receipt["run_permission"] is not False or receipt["physical_commands"] != 0
               for receipt in (imported, exchanged)):
            raise RuntimeError("Recovery permission contract failed")
        return {"ok": True, "simulation_only": True, "scope": "public_CLI_subprocess_acceptance",
                "command_results": executed, "cartridge_generation": selected["record"]["generation"],
                "settings_unchanged": True, "source_file_unchanged": True,
                "old_module": imported["replacement_module"]["serial"],
                "new_module": exchanged["replacement_module"]["serial"],
                "new_module_factory_metadata": exchanged["replacement_module"]["factory_calibration"],
                "verification_required": exchanged["verification_required"],
                "outputs_inhibited": True, "homed": False, "run_permission": False, "physical_commands": 0,
                "temporary_files_removed": True}


if __name__ == "__main__":
    print(json.dumps(run(), indent=2))
