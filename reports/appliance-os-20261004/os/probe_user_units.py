"""Additive offline user-unit syntax probe in its own runtime directory."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import re
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def main():
    out = HERE / "user-unit-probe-r01"; out.mkdir(exist_ok=False)
    raw = json.loads((HERE / "run-r01/receipt.json").read_text())
    work = raw["rootfs_work"]
    assert re.fullmatch(r"/work/controller-os-[0-9a-f]{32}", work)
    rootfs = "/root/.cache/controller-lab-linuxcnc/rootfs"
    wsl = ["wsl", "-d", "GarciaMechBuilder", "-u", "root", "--"]
    units = work + "/rootfs/etc/systemd/user/"
    current = {name: value for name, value in raw["artifact_sha256"].items() if name.startswith("image-a/rootfs/etc/systemd/user/")}
    for name, value in current.items(): assert sha(HERE / "run-r01" / name) == value
    commands = [wsl + ["chroot", rootfs, "mkdir", "-m", "700", work + "/unit-probe-runtime"],
        wsl + ["chroot", rootfs, "/usr/bin/env", "XDG_RUNTIME_DIR=" + work + "/unit-probe-runtime",
               "SYSTEMD_UNIT_PATH=" + units + ":/usr/lib/systemd/user",
               "systemd-analyze", "--user", "verify", units + "controller-kiosk-recovery.service",
               units + "controller-kiosk-recovery.target"]]
    executions = []
    for name, command in zip(("create-own-runtime-directory", "user-recovery-syntax"), commands):
        result = subprocess.run(command, capture_output=True, timeout=30)
        log = out / (name + ".log"); log.write_bytes(result.stdout + result.stderr)
        executions.append({"stage": name, "command": command, "exit_code": result.returncode, "log_sha256": sha(log)})
        if result.returncode: break
    stable = all(sha(HERE / "run-r01" / name) == value for name, value in current.items())
    value = {"schema_version": 1, "utc": datetime.now(timezone.utc).isoformat(),
        "status": "PASS_USER_RECOVERY_UNIT_SYNTAX" if len(executions) == 2 and all(v["exit_code"] == 0 for v in executions) and stable else "NOT_QUALIFIED",
        "scope": "Offline systemd user-unit parser for two exact staged recovery units, isolated chroot runtime directory; no manager activation or GUI service execution",
        "executions": executions, "staged_user_unit_sha256": current,
        "staged_unit_artifact_base": "reports/appliance-os-20261004/os/run-r01", "units_unchanged": stable,
        "runner_sha256": sha(__file__), "base_receipt_sha256": sha(HERE / "run-r01/receipt.json"),
        "retained_initial_probe": "run-r01/systemd-user-recovery-syntax.log",
        "initial_probe_failure": "Inherited WSLg runtime directory does not exist inside isolated rootfs",
        "unit_startup_executed": False, "browser_launched": False, "systemd_manager_activated": False,
        "actual_physical_boot": False, "services_installed_or_enabled": False,
        "desktop_or_network_config_modified": False, "paid_api_calls": 0, "physical_device_connections": 0}
    with (out / "receipt.json").open("x", encoding="utf-8", newline="\n") as stream:
        json.dump(value, stream, indent=2); stream.write("\n")
    print(json.dumps({"status": value["status"], "receipt_sha256": sha(out / "receipt.json")}))
    return 0 if value["status"] == "PASS_USER_RECOVERY_UNIT_SYNTAX" else 1


if __name__ == "__main__":
    raise SystemExit(main())
