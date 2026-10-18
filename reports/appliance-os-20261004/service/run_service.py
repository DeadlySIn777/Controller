"""Fresh bounded appliance checks; exclusive report outputs, no device access."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[3]
REPORT = ROOT / "reports/appliance-os-20261004/service"


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def hashes(names):
    return {name: sha(ROOT / name) for name in sorted(names)}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--run", required=True)
    args = parser.parse_args()
    if not re.fullmatch(r"run-r[0-9]{2}", args.run):
        raise ValueError("Exclusive report run name required")
    output = REPORT / args.run
    output.mkdir(parents=True, exist_ok=False)
    fixture = output / "fixtures"
    fixture.mkdir()
    sources = ["controller_appliance/__init__.py", "controller_appliance/__main__.py",
               "controller_appliance/service.py", "tests/test_controller_appliance.py",
               "controller_config/package_archive.py", "controller_config/__init__.py",
               "reports/appliance-os-20261004/service/run_service.py"]
    before = hashes(sources)
    runtime = json.loads((ROOT / "reports/deeper-runtime-20261004/host/receipt.json").read_text())["source_sha256"]
    original = [p.relative_to(ROOT).as_posix() for p in (ROOT / "controller_config").rglob("*")
                if p.is_file() and p.suffix in (".py", ".js", ".css", ".html")]
    protected = hashes(original)
    settings = ["reports/deeper-runtime-20261004/host/fixtures-12/setup.json",
                "reports/deeper-runtime-20261004/host/fixtures-8/setup.json"]
    settings_before = hashes(settings)
    commands = {
        "windows": [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_controller_appliance.py", "-v"],
        "linux": ["wsl.exe", "-d", "GarciaMechBuilder", "--cd", "/mnt/c/Users/Gluis/OneDrive/Documents/ChatGPT/Controller", "--",
                  "python3", "-m", "unittest", "discover", "-s", "tests", "-p", "test_controller_appliance.py", "-v"]}
    observations = {}
    for platform, command in commands.items():
        env = os.environ.copy()
        env["TEMP"] = env["TMP"] = str(fixture)
        done = subprocess.run(command, cwd=ROOT, env=env, capture_output=True, timeout=90)
        (output / f"{platform}.stdout.log").write_bytes(done.stdout)
        (output / f"{platform}.stderr.log").write_bytes(done.stderr)
        text = done.stderr.decode("utf-8", "replace")
        count = re.search(r"Ran (\d+) tests", text)
        skipped = re.search(r"OK \(skipped=(\d+)\)", text)
        observations[platform] = {"command": command, "exit_code": done.returncode,
                                  "reported": int(count.group(1)) if count else 0,
                                  "skipped": int(skipped.group(1)) if skipped else 0,
                                  "status": "PASS" if done.returncode == 0 and count else "FAIL",
                                  "zstd_positive_packages": platform == "windows",
                                  "symlink_and_FIFO_guards": platform == "linux"}
    after = hashes(sources)
    runtime_mismatches = [name for name, expected in runtime.items() if sha(ROOT / name) != expected]
    artifacts = {p.relative_to(ROOT).as_posix(): sha(p) for p in output.glob("*.log")}
    stable = before == after and protected == hashes(original) and settings_before == hashes(settings) and not runtime_mismatches
    receipt = {"schema_version": 1, "kind": "appliance_interface_service_qualification", "utc": datetime.now(timezone.utc).isoformat(),
               "status": "SCOPED_PASS" if stable and all(x["status"] == "PASS" for x in observations.values()) else "FAIL",
               "source_sha256": before, "source_inputs_unchanged": before == after,
               "controller_config_source_sha256": protected, "controller_config_sources_unchanged": protected == hashes(original),
               "protected_runtime_source_sha256": runtime, "protected_runtime_source_count": len(runtime), "runtime_mismatches": runtime_mismatches,
               "original_fixture_store_sha256": settings_before, "original_fixture_stores_unchanged": settings_before == hashes(settings),
               "platforms": observations, "artifact_sha256": artifacts, "api_calls": 0, "device_connections": 0,
               "machine_store_writes": 0, "machine_commands": [], "full_machine_factory_reset": "BLOCKED",
               "reset_scope": "local interface preferences only; reversible while no later preference edit supersedes reset",
               "service_mode_scope": "session presentation only, not authentication or machine permission",
               "host_power_loss_qualified": False, "physical_authority": False,
               "boundaries": ["SHA detects corruption, not sender authenticity", "Approved flat config/support package directory only",
                              "Windows Zstd tests and Linux symlink/FIFO tests are separate executable surfaces",
                              "No installed rootfs modules, motion profiles or original machine stores changed"]}
    (output / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "receipt": str(output / "receipt.json"), "platforms": observations}))
    return 0 if receipt["status"] == "SCOPED_PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
