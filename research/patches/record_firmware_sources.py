"""Recreate source lock/evidence metadata from the audited local checkouts.

Build status, compiler and distribution are derived from the build helper's
build-local/build-record.json, each target's log (which must end in "EXIT: <code>") and the
executables' SHA-256; nothing is asserted as a literal. The audit results are accepted as
evidence for these executables only if audit/binaries.json names the same hashes. Copies
of the build record, logs and audit results are kept under research/evidence/grblhal/ so
the derived record can be re-checked without the ignored vendor-src tree.

Exit status: 0 only when every target built successfully and the audited executables are
the recorded ones. On any mismatch the record is still written (so the failure is kept),
and the script exits 1.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import re
import shutil
import subprocess
import sys

research = Path(__file__).resolve().parents[1]
build_dir = research / "vendor-src" / "grblhal-simulator" / "build-local"
evidence_dir = research / "evidence" / "grblhal"
TARGETS = ["grblHAL_sim", "grblHAL_validator"]
repos = {
    "fluidnc": ["platformio.ini", "FluidNC/src/GCode.cpp", "FluidNC/src/Kinematics/Cartesian.cpp", ".github/workflows/linux_x86_64.yml"],
    "grblhal-simulator": ["CMakeLists.txt", "README.md", "src/driver.c", "src/validator_driver.c", "src/validator.c", "src/grbl_interface.c"],
    "grblhal-simulator/src/grbl": ["config.h", "gcode.c", "motion_control.c", "hal.h", "changelog.md", "vfs.h"],
    "grblhal-simulator/src/sdcard": ["CMakeLists.txt"],
    "grblhal-rp2040": ["README.md", "CMakeLists.txt", "driver.c", "my_machine.h"],
    "grblhal-stm32h7": ["README.md", "platformio.ini", "Src/driver.c", "Inc/my_machine.h"],
    "linuxcnc": ["src/configure.ac", "docs/src/code/building-linuxcnc.adoc", "docs/src/gcode/g-code.adoc", "docs/src/man/man9/pid.9.adoc", "docs/src/config/ini-homing.adoc", "docs/src/plasma/qtplasmac.adoc"],
}


def git(root, *args):
    return subprocess.check_output(["git", "-C", str(root), *args], text=True).strip()


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def derive_build(build_dir):
    """Return (build dict, environment fields, problems) derived from recorded artefacts."""
    problems = []
    record_path = build_dir / "build-record.json"
    if not record_path.is_file():
        return ({t: "not_recorded" for t in TARGETS}, {"distro": None, "compiler": None},
                [f"{record_path.name} missing: rerun build_grblhal_wsl.py"])
    record = json.loads(record_path.read_text(encoding="utf-8"))
    build = {}
    warnings = set()
    for target in TARGETS:
        entry = record.get("targets", {}).get(target)
        if entry is None:
            build[target] = "not_built"
            problems.append(f"{target}: not in build record")
            continue
        log = build_dir / entry["log"]
        binary = build_dir / entry["binary"]
        log_lines = log.read_text(encoding="utf-8", errors="replace").splitlines() if log.is_file() else []
        match = re.fullmatch(r"EXIT: (-?\d+)", log_lines[-1]) if log_lines else None
        log_exit = int(match[1]) if match else None
        if not log.is_file() or sha256(log) != entry["log_sha256"]:
            status = "log_missing_or_changed_since_build"
        elif log_exit is None or log_exit != entry["exit_code"]:
            status = "log_exit_status_missing_or_inconsistent"
        elif entry["exit_code"] != 0:
            status = f"failed_exit_{entry['exit_code']}"
        elif not binary.is_file() or sha256(binary) != entry["binary_sha256"]:
            status = "binary_missing_or_changed_since_build"
        else:
            status = "success"
        if status != "success":
            problems.append(f"{target}: {status}")
        build[target] = status
        build[target + "_binary_sha256"] = entry.get("binary_sha256")
        build[target + "_log_sha256"] = entry["log_sha256"]
        warnings.update(entry.get("warnings", []))
    build["compiler_warnings"] = sorted(warnings)
    build["build_recorded_utc"] = record.get("recorded_utc")
    environment = {"distro": record.get("distro"), "compiler": record.get("compiler"),
                   "machine": record.get("machine")}
    return build, environment, problems


def derive_audit(build_dir, build):
    """Return (test results, audit identity dict, problems)."""
    results_path = build_dir / "audit" / "results.json"
    binaries_path = build_dir / "audit" / "binaries.json"
    if not results_path.is_file():
        return [], {"results_match_recorded_binaries": False}, ["audit/results.json missing"]
    results = json.loads(results_path.read_text(encoding="utf-8"))
    audited = json.loads(binaries_path.read_text(encoding="utf-8")) if binaries_path.is_file() else {}
    match = bool(audited) and all(audited.get(t) == build.get(t + "_binary_sha256") for t in TARGETS)
    problems = [] if match else ["audit results were not produced by the recorded executables: rerun run_grblhal_audit.py"]
    return results, {"results_match_recorded_binaries": match, "audited_binary_sha256": audited}, problems


EVIDENCE_NAMES = ["build-record.json", "grblHAL_sim-build.log", "grblHAL_validator-build.log",
                  "audit/results.json", "audit/binaries.json"]


def copy_evidence(build_dir, evidence_dir, repo_root):
    """Copy the small artefacts the record is derived from next to it (vendor-src is ignored).

    Returns ({repo-relative copy: sha256}, problems). A copy left from an earlier run whose
    source is now missing is deleted and reported, never kept as if it described this run.
    """
    evidence_dir.mkdir(parents=True, exist_ok=True)
    kept, problems = {}, []
    for name in EVIDENCE_NAMES:
        source = build_dir / name
        target = evidence_dir / Path(name).name
        rel = target.relative_to(repo_root).as_posix()
        if source.is_file():
            shutil.copyfile(source, target)
            kept[rel] = sha256(target)
        elif target.exists():
            target.unlink()
            problems.append(f"{name}: missing from build-local; removed stale evidence copy {rel}")
        else:
            problems.append(f"{name}: missing from build-local; no evidence copy kept")
    return kept, problems


def main():
    sources = []
    for name, paths in repos.items():
        root = research / "vendor-src" / name
        revision = git(root, "rev-parse", "HEAD")
        origin = git(root, "remote", "get-url", "origin").removesuffix(".git").rstrip("/")
        sources.append({
            "name": name, "origin": origin, "commit": revision,
            "commit_date": git(root, "log", "-1", "--format=%cI"),
            "commit_url": f"{origin}/commit/{revision}",
            "nested_gitlinks": git(root, "ls-tree", "-r", "HEAD").splitlines() if name in ["grblhal-rp2040", "grblhal-stm32h7", "grblhal-simulator"] else [],
            "evidence_files": [{"path": p, "url": f"{origin}/blob/{revision}/{p}", "local_sha256": sha256(root / p)} for p in paths],
            "local_diff": git(root, "diff", "--stat"),
        })
        sources[-1]["nested_gitlinks"] = [line for line in sources[-1]["nested_gitlinks"] if line.startswith("160000")]

    build, environment, problems = derive_build(build_dir)
    test_results, audit_identity, audit_problems = derive_audit(build_dir, build)
    problems += audit_problems

    kept, copy_problems = copy_evidence(build_dir, evidence_dir, research.parent)
    problems += copy_problems

    build.update({"source_patch": "patches/grblhal-musl-time-types.patch", "command_script": "patches/build_grblhal_wsl.py",
                  "warning_note": "Compiler warnings are copied from the build logs; Modbus is not exercised by these tests."})
    result = {
        "audit_date_utc": datetime.now(timezone.utc).isoformat(),
        "source_snapshot_note": "Pinned upstream development HEADs, not a selected production release. Source presence is not hardware verification.",
        "environment": {"host": "Windows", "execution": "WSL2 GarciaMechBuilder", **environment, "installed_for_audit": []},
        "derivation": "build statuses, compiler and distro derived from build-local/build-record.json, EXIT lines of the build logs and executable SHA-256; see research/patches/record_firmware_sources.py",
        "sources": sources,
        "build": build,
        "test_script": "patches/run_grblhal_audit.py",
        "audit_identity": audit_identity,
        "test_results": test_results,
        "evidence_copies_sha256": kept,
        "record_problems": problems,
        "not_run": ["FluidNC native/WASM or MCU compilation", "RP2350 hardware-target build", "STM32H7 hardware-target build", "LinuxCNC build/test", "hardware timing/jitter", "encoder feedback hardware", "spindle synchronization", "rigid tapping", "physical probe/limit response"],
    }
    with open(research / "firmware-sources.json", "w", encoding="utf-8", newline="\n") as handle:
        handle.write(json.dumps(result, indent=2) + "\n")
    print("Wrote research/firmware-sources.json with", len(sources), "pinned repositories and", len(test_results), "test records")
    for problem in problems:
        print("PROBLEM:", problem, file=sys.stderr)
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main())
