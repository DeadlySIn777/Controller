"""Structured offline image commands; no disk writer or OS installer."""
import argparse
import json
from pathlib import Path

from controller_config.model import ConfigurationError
from .image import DEV_PROFILE, MANIFEST, definition, profiles, stage, verify_image
from .preflight import preflight, recovery


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    commands.add_parser("profiles")
    for name in ("definition", "stage", "inspect", "preflight", "recovery"):
        command = commands.add_parser(name)
        command.add_argument("--profile", default=DEV_PROFILE)
        command.add_argument("--allow-development", action="store_true")
        if name == "stage":
            command.add_argument("--source-root", type=Path, required=True)
            command.add_argument("--output", type=Path, required=True)
            command.add_argument("--release-id", default="development-r1")
        if name in ("inspect", "preflight", "recovery"):
            command.add_argument("--root", type=Path, required=True)
            command.add_argument("--manifest", type=Path)
        if name in ("preflight", "recovery"):
            command.add_argument("--workspace", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        if args.command == "profiles":
            result = {"profiles": profiles(), "physical_authority": False}
        else:
            options = {"profile": args.profile, "allow_development": args.allow_development}
            if args.command == "definition":
                result = definition(**options)
            elif args.command == "stage":
                result = stage(args.source_root, args.output, release_id=args.release_id, **options)
            else:
                root = args.root.absolute()
                manifest = args.manifest.absolute().relative_to(root).as_posix() if args.manifest else MANIFEST
                if args.command == "inspect":
                    verified = verify_image(root, manifest_path=manifest, exact_overlay=True, **options)
                    result = {"status": "VERIFIED_DEVELOPMENT_OVERLAY", "manifest_sha256": verified["manifest_sha256"], "physical_authority": False, "bootable_image_qualified": False}
                else:
                    result = (preflight if args.command == "preflight" else recovery)(root, args.workspace, manifest_path=manifest, **options)
        print(json.dumps({"ok": True, "result": result}, allow_nan=False))
        return 0
    except (ConfigurationError, OSError, ValueError, RecursionError) as error:
        print(json.dumps({"ok": False, "error": {"code": getattr(error, "code", "OS_IO"), "message": str(error)}, "physical_authority": False}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
