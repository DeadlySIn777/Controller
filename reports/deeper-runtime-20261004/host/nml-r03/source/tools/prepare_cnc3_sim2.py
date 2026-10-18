"""Prepare/verify a reviewed SIM2 manifest; no device or settings writes."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from controller_config.model import ConfigurationError
from controller_config.service import read_json
from controller_config.setup_service import SetupService
from controller_lab.cnc3_configuration import prepare_configuration, verify_configuration
from tools.create_cnc3_qualification_fixture import runtime_sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--store", type=Path, required=True)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--binding", type=Path, help="Exact six-field binding the caller reviewed")
    mode.add_argument("--verify", type=Path, help="Recompute an existing manifest before running it")
    parser.add_argument("--run-id", help="Explicit canonical simulation-run UUID")
    parser.add_argument("--source", action="append", default=[], help="Workspace-relative runtime source; repeat for all sources")
    parser.add_argument("--encoder-map", type=Path, help="Explicit lab encoder-to-motor mapping, required when encoders are configured")
    parser.add_argument("--output", type=Path, help="New manifest, never an overwrite")
    args = parser.parse_args()
    service = SetupService(args.store)
    try:
        if args.verify:
            if args.output or args.run_id or args.source or args.encoder_map:
                parser.error("--verify cannot prepare or write another manifest")
            candidate = read_json(args.verify)
            context = candidate.get("simulation_context", {}) if type(candidate) is dict else {}
            inventory = context.get("source_sha256", {}) if type(context) is dict else {}
            if type(inventory) is not dict or set(inventory) != set(runtime_sources()):
                raise ConfigurationError("SIM2_SOURCE_CLOSURE", "Runtime source inventory changed; prepare a new manifest with the complete source set")
            manifest = verify_configuration(candidate, service, source_root=ROOT, expected_source_files=runtime_sources())
        else:
            if not args.output:
                parser.error("Preparation requires --output")
            output = args.output.resolve()
            if not output.is_relative_to((ROOT / "reports").resolve()) or output == args.store.resolve():
                raise ConfigurationError("SIM2_OUTPUT", "Lab manifests must be new files in the workspace reports directory")
            if set(args.source) != set(runtime_sources()):
                raise ConfigurationError("SIM2_SOURCE_CLOSURE", "Preparation requires the complete current runtime source set")
            manifest = prepare_configuration(service, read_json(args.binding), run_id=args.run_id,
                                             source_root=ROOT, source_files=args.source,
                                             encoder_mapping=read_json(args.encoder_map) if args.encoder_map else None)
            output.parent.mkdir(parents=True, exist_ok=True)
            with output.open("x", encoding="utf-8") as handle:
                json.dump(manifest, handle, indent=2, allow_nan=False)
                handle.write("\n")
        print(json.dumps({"status": "PASS", "manifest_sha256": manifest["manifest_sha256"],
                          "configuration_binding": manifest["configuration_binding"],
                          "simulation_only": True, "physical_backend_allowed": False}))
        return 0
    except (ConfigurationError, OSError) as exc:
        print(json.dumps({"status": "REFUSED", "code": getattr(exc, "code", "SIM2_IO"), "message": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
