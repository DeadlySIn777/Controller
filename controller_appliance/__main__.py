"""Structured local appliance commands, with no shell or machine commands."""
import argparse
import json
from pathlib import Path
import sys

from .service import ApplianceError, ApplianceService, MAX_STATE, _read, load_json


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--directory", type=Path, required=True)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("status", "files", "preview-reset", "preview-undo"):
        commands.add_parser(name)
    edit = commands.add_parser("preview-preferences")
    edit.add_argument("--patch", required=True, help="JSON preference patch")
    edit.add_argument("--expected-revision", required=True, type=int)
    confirm = commands.add_parser("confirm")
    confirm.add_argument("--plan", required=True, type=Path)
    confirm.add_argument("--request-id", required=True)
    confirm.add_argument("--confirmation", required=True)
    download = commands.add_parser("download")
    download.add_argument("--package-id", required=True)
    download.add_argument("--expected-sha256", required=True)
    download.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        app = ApplianceService(args.directory)
        if args.command == "status":
            result = app.status()
        elif args.command == "files":
            result = app.files()
        elif args.command == "preview-reset":
            result = app.preview_reset()
        elif args.command == "preview-undo":
            result = app.preview_undo()
        elif args.command == "preview-preferences":
            if len(args.patch.encode("utf-8")) > MAX_STATE:
                raise ApplianceError("APPLIANCE_SIZE", "Preference patch exceeds its bound")
            result = app.preview_preferences(load_json(args.patch), args.expected_revision)
        elif args.command == "confirm":
            result = app.confirm(load_json(_read(args.plan.absolute(), MAX_STATE)), args.request_id, args.confirmation)
        else:
            package = app.download(args.package_id, args.expected_sha256)
            # Existing archive publisher uses exclusive atomic publication; no overwrite.
            from controller_config.package_archive import _publish
            target = _publish(args.output, package["data"])
            result = {**package["metadata"], "output": str(target), "configuration_applied": False}
        print(json.dumps({"ok": True, "result": result}, allow_nan=False))
        return 0
    except (ApplianceError, OSError, ValueError) as error:
        print(json.dumps({"ok": False, "error": {"code": getattr(error, "code", "APPLIANCE_IO"), "message": str(error)}}))
        return 1


if __name__ == "__main__":
    sys.exit(main())
