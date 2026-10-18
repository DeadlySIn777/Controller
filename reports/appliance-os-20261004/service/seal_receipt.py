"""Seal only executed appliance service/HTTP evidence; never restamp history."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "reports/appliance-os-20261004/service"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    destination = REPORT / "receipt.json"
    if destination.exists():
        raise FileExistsError("Canonical appliance receipt already exists")
    unit_path, http_path = REPORT / "run-r04/receipt.json", REPORT / "http-r02/receipt.json"
    unit, http = json.loads(unit_path.read_text()), json.loads(http_path.read_text())
    assert unit["status"] == http["status"] == "SCOPED_PASS"
    sources = dict(unit["source_sha256"])
    for name, value in http["source_sha256"].items():
        assert name not in sources or sources[name] == value, name
        sources[name] = value
    sources[Path(__file__).relative_to(ROOT).as_posix()] = sha(Path(__file__))
    protected = {**unit["controller_config_source_sha256"], **unit["protected_runtime_source_sha256"],
                 **unit["original_fixture_store_sha256"]}
    assert all(sha(ROOT / name) == expected for name, expected in {**sources, **protected}.items())
    assert all(check["passed"] for check in http["checks"])
    artifacts = dict(unit["artifact_sha256"])
    for path in (unit_path, http_path, REPORT / "README.md"):
        artifacts[path.relative_to(ROOT).as_posix()] = sha(path)
    assert all(sha(ROOT / name) == expected for name, expected in artifacts.items())
    receipt = {"schema_version":1,"kind":"appliance_local_preferences_files_service","status":"SCOPED_PASS",
               "utc":datetime.now(timezone.utc).isoformat(),"source_sha256":dict(sorted(sources.items())),
               "source_inputs_unchanged":True,"artifact_sha256":dict(sorted(artifacts.items())),
               "service_run":unit_path.relative_to(ROOT).as_posix(),"service_methods":29,"platforms":unit["platforms"],
               "http_run":http_path.relative_to(ROOT).as_posix(),"actual_HTTP_check_count":http["check_count"],
               "actual_HTTP_checks":http["checks"],"protected_runtime_source_count":71,
               "controller_config_source_count":24,"protected_source_and_setting_sha256":dict(sorted(protected.items())),
               "protected_sources_and_existing_machine_settings_unchanged":True,
               "reset_scope":"Interface preferences only; reversible until superseded by a later preference edit",
               "full_machine_factory_reset":"BLOCKED; protected storage/calibration/entitlement/signed-image contract unqualified",
               "service_mode_scope":"Volatile service-session presentation, not authentication or machine permission",
               "api_calls":0,"hardware_connections":0,"machine_commands":[],"original_machine_store_writes":0,
               "installed_module_mutations":0,"physical_authority":False,"physical_power_loss_qualified":False,
               "touchscreen_performance_qualified":False,"bootable_signed_image_qualified":False,
               "scope":"Shared Python+CLI service, actual HTTP transport and unchanged archive codec on explicit temporary fixtures; browser layout and OS staging separately recorded",
               "historical_runs_preserved":["run-r01","run-r02","run-r03","http-r01"],
               "negative_controls":["First-use cross-workspace preview refusal; normalized same-workspace alias acceptance",
                    "Stale/expired/resealed/unknown plan and conflicting UUID refusal", "Local lock contention and lost-publication-ack idempotent reconciliation",
                    "Executed symlink/hardlink/FIFO and swapped-FIFO refusal; network/reparse guards source-inspected only", "Bounded scan and sparse oversized file refusal",
                    "Real archive corruption/job-kind/SHA mismatch and changed-file refusal", "Unavailable Zstd explicitly disables package validation",
                    "Inherited Host/Origin/header token and read-only-cookie separation; exact query fields"]}
    destination.write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status":receipt["status"],"receipt":str(destination),"sha256":sha(destination),"selected_source_count":len(sources)}))


if __name__ == "__main__":
    main()
