"""CLI adapter for the same diagnostic/package service used by the browser."""
from pathlib import Path

from .diagnostic_service import DiagnosticService, _convert_error
from .model import ConfigurationError
from .service import export_json


def bounded_read(path, limit):
    with Path(path).open("rb") as stream:
        data = stream.read(limit + 1)
    if len(data) > limit:
        raise ConfigurationError("PACKAGE_INPUT_SIZE", "Input exceeds the declared size bound")
    return data


def dispatch_diagnostics(args):
    from .package_archive import (ArchiveError, read_archive, create_archive,
                                 MAX_ENTRIES, MAX_PAYLOAD_BYTES, MAX_FILE_BYTES)
    from .setup_web import _request_json
    service = DiagnosticService(args.directory)
    try:
        if args.setup_operation == "diagnostics":
            op = args.diagnostic_operation
            if op == "status":
                return service.context()
            if op == "state":
                return service.report()["machine_state"]
            if op == "state-schema":
                from .machine_state import machine_observation_schema
                return machine_observation_schema()
            if op == "observation-example":
                from .machine_state import example_machine_observation
                record = example_machine_observation(service.setup.status())
                export_json(args.output, record)
                return {"written": args.output, "authored_simulation": True,
                        "physical_observation": False, "machine_commands": []}
            if op == "example":
                return service.create_example()
            if op == "append":
                try:
                    record = _request_json(bounded_read(args.file, 128_000))
                except (ValueError, UnicodeError, RecursionError) as error:
                    raise ConfigurationError("DIAGNOSTIC_RECORD", "Expected a bounded finite JSON simulation envelope") from error
                return service.append(record)
            if op == "report":
                return service.report(args.incident_id, args.example)
            return service.package(args.output, "support", args.example)
        op = args.package_operation
        if op == "backup":
            return service.package(args.output, "config")
        if op == "inspect":
            value = read_archive(args.file)
            return {"manifest": value["manifest"], "verified": True,
                    "extracted": False, "executed": False, "machine_commands": []}
        if op == "restore-preview":
            value = service.restore_preview(args.file, args.source)
            export_json(args.output, value)
            return {"written": args.output, "requires_review_and_commit": True,
                    "executed": False, "machine_commands": []}
        entries = {}
        if len(args.entry) > MAX_ENTRIES:
            raise ConfigurationError("PACKAGE_INPUT_SIZE", "Too many package entries")
        total_bytes = 0
        for item in args.entry:
            name, separator, source = item.partition("=")
            if not separator or not source or name in entries:
                raise ConfigurationError("PACKAGE_ENTRY", "Use distinct portable member=source-file entries")
            entries[name] = bounded_read(source, min(MAX_FILE_BYTES, MAX_PAYLOAD_BYTES - total_bytes))
            total_bytes += len(entries[name])
        return create_archive(args.output, entries, "job", metadata={
            "scope": "offline_assets", "motion_authorized": False,
            "execution_supported": False, "automatic_apply": False})
    except ArchiveError as error:
        raise _convert_error(error) from error
