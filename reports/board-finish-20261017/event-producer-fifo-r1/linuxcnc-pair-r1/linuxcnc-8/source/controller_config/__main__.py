"""Run as python -m controller_config; no installed global cncctl is claimed."""

import argparse
import json
from pathlib import Path
import sys

from .model import ConfigurationError
from .recovery import Cartridge, RecoveryService, SLOT, module_fixture
from .service import ConfigurationService, export_json, read_json


class JsonArgumentParser(argparse.ArgumentParser):
    """Operational errors remain machine-readable; --help retains normal usage."""
    def error(self, message):
        raise ConfigurationError("ARGUMENT_ERROR", message)


def _cartridge_arguments(sub):
    sub.add_argument("--directory", required=True, help="Explicit directory containing two virtual cartridge files")
    sub.add_argument("--machine-id", required=True, help="Canonical UUID for the machine, independent of compute store identity")


def parser():
    p = JsonArgumentParser(prog="python -m controller_config",
        description="Prototype cncctl: disconnected simulation configuration only; all output is JSON.")
    p.add_argument("--store", default=".controller-config-demo/state.json", help="Dedicated demo state path; created only by init")
    p.add_argument("--json", action="store_true", help="Explicit structured mode (already the default)")
    commands = p.add_subparsers(dest="command", required=True)
    from .setup_cli import add_commands
    add_commands(commands)
    for name in ("capabilities", "schema", "init", "audit"):
        sub = commands.add_parser(name)
        if name == "init":
            sub.add_argument("--actor", default="cli-demo")
    profile = commands.add_parser("profile").add_subparsers(dest="operation", required=True)
    profile.add_parser("list")
    select = profile.add_parser("select")
    select.add_argument("profile_id")
    select.add_argument("--output", help="Write raw configuration to a new file")
    config = commands.add_parser("config").add_subparsers(dest="operation", required=True)
    config.add_parser("show")
    for name in ("validate", "diff", "apply"):
        sub = config.add_parser(name)
        sub.add_argument("file", help="Configuration JSON, or preview plan JSON for apply")
        if name == "diff":
            sub.add_argument("--output", help="Write raw revision-bound plan to a new file")
        if name == "apply":
            sub.add_argument("--actor", default="cli-demo")
    wiring = commands.add_parser("wiring").add_subparsers(dest="operation", required=True)
    wiring.add_parser("plan").add_argument("file")
    backup = commands.add_parser("backup").add_subparsers(dest="operation", required=True)
    backup.add_parser("create").add_argument("output")
    restore = backup.add_parser("restore-plan")
    restore.add_argument("file")
    restore.add_argument("--output", help="Write restore preview; apply it with config apply")
    cartridge = commands.add_parser("cartridge", help="Bounded file-backed cartridge; no memory device is opened").add_subparsers(dest="operation", required=True)
    _cartridge_arguments(cartridge.add_parser("inspect", help="Read and validate records without creating or importing anything"))
    save = cartridge.add_parser("save", help="Save an explicit virtual configuration using compare-and-save")
    _cartridge_arguments(save)
    save.add_argument("--configuration", required=True, help="Raw virtual configuration JSON, not a CLI response or backup")
    save.add_argument("--expected-generation", required=True, type=int, help="Previously inspected generation, or zero for an empty cartridge")
    recovery = commands.add_parser("recovery", help="Disconnected machine recovery using the shared service").add_subparsers(dest="operation", required=True)
    inventory = recovery.add_parser("inventory", help="Author a named simulation observation; this does not discover equipment")
    inventory.add_argument("--input-bank", required=True, help="Built-in module fixture, such as input-original or input-replacement")
    inventory.add_argument("--output", required=True, help="New JSON file for the authored fixture inventory")
    for name in ("bootstrap-preview", "replace-preview", "apply"):
        sub = recovery.add_parser(name)
        _cartridge_arguments(sub)
        sub.add_argument("--fixture-inventory", required=True, help="Explicit authored inventory JSON; never physical discovery or permission")
        if name == "apply":
            sub.add_argument("file", help="Raw recovery plan exported by a preview command")
        else:
            sub.add_argument("--output", required=True, help="New file for the dependency-bound plan; preview is read-only apart from this export")
    return p


