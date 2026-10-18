"""Independent inert control of library-vs-CLI source closure."""
import hashlib
import inspect
import json
from pathlib import Path
import sys
import tempfile
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sys.path.insert(0, str(ROOT))
from controller_config.model import ConfigurationError
from controller_config.setup_service import SetupService, example_draft
from controller_lab.cnc3_configuration import configuration_binding, prepare_configuration, verify_configuration
from tools.create_cnc3_qualification_fixture import runtime_sources

def main(out):
    if out.exists():
        raise RuntimeError("fresh review receipt required")
    sources = [ROOT / name for name in ["controller_lab/cnc3_configuration.py", "controller_lab/__init__.py", "tools/prepare_cnc3_sim2.py", "tools/create_cnc3_qualification_fixture.py", "tests/test_cnc3_configuration.py"]]
    before = {str(path): hashlib.sha256(path.read_bytes()).hexdigest() for path in sources}
    with tempfile.TemporaryDirectory(prefix="closure-fixture-", dir=HERE) as fixture:
        root = Path(fixture).resolve()
        assert root.parent == HERE
        for name in ["runtime.cpp", "safety.hpp"]:
            (root / name).write_text("// inert source closure fixture\n", encoding="utf8")
        service = SetupService(root / "setup.json")
        service.initialize(); service.save_draft(example_draft("sim-machine-12motor"), 0)
        service.commit(service.preview(), str(uuid.uuid4()))
        binding = configuration_binding(service.backup_snapshot())
        run_id = str(uuid.uuid4())
        full = prepare_configuration(service, binding, run_id=run_id, source_root=root, source_files=["runtime.cpp", "safety.hpp"], encoder_mapping=[])
        partial = prepare_configuration(service, binding, run_id=run_id, source_root=root, source_files=["runtime.cpp"], encoder_mapping=[])
        refused = False
        omission_error = None
        try:
            verify_configuration(partial, service, source_root=root, expected_source_files=["runtime.cpp", "safety.hpp"])
        except ConfigurationError as error:
            refused = True
            omission_error = error.code
        full_matches = verify_configuration(full, service, source_root=root, expected_source_files=["runtime.cpp", "safety.hpp"]) == full
        missing_closure_refused = False
        try:
            verify_configuration(full, service, source_root=root)
        except TypeError:
            missing_closure_refused = True
        signature = str(inspect.signature(verify_configuration))
        result = {"status": "LIBRARY_REJECTED_SELF_SELECTED_SUBSET" if refused else "LIBRARY_ACCEPTED_SELF_SELECTED_SUBSET_WITHOUT_TRUSTED_CLOSURE",
            "full_inventory": sorted(full["simulation_context"]["source_sha256"]),
            "partial_inventory": sorted(partial["simulation_context"]["source_sha256"]),
            "different_source_digest": full["simulation_context"]["source_digest"] != partial["simulation_context"]["source_digest"],
            "omission_refusal_code": omission_error, "complete_expected_closure_accepted": full_matches,
            "trusted_expected_closure_argument_is_required": missing_closure_refused,
            "verify_signature": signature,
            "trusted_runtime_closure_binds_controller_lab_initializer": "controller_lab/__init__.py" in runtime_sources(),
            "scope": "Actual library calls with a temporary inert two-source fixture; no CLI/device, no existing settings or source mutation",
            "physical_authority": False, "source_sha256": before,
            "inputs_unchanged": all(hashlib.sha256(path.read_bytes()).hexdigest() == before[str(path)] for path in sources)}
    with out.open("x", encoding="utf8") as handle:
        json.dump(result, handle, indent=2); handle.write("\n")
    print(json.dumps({key: result[key] for key in ["status", "trusted_runtime_closure_binds_controller_lab_initializer", "inputs_unchanged"]}))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    main(parser.parse_args().out.resolve())
