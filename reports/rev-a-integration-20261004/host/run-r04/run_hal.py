"""Fresh, source-bound disconnected CNC3 HAL/actual serial-RTL refusal run."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import time
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
PROJECT = HERE.parents[2]
CANDIDATE = PROJECT / "reports/cnc3-is2-profile-20261002/profile-candidate-r02"
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def unix(p):
    path = p.resolve().as_posix()
    return "/mnt/" + path[0].lower() + path[2:]

def main(out):
    if out.exists():
        raise RuntimeError("fresh output directory required")
    out.mkdir(parents=True)
    sources = [p for p in HERE.rglob("*") if p.is_file() and p.suffix in (".py", ".sh", ".c", ".cpp", ".h") and "__pycache__" not in p.parts and not any(part.startswith("run-r") for part in p.parts)]
    candidate_sources = list((CANDIDATE / "rtl").glob("*.v")) + list((CANDIDATE / "driver").glob("*")) + [CANDIDATE / "originals/cnc3.c"]
    candidate_sources = [p for p in candidate_sources if p.is_file()]
    before = {str(p): sha(p) for p in sources + candidate_sources}
    for p in candidate_sources:
        target = out / "inputs" / p.relative_to(CANDIDATE)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
    for p in sources:
        target = out / p.relative_to(HERE)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(p, target)
    (out / "input-source-hashes.json").write_text(json.dumps(before, indent=2) + "\n")
    run_key = uuid.uuid4().hex
    work = "/work/rev-a-host-20261004-" + run_key
    distro = os.environ.get("CNC3_WSL_DISTRO", "GarciaMechBuilder")
    executions = []
    observations = []
    error = None
    installed = False
    def run(stage, command, timeout=600):
        started = time.monotonic()
        result = subprocess.run(command, capture_output=True, timeout=timeout)
        log = out / (stage + ".log")
        log.write_bytes(result.stdout + result.stderr)
        executions.append({"stage": stage, "command": command, "exit_code": result.returncode,
                           "seconds": round(time.monotonic() - started, 3), "log_sha256": sha(log)})
        print(json.dumps({"stage": stage, "exit_code": result.returncode}), flush=True)
        if result.returncode:
            raise RuntimeError(f"{stage} failed; see {log}")
        return result
    wsl = ["wsl", "-d", distro, "-u", "root", "--"]
    try:
        run("build", wsl + ["sh", unix(out / "build.sh"), unix(out), run_key], timeout=900)
        run("install-temporary-modules", wsl + ["python3", unix(out / "module_guard.py"), "install", work, unix(out)])
        installed = True
        for case in ["denied", "qualification", "crc", "encoder", "mpg", "IS1"]:
            module = f"cnc3_refusal_{'IS1' if case == 'IS1' else 'IS2'}_{run_key}"
            run("HAL-" + case, wsl + ["timeout", "-s", "KILL", "150", "unshare", "--mount", "--pid", "--ipc", "--net", "--fork", "--kill-child", "sh", unix(out / "run_case.sh"), work, module, case], timeout=170)
            result = run("collect-" + case, wsl + ["cat", "/root/.cache/controller-lab-linuxcnc/rootfs" + work + f"/observation-{case}.json"])
            observation = json.loads(result.stdout)
            observations.append(observation)
            (out / f"observation-{case}.json").write_text(json.dumps(observation, indent=2) + "\n")
            run("HAL-commands-" + case, wsl + ["cat", "/root/.cache/controller-lab-linuxcnc/rootfs" + work + f"/halcmd-{case}.log"])
    except Exception as exc:
        error = repr(exc)
    finally:
        if installed:
            try:
                run("restore-installed-modules", wsl + ["python3", unix(out / "module_guard.py"), "restore", work, unix(out)])
            except Exception as exc:
                error = (error or "") + "; restore: " + repr(exc)
    unchanged = all(sha(Path(p)) == digest for p, digest in before.items())
    modules_preserved = (out / "installed-modules-after.json").exists() and json.loads((out / "installed-modules-before.json").read_text()) == json.loads((out / "installed-modules-after.json").read_text())
    passed = not error and unchanged and modules_preserved and len(observations) == 6 and all(o["status"] == "PASS" for o in observations)
    receipt = {"status": "PASS" if passed else "FAIL", "error": error, "run_key": run_key,
               "source_sha256": before, "source_inputs_unchanged": unchanged,
               "installed_existing_rootfs_modules_preserved": modules_preserved,
               "rootfs_work": work, "WSL_distro": distro, "executions": executions,
               "observations": observations,
               "scope": {"actual_compiled_LinuxCNC_HAL_scheduler": passed,
                         "declared_motor_channels": 12, "declared_base_encoder_channels": 4,
                         "actual_serial_SPI_endpoint": "unchanged report-local incomplete IS2 profile candidate",
                         "actual_CNC3_C_driver": "unchanged report-local IS2 derivative; original IS1 negative control",
                         "main_gateware_v3_is_stateful": False, "successful_motion_discovery": False,
                         "actual_LinuxCNC_motion_controller_trajectory": False,
                         "all12_HAL_to_STEP_and_feedback_ACTIVE": False,
                         "complete_IOL1_limits_probe_providers": False,
                         "target_realtime_or_physical_qualification": False,
                         "frozen_command_bytes": 96, "frozen_feedback_bytes": 176,
                         "paid_provider_calls": 0, "hardware_device_connections": 0},
               "full_requested_milestone_complete": False,
               "license_boundary": "Retained CNC3 sources identify LicenseRef-Proprietary; local combined-module descriptor matches. No redistribution or binary release qualification.",
               "artifact_sha256": {p.relative_to(out).as_posix(): sha(p) for p in out.rglob("*") if p.is_file()}}
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n")
    print(json.dumps({"status": receipt["status"], "error": error, "cases": len(observations), "full_requested_milestone_complete": False}), flush=True)
    return 0 if passed else 1

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(main(args.out.resolve()))
