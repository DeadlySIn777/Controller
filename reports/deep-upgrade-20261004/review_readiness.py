"""Independent same-revision substitution probes on temporary SIM stores."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import sys
import tempfile
import uuid
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from controller_config.model import ConfigurationError
from controller_config.package_archive import create_archive
from controller_config.service import atomic_write, digest, read_json, _seal
from controller_config.setup_readiness import ReadinessService
from controller_config.setup_service import SetupService, example_draft, validate_draft


def main():
    source = ROOT / "controller_config/setup_readiness.py"
    before = hashlib.sha256(source.read_bytes()).hexdigest()
    results = []
    for changed in ("store_id", "generation", "active_configuration", "draft"):
        with tempfile.TemporaryDirectory(prefix="readiness-binding-review-") as directory:
            setup = SetupService(Path(directory) / "setup.json")
            setup.initialize()
            setup.save_draft(example_draft("sim-mill-3axis"), 0)
            setup.commit(setup.preview(), "independent-review")
            original = setup.status()
            def archive_then_substitute(*args, **kwargs):
                result = create_archive(*args, **kwargs)
                state = read_json(setup.path)
                state.pop("integrity_sha256")
                if changed == "store_id":
                    state["store_id"] = str(uuid.uuid4())
                elif changed == "generation":
                    state["generation"] += 1
                    state["active"]["generation"] = state["generation"]
                elif changed == "draft":
                    state["draft"]["machine_name"] += " changed after archive"
                else:
                    state["active"]["draft"]["machine_name"] += " replaced active"
                    state["draft"] = state["active"]["draft"]
                    checked = validate_draft(state["active"]["draft"], require_complete=True)
                    state["active"].update(configuration_sha256=digest(state["active"]["draft"]),
                        calculations=checked["calculations"], wiring=checked["wiring"])
                atomic_write(setup.path, _seal(state))
                # Prove this is a valid changed store rather than a checksum or
                # malformed-store rejection. Revision and epoch stay identical.
                substitute = setup.status()
                assert substitute["revision"] == original["revision"]
                assert substitute["epoch"] == original["epoch"]
                return result
            with patch("controller_config.package_archive.create_archive", side_effect=archive_then_substitute):
                try:
                    ReadinessService(directory).rehearse(original["revision"])
                except ConfigurationError as error:
                    results.append({"changed": changed, "valid_store_same_revision_and_epoch": True,
                                    "error_code": error.code, "passed": error.code == "SETUP_STALE"})
                else:
                    results.append({"changed": changed, "passed": False, "error_code": None})
    receipt = {"scope": "independent_temporary_simulation_store_binding_review",
               "completed_utc": datetime.now(timezone.utc).isoformat(), "cases": results,
               "source_sha256": before, "source_unchanged": before == hashlib.sha256(source.read_bytes()).hexdigest(),
               "paid_calls": 0, "physical_commands": 0}
    (Path(__file__).parent / "readiness-binding-review.json").write_text(json.dumps(receipt, indent=2)+"\n", encoding="utf-8")
    print(json.dumps(receipt))
    return 0 if receipt["source_unchanged"] and all(result["passed"] for result in results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
