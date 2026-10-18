"""Create an isolated, explicitly authored 8/12-joint CNC3 SIM2 fixture."""
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
import sys
import uuid

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from controller_config.setup_service import SetupService, example_draft
from controller_lab.cnc3_configuration import configuration_binding, prepare_configuration

SOURCE_EXTENSIONS = {".py", ".c", ".h", ".cpp", ".hpp", ".v", ".sv", ".ini", ".hal", ".sh", ".json"}


def runtime_sources():
    sources = set()
    for directory in ("cnc3_runtime", "gateware/v3/runtime"):
        for path in (ROOT / directory).rglob("*"):
            if (path.is_file() and path.suffix in SOURCE_EXTENSIONS and
                    not {"__pycache__", "obj_dir", "build", "vendor-src"}.intersection(path.relative_to(ROOT).parts)):
                sources.add(path.relative_to(ROOT).as_posix())
    sources.update(path.relative_to(ROOT).as_posix() for path in (ROOT / "controller_config").glob("*.py"))
    sources.update({"controller_lab/__init__.py", "controller_lab/cnc3_configuration.py", "tests/test_cnc3_configuration.py",
                    "tools/prepare_cnc3_sim2.py", "tools/create_cnc3_qualification_fixture.py"})
    return sorted(sources)


def write_new(path, value):
    with path.open("x", encoding="utf-8") as handle:
        json.dump(value, handle, indent=2, allow_nan=False)
        handle.write("\n")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--motors", type=int, choices=[8, 12], required=True)
    parser.add_argument("--output", type=Path, required=True, help="New isolated fixture directory under reports")
    parser.add_argument("--manifest", type=Path, required=True, help="New manifest under reports")
    args = parser.parse_args()
    output, manifest_path = args.output.resolve(), args.manifest.resolve()
    reports = (ROOT / "reports").resolve()
    if not output.is_relative_to(reports) or not manifest_path.is_relative_to(reports) or output == reports:
        parser.error("Fixture and manifest must remain in the workspace reports directory")
    if output.exists() or manifest_path.exists():
        parser.error("Qualification fixtures and manifests cannot overwrite previous evidence")
    output.mkdir(parents=True, exist_ok=False)
    draft = example_draft(f"sim-machine-{args.motors}motor")
    draft["machine_name"] = f"Authored disconnected CNC3 SIM2 {args.motors}-joint qualification"
    draft["inputs"] = [{"resource": f"SIM.DI{i}", "role": f"fixture_input{i}",
        "equipment_profile": "sim-24v-switch-v1", "voltage_v": 24} for i in range(24)]
    draft["outputs"] = [{"resource": f"SIM.DO{i}", "role": f"fixture_output{i}",
        "equipment_profile": "sim-smart-output-v1", "voltage_v": 24, "current_a": .25} for i in range(16)]
    draft["encoders"] = [{"resource": f"SIM.ABZ{i}", "role": f"fixture_motor{i}_feedback",
        "equipment_profile": "sim-abz-5v-v1", "counts_per_revolution": 3200} for i in range(4)]
    service = SetupService(output / "setup.json")
    service.initialize(actor="qualification_fixture")
    service.save_draft(draft, 0, actor="qualification_fixture")
    service.commit(service.preview(), str(uuid.uuid4()), actor="qualification_fixture")
    binding = configuration_binding(service.backup_snapshot())
    write_new(output / "binding.json", binding)
    run_id = str(uuid.uuid4())
    source_files = runtime_sources()
    encoder_mapping = [{"encoder_channel": i, "motor_channel": i, "edges_per_step": 1} for i in range(4)]
    write_new(output / "encoder-mapping.json", encoder_mapping)
    manifest = prepare_configuration(service, binding, run_id=run_id, source_root=ROOT, source_files=source_files,
                                     encoder_mapping=encoder_mapping)
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    write_new(manifest_path, manifest)
    write_new(output / "preparation.json", {"schema_version": 1, "kind": "authored_cnc3_sim2_fixture",
        "store": service.path.relative_to(ROOT).as_posix(), "binding": (output / "binding.json").relative_to(ROOT).as_posix(),
        "manifest": manifest_path.relative_to(ROOT).as_posix(), "run_id": run_id, "source_files": source_files,
        "encoder_mapping": (output / "encoder-mapping.json").relative_to(ROOT).as_posix(),
        "encoder_mechanics": "one AB edge per emitted/accepted motor STEP; 3200 per motor revolution at explicit 1:1 gearing",
        "all_values_are_authored": True, "hardware_observed": False, "settings_sha256": hashlib.sha256(service.path.read_bytes()).hexdigest(),
        "physical_authority": False, "api_calls": 0})
    print(json.dumps({"status": "PREPARED", "manifest_sha256": manifest["manifest_sha256"],
                      "sources": len(source_files), "simulation_only": True, "physical_authority": False}))


if __name__ == "__main__":
    main()