def _fixture_inventory(path):
    """Reread selections on every observation; callers cannot supply capabilities."""
    value = read_json(path)
    required = {"schema_version", "kind", "simulation_only", "provenance", "modules"}
    if (type(value) is not dict or set(value) != required or
            type(value["schema_version"]) is not int or value["schema_version"] != 1 or
            value["kind"] != "disconnected_fixture_inventory" or value["simulation_only"] is not True or
            value["provenance"] != "authored_builtin_module_fixtures_v1" or
            type(value["modules"]) is not dict or set(value["modules"]) != {SLOT}):
        raise ConfigurationError("FIXTURE_INVENTORY", "Expected an explicitly authored built-in simulation inventory; capabilities and physical observations are not accepted")
    module_fixture(value["modules"][SLOT])
    return value["modules"]


def _recovery_dispatch(args, service):
    if args.operation == "inventory":
        module_fixture(args.input_bank)
        value = {"schema_version": 1, "kind": "disconnected_fixture_inventory", "simulation_only": True,
                 "provenance": "authored_builtin_module_fixtures_v1", "modules": {SLOT: args.input_bank}}
        export_json(args.output, value)
        return {"written": args.output, "provenance": value["provenance"], "simulation_only": True,
                "physical_discovery": False}
    recovery = RecoveryService(service, Cartridge(args.directory), args.machine_id,
                               lambda: _fixture_inventory(args.fixture_inventory))
    if args.operation == "apply":
        return recovery.apply(read_json(args.file))
    operation = "bootstrap" if args.operation == "bootstrap-preview" else "replace_input_bank"
    value = recovery.preview(operation)
    export_json(args.output, value)
    return {"written": args.output, "operation": operation, "simulation_only": True,
            "outputs_inhibited": True, "homed": False, "run_permission": False,
            "fixture_inventory": str(Path(args.fixture_inventory).resolve()),
            "inventory_provenance": "authored_builtin_module_fixtures_v1"}


def dispatch(args):
    if args.command == "setup":
        from .setup_cli import dispatch as setup_dispatch
        return setup_dispatch(args)
    service = ConfigurationService(args.store)
    if args.command == "cartridge":
        cartridge = Cartridge(args.directory)
        if args.operation == "inspect":
            return cartridge.load(args.machine_id)
        source = Path(args.configuration).resolve()
        if source in (cartridge.slot_path(0), cartridge.slot_path(1)):
            raise ConfigurationError("SOURCE_CONFLICT", "Configuration source cannot also be a cartridge record destination")
        return cartridge.save(args.machine_id, read_json(source), args.expected_generation)
    if args.command == "recovery":
        return _recovery_dispatch(args, service)
    if args.command == "capabilities":
        return service.capabilities()
    if args.command == "schema":
        return service.schema()
    if args.command == "init":
        return service.initialize(args.actor)
    if args.command == "audit":
        return service.audit()
    if args.command == "profile":
        if args.operation == "list":
            return service.profiles()
        value = service.select_profile(args.profile_id)
    elif args.command == "wiring":
        return service.wiring(read_json(args.file))
    elif args.command == "backup":
        value = service.backup() if args.operation == "create" else service.restore_preview(read_json(args.file))
    elif args.operation == "show":
        return service.show()
    elif args.operation == "validate":
        return service.validate(read_json(args.file))
    elif args.operation == "diff":
        value = service.preview(read_json(args.file))
    else:
        return service.apply(read_json(args.file), args.actor)
    if args.output:
        export_json(args.output, value)
        return {"written": args.output, "simulation_only": True}
    return value


def main(argv=None):
    try:
        args = parser().parse_args(argv)
        result = dispatch(args)
        response = {"schema_version": 1, "ok": True, "simulation_only": True, "result": result}
        status = 0
    except ConfigurationError as error:
        response = {"schema_version": 1, "ok": False, "simulation_only": True, "error": error.as_dict()}
        status = 2
    except OSError as error:
        response = {"schema_version": 1, "ok": False, "simulation_only": True,
                    "error": {"code": "IO_ERROR", "message": str(error), "path": ""}}
        status = 2
    # JSON escapes preserve Unicode without depending on Windows console codepages.
    print(json.dumps(response, indent=2, ensure_ascii=True, allow_nan=False))
    return status


if __name__ == "__main__":
    sys.exit(main())
