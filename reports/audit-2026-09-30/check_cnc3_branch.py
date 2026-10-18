"""Narrow disconnected audit of an existing unmerged worktree; never edits it."""
from pathlib import Path
import hashlib
import json
import os
import shlex
import shutil
import subprocess
import sys
import uuid

BRANCH = Path("C:/Users/Gluis/claude-worktrees/controller-interface-spec")
OUT = Path(__file__).resolve().parent / "CNC3_BRANCH_CHECKS"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def git(*args):
    return subprocess.check_output(["git", "-C", str(BRANCH), *args], text=True).strip()


def snapshot(paths):
    return {name: digest(BRANCH / name) for name in paths}


def wsl_path(path):
    path = path.resolve().as_posix()
    return "/mnt/" + path[0].lower() + path[2:]


def main():
    if OUT.exists():
        raise SystemExit("Refusing to overwrite an earlier branch audit")
    OUT.mkdir()
    paths = set(git("diff", "--name-only", "e994311..HEAD").splitlines())
    paths.update(git("ls-files", "AGENTS.md", "PROJECT_MEMORY.md", "README.md", "docs/BUILD_PLAN.md",
                     "docs/PLATFORM_ROADMAP.md", "docs/DISPLAY_TIERS.md", "reports/ENGINEERING_STATUS.md").splitlines())
    paths = sorted(paths)
    before = snapshot(paths)
    inputs = OUT / "inputs"
    for name in paths:
        target = inputs / name
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(BRANCH / name, target)
    if before != snapshot(paths):
        raise SystemExit("Branch changed during snapshot")
    commands = [
        ("interface-spec", [sys.executable, "tools/interface_spec_validate.py", "--check"]),
        ("protocol-arithmetic", [sys.executable, "tools/is1_protocol_check.py"]),
        ("protocol-codec", [sys.executable, "gateware/v3/tools/protocol_v3.py", "--check"]),
        ("generated-layout", [sys.executable, "gateware/v3/tools/gen_c_layout.py", "--check"]),
        ("spec-tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_interface_spec.py", "-v"]),
        ("codec-tests", [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_protocol_v3_reference.py", "-v"]),
    ]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    results = []
    for name, command in commands:
        result = subprocess.run(command, cwd=BRANCH, env=env, capture_output=True, text=True)
        log = OUT / (name + ".log")
        log.write_text(result.stdout + result.stderr, encoding="utf-8", newline="\n")
        results.append({"name": name, "command": command, "exit_code": result.returncode, "log": log.name})
        print(f"{name}: exit {result.returncode}", flush=True)
    # Compile from the preserved audit copy into a new task-local directory. No existing
    # rootfs work folder is removed, and no branch input or historical artifact is changed.
    work = "/work/cnc3-audit-" + uuid.uuid4().hex
    source = wsl_path(inputs / "cnc3")
    artifacts = wsl_path(OUT / "build-artifacts")
    script = "\n".join([
        "#!/bin/sh", "set -eu",
        "task_root=${CONTROLLER_LAB_ROOTFS:-/root/.cache/controller-lab-linuxcnc/rootfs}",
        "test -f \"$task_root/etc/debian_version\"",
        "task_work=" + shlex.quote(work),
        "test ! -e \"$task_root$task_work\"",
        "mkdir -p \"$task_root$task_work\"",
        "cp -a " + shlex.quote(source) + " \"$task_root$task_work/cnc3\"",
        "export CONTROLLER_LAB_ROOTFS=\"$task_root\" CNC3_AUDIT_WORK=\"$task_work\"",
        "unshare --mount --pid --net --fork --kill-child sh -c '" +
        "mount -t proc proc \"$CONTROLLER_LAB_ROOTFS/proc\"; " +
        "exec chroot \"$CONTROLLER_LAB_ROOTFS\" sh -c \"gcc --version; " +
        "ASAN_OPTIONS=detect_leaks=1:halt_on_error=1 UBSAN_OPTIONS=halt_on_error=1 " +
        "sh $CNC3_AUDIT_WORK/cnc3/tools/host_tests.sh $CNC3_AUDIT_WORK/build\"'",
        "cp -a \"$task_root$task_work/build\" " + shlex.quote(artifacts), "",
    ])
    (OUT / "run-c-host.sh").write_text(script, encoding="utf-8", newline="\n")
    command = ["wsl", "-d", "GarciaMechBuilder", "--", "sh", wsl_path(OUT / "run-c-host.sh")]
    result = subprocess.run(command, env=env, capture_output=True)
    (OUT / "c-host.log").write_bytes(result.stdout + result.stderr)
    results.append({"name": "c-host", "command": command, "exit_code": result.returncode,
                    "log": "c-host.log", "rootfs_work": work})
    print(f"c-host: exit {result.returncode}", flush=True)
    after = snapshot(paths)
    changed = [name for name in paths if before[name] != after[name]]
    receipt = {"scope": "Unmerged IS-1/CNC3 source/specification/host-model checks only",
               "manufacturing_ready": False, "branch": git("branch", "--show-current"),
               "head": git("rev-parse", "HEAD"), "worktree": str(BRANCH),
               "worktree_status": git("status", "--short"), "input_count": len(paths),
               "source_before_sha256": before, "source_after_sha256": after,
               "changed_during_run": changed, "commands": results,
               "checks_pass": not changed and all(r["exit_code"] == 0 for r in results),
               "evidence_class": "Specification checks plus Python/C host tests against a C endpoint model; no RTL/HAL/LinuxCNC/physical transport",
               "artifacts_sha256": {str(p.relative_to(OUT)).replace("\\", "/"): digest(p)
                   for p in sorted(OUT.rglob("*")) if p.is_file() and "inputs" not in p.relative_to(OUT).parts}}
    (OUT / "review.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf-8", newline="\n")
    print(json.dumps({"checks_pass": receipt["checks_pass"], "input_count": len(paths), "changed": changed}))
    return 0 if receipt["checks_pass"] else 1


if __name__ == "__main__":
    sys.exit(main())
