"""Build pinned upstream grblHAL host targets with an existing Linux GCC.

Run under WSL from repository root. Does not install anything or patch upstream.
The source lists are read from upstream CMakeLists.txt, not reimplemented.

The compiler and distribution are queried at run time (never hard-coded). Each target's
log ends with an "EXIT: <code>" line, and build-local/build-record.json records the exit
code plus SHA-256 of every log and produced executable, so record_firmware_sources.py can
derive success/failure instead of asserting it. A target's previous executable is removed
before it is rebuilt, so a failed build can never leave an older binary looking current.
"""
from datetime import datetime, timezone
from pathlib import Path
import hashlib
import json
import platform
import re
import subprocess
import sys

root = Path(__file__).resolve().parents[1] / "vendor-src" / "grblhal-simulator"
out = root / "build-local"
out.mkdir(exist_ok=True)


def sha256(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def os_release():
    fields = {}
    for line in Path("/etc/os-release").read_text().splitlines():
        key, _, value = line.partition("=")
        fields[key] = value.strip().strip('"')
    return fields


def library_sources(folder):
    return [str(folder / p) for p in re.findall(r"\$\{CMAKE_CURRENT_LIST_DIR\}/([^\s)]+\.c)", (folder / "CMakeLists.txt").read_text())]


compiler = subprocess.run(["gcc", "--version"], capture_output=True, text=True, check=True).stdout.splitlines()[0].strip()
release = os_release()
distro = release.get("PRETTY_NAME") or f"{release.get('NAME', 'unknown')} {release.get('VERSION_ID', '')}".strip()
machine = platform.machine()

common = ["gcc", "-std=gnu11", "-O2", "-fno-strict-aliasing", "-DF_CPU=16000000", "-DPLATFORM_LINUX", "-I" + str(root / "src"), "-I" + str(root / "src/sdcard"), "-I" + str(out)]
(out / "build_info.h").write_text(
    '#define SIM_BUILD_TYPE "Local-GCC-audit"\n'
    '#define SIM_C_FLAGS "-std=gnu11 -O2 -fno-strict-aliasing"\n'
    f'#define SIM_COMPILER {json.dumps(compiler)}\n'
    f'#define SIM_TARGET {json.dumps(f"WSL {distro} {machine}")}\n')
grbl = library_sources(root / "src/grbl")
sdcard = library_sources(root / "src/sdcard")
targets = {
    "grblHAL_validator": (["eeprom.c", "grbl_eeprom_extensions.c", "validator.c", "validator_driver.c", "platform_linux.c"], []),
    "grblHAL_sim": (["main.c", "simulator.c", "driver.c", "eeprom.c", "grbl_eeprom_extensions.c", "mcu.c", "serial.c", "grbl_interface.c", "fs_posix.c", "platform_linux.c"], sdcard),
}
record = {
    "recorded_utc": datetime.now(timezone.utc).isoformat(),
    "distro": distro,
    "machine": machine,
    "compiler": compiler,
    "build_info_sha256": sha256(out / "build_info.h"),
    "targets": {},
}
failed = 0
for target, (specific, extra) in targets.items():
    binary = out / target
    binary.unlink(missing_ok=True)
    command = common + [str(root / "src" / p) for p in specific] + grbl + extra + ["-lm", "-lrt", "-pthread", "-o", str(binary)]
    result = subprocess.run(command, cwd=root, capture_output=True, text=True)
    log = out / (target + "-build.log")
    log.write_text("COMMAND: " + repr(command) + "\n" + "COMPILER: " + compiler + "\n"
                   + result.stdout + result.stderr + f"EXIT: {result.returncode}\n")
    record["targets"][target] = {
        "exit_code": result.returncode,
        "log": log.name,
        "log_sha256": sha256(log),
        "binary": binary.name,
        "binary_sha256": sha256(binary) if result.returncode == 0 and binary.is_file() else None,
        "warnings": sorted(set(re.findall(r"[^/\s]+:\d+:\d+: warning: [^\n]+", result.stderr))),
    }
    print(f"{target}: compiler exit {result.returncode}")
    print(result.stderr[-12000:])
    if result.returncode:
        failed = result.returncode
        break
(out / "build-record.json").write_text(json.dumps(record, indent=2) + "\n")
if failed:
    sys.exit(failed)
