"""Compile and execute copied SIM providers; preserve all attempts and mutations."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import uuid

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
SOURCE = ROOT / "cnc3_runtime/providers"
FILES = ("provider_ledger.hpp", "virtual_provider.hpp", "test_providers.cpp")

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def linux(path):
    value = path.resolve().as_posix()
    if sys.platform == "win32":
        return "/mnt/" + value[0].lower() + value[2:]
    return value

def main(out):
    if out.exists():
        raise RuntimeError("fresh output directory required")
    out.mkdir(parents=True)
    before = {str(SOURCE / name): sha(SOURCE / name) for name in FILES}
    before[str(Path(__file__))] = sha(Path(__file__))
    before[str(HERE / "run_in_rootfs.sh")] = sha(HERE / "run_in_rootfs.sh")
    inputs = out / "inputs"
    inputs.mkdir()
    for name in FILES:
        shutil.copyfile(SOURCE / name, inputs / name)
    commands = []
    rootfs = "/root/.cache/controller-lab-linuxcnc/rootfs"
    work = "/work/provider-" + uuid.uuid4().hex
    def run(stage, command, expected=0, timeout=180):
        full = (["wsl", "-d", "GarciaMechBuilder", "--"] if sys.platform == "win32" else []) + command
        result = subprocess.run(full, capture_output=True, text=True, timeout=timeout)
        (out / (stage + ".stdout.log")).write_text(result.stdout, encoding="utf8")
        (out / (stage + ".stderr.log")).write_text(result.stderr, encoding="utf8")
        row = {"stage": stage, "command": full, "exit_code": result.returncode}
        commands.append(row)
        if (expected == 0 and result.returncode != 0) or (expected == "nonzero" and result.returncode == 0):
            raise RuntimeError(stage + " produced unexpected exit " + str(result.returncode))
        return result
    receipt = {"status": "RUNNING", "utc": datetime.now(timezone.utc).isoformat(),
               "source_sha256": before, "executions": commands, "scope": "Copied standalone C++ SIM provider/plant execution; not continuous HAL/RTL or physical qualification",
               "physical_authority": False, "production_profile_complete": False,
               "device_connections": 0, "paid_API_calls": 0, "frozen_wire_protocol_modified": False}
    try:
        # Use the existing isolated glibc compiler/runtime, including installed
        # sanitizer libraries. This creates only a new UUID-keyed work tree.
        run("create-rootfs-work", ["mkdir", rootfs + work])
        run("copy-rootfs-inputs", ["cp", "-r", linux(inputs), rootfs + work + "/inputs"])
        receipt["rootfs_work"] = rootfs + work
        run("compiler-version", ["chroot", rootfs, "g++", "--version"])
        flags = ["-std=c++17", "-Wall", "-Wextra", "-Werror", "-pedantic"]
        normal = out / "providers-normal"
        run("normal-compile", ["chroot", rootfs, "g++", *flags, "-O2", work + "/inputs/test_providers.cpp", "-o", work + "/providers-normal"])
        normal_result = run("normal-run", ["chroot", rootfs, work + "/providers-normal"])
        run("normal-artifact-copy", ["cp", rootfs + work + "/providers-normal", linux(normal)])
        receipt["normal"] = json.loads(normal_result.stdout)
        sanitizer = out / "providers-sanitized"
        run("sanitizer-compile", ["chroot", rootfs, "g++", *flags, "-O1", "-g", "-fsanitize=address,undefined", "-fno-omit-frame-pointer", work + "/inputs/test_providers.cpp", "-o", work + "/providers-sanitized"])
        sanitizer_result = run("sanitizer-run", ["unshare", "--mount", "--pid", "--fork", "--", "/bin/sh", linux(HERE / "run_in_rootfs.sh"), rootfs, work + "/providers-sanitized"])
        run("sanitizer-artifact-copy", ["cp", rootfs + work + "/providers-sanitized", linux(sanitizer)])
        receipt["sanitized"] = json.loads(sanitizer_result.stdout)
        changes = [
            ("crc", "provider_ledger.hpp", "record.crc != record.checksum()", "false"),
            ("full-source-binding", "provider_ledger.hpp", "record.source_digest != identity_.source_digest", "false"),
            ("full-config-binding", "provider_ledger.hpp", "record.config_digest != identity_.config_digest", "false"),
            ("freshness", "provider_ledger.hpp", "now - accepted_.captured_tick >= stale_ticks", "false"),
            ("ordered-sequence", "provider_ledger.hpp", "record.sequence != accepted_.sequence + 1", "false"),
            ("independent-motion-gate", "virtual_provider.hpp", "(inputs_.gate_high & needed) != needed || (inputs_.opi_ok & needed) != needed", "(((inputs_.gate_high & needed) != needed || (inputs_.opi_ok & needed) != needed) && false)"),
            ("independent-output-gate", "virtual_provider.hpp", "inputs_.output_gate_high && inputs_.output_opi_ok", "(inputs_.output_gate_high || !inputs_.output_gate_high)"),
            ("motor-gate-opi-phase", "virtual_provider.hpp", "previous_motor_request_ = motor_requested;", "result.opi_ok = result.gate_high; previous_motor_request_ = motor_requested;"),
            ("output-domain-mixing", "virtual_provider.hpp", "if (outputs.output_opi_rearm &&", "if ((outputs.output_opi_rearm || (outputs.opi_rearm & 8)) &&"),
            ("consumed-reset", "virtual_provider.hpp", "!press_consumed_ && tick - press_start_", "tick - press_start_"),
            ("forced-watchdog-clearance", "virtual_provider.hpp", "previous_forced_fault_ && !forced_fault", "previous_forced_fault_ && forced_fault"),
            ("watchdog-recovery-boundary", "virtual_provider.hpp", "now - idle_since_ >= recovery_", "now - idle_since_ > recovery_"),
        ]
        receipt["mutation_controls"] = []
        for name, filename, old, new in changes:
            directory = out / ("mutation-" + name)
            directory.mkdir()
            for source_name in FILES:
                shutil.copyfile(inputs / source_name, directory / source_name)
            path = directory / filename
            text = path.read_text(encoding="utf8")
            if text.count(old) != 1:
                raise RuntimeError("mutation token not unique: " + name)
            path.write_text(text.replace(old, new), encoding="utf8")
            binary = directory / "provider-test"
            run("mutation-" + name + "-copy", ["cp", "-r", linux(directory), rootfs + work + "/" + directory.name])
            run("mutation-" + name + "-compile", ["chroot", rootfs, "g++", *flags, "-O2", work + "/" + directory.name + "/test_providers.cpp", "-o", work + "/" + directory.name + "/provider-test"])
            result = run("mutation-" + name + "-run", ["chroot", rootfs, work + "/" + directory.name + "/provider-test"], expected="nonzero")
            run("mutation-" + name + "-artifact-copy", ["cp", rootfs + work + "/" + directory.name + "/provider-test", linux(binary)])
            receipt["mutation_controls"].append({"case": name, "status": "DETECTED", "mutated_copy": str(path.relative_to(out)), "mutated_sha256": sha(path), "failure": result.stderr.strip()})
        receipt["source_inputs_unchanged"] = all(sha(Path(name)) == digest for name, digest in before.items())
        if not receipt["source_inputs_unchanged"]:
            raise RuntimeError("input source changed during run")
        receipt["status"] = "PASS_WITHIN_PROVIDER_SCOPE"
    except Exception as error:
        receipt["status"] = "FAIL"
        receipt["error"] = str(error)
    receipt["artifact_sha256"] = {str(path.relative_to(out)): sha(path) for path in sorted(out.rglob("*")) if path.is_file()}
    with (out / "receipt.json").open("x", encoding="utf8") as handle:
        json.dump(receipt, handle, indent=2)
        handle.write("\n")
    print(json.dumps({"status": receipt["status"], "normal": receipt.get("normal"), "sanitized": receipt.get("sanitized"), "mutations": len(receipt.get("mutation_controls", [])), "out": str(out)}))
    if receipt["status"] == "FAIL":
        print(receipt["error"], file=sys.stderr)
        raise SystemExit(1)

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    main(parser.parse_args().out.resolve())
