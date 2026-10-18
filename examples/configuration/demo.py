"""Run from the repository root: python -m examples.configuration.demo.

Uses the exact ConfigurationService API used by the CLI. All persisted files live
in a temporary directory; no physical device, LinuxCNC, network or GPIO is opened.
"""

from copy import deepcopy
import json
from pathlib import Path
from tempfile import TemporaryDirectory

from controller_config import ConfigurationError, ConfigurationService, RuntimeState
from controller_config.service import export_json, read_json


def run_demo():
    with TemporaryDirectory(prefix="controller-config-demo-") as directory:
        path = Path(directory) / "state.json"
        service = ConfigurationService(path)
        service.initialize("api-demo")
        selected = service.select_profile("sim-mill-3axis")
        validation = service.validate(selected)
        wiring = service.wiring(selected)
        first = service.apply(service.preview(selected), "api-demo")
        backup_path = Path(directory) / "backup.json"
        export_json(backup_path, service.backup())

        changed = deepcopy(selected)
        changed["devices"][0]["calibration"][0]["steps_per_unit"] = 250
        update_plan = service.preview(changed)
        second = service.apply(update_plan, "api-demo")

        failures = {}
        conflict = deepcopy(selected)
        conflict["devices"][2]["required_connections"][0]["resource"] = "SIM.M0"
        for name, action in (
            ("resource_conflict", lambda: service.validate(conflict)),
            ("stale_apply", lambda: service.apply(update_plan)),
            ("armed_apply", lambda: ConfigurationService(path, lambda: RuntimeState(armed=True)).apply(service.preview(selected))),
        ):
            try:
                action()
            except ConfigurationError as error:
                failures[name] = error.code
            else:
                raise AssertionError(f"Expected {name} refusal")

        restore_plan = service.restore_preview(read_json(backup_path))
        restored = service.apply(restore_plan, "api-demo-restore")
        assert service.show()["configuration"] == selected
        assert [first["revision"], second["revision"], restored["revision"]] == [1, 2, 3]
        return {"schema_version": 1, "simulation_only": True,
                "identity": service.capabilities()["identity"],
                "profile": selected["machine"]["profile_id"], "validation": validation,
                "illustrative_wiring_connections": len(wiring["connections"]),
                "change_preview": update_plan["changes"], "refusals": failures,
                "revision_sequence": [1, 2, 3], "restored_configuration_matches_original": True,
                "audit_actions": [item["action"] for item in service.audit()["entries"]],
                "physical_commands_sent": 0, "physical_commissioning_complete": False,
                "temporary_files_removed_after_demo": True}


if __name__ == "__main__":
    print(json.dumps(run_demo(), indent=2))
