"""Actual Efinix-family synthesis of the bounded CNC3 structural endpoint.

This is a family mapping check, not a vendor package fit or timing proof.
The existing isolated Debian lab rootfs supplies the real Yosys executable.
"""
from pathlib import Path
import argparse
import hashlib
import json
import shutil
import subprocess
import uuid

BASE = Path(__file__).resolve().parents[1]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def unix(path):
    if not path.drive:
        raise ValueError("This Windows lab runner requires an absolute drive path")
    return "/mnt/" + path.drive[0].lower() + path.as_posix()[2:]


def main(out):
    out = out.resolve()
    if out.exists():
        raise RuntimeError("Fresh synthesis evidence directory required")
    out.mkdir(parents=True)
    sources = sorted((BASE / "rtl").glob("*.v"))
    if len(sources) != 5:
        raise RuntimeError("Expected the exact five structural CNC3 RTL sources")
    before = {f.relative_to(BASE).as_posix(): sha(f) for f in sources}
    snapshots = out / "inputs" / "rtl"
    snapshots.mkdir(parents=True)
    for source in sources:
        shutil.copyfile(source, snapshots / source.name)
    work = "cnc3-transport-" + uuid.uuid4().hex[:12]
    script = f'''#!/bin/sh
set -eu
cd '{unix(out)}'
rootfs=/root/.cache/controller-lab-linuxcnc/rootfs
mkdir "$rootfs/work/{work}"
cp inputs/rtl/*.v "$rootfs/work/{work}/"
cp synth.ys "$rootfs/work/{work}/"
set +e
unshare --mount --propagation private --pid --fork --kill-child sh -c 'mount -t proc proc /root/.cache/controller-lab-linuxcnc/rootfs/proc; chroot /root/.cache/controller-lab-linuxcnc/rootfs sh -c "cd /work/{work}; yosys -V > yosys-version.txt; yosys -Q -T -s synth.ys > synthesis.log 2>&1"'
result=$?
set -e
cp "$rootfs/work/{work}/"*.json "$rootfs/work/{work}/"*.log "$rootfs/work/{work}/"*.txt .
test "$result" -eq 0
'''
    (out / "run.sh").write_text(script, encoding="utf8", newline="\n")
    (out / "synth.ys").write_text('''read_verilog cnc3_command_validate.v cnc3_spi_transport.v cnc3_frame_endpoint.v cnc3_feedback_pack.v cnc3_status_pack.v
hierarchy -check -top cnc3_frame_endpoint
proc
check -assert
select -assert-none t:$dlatch t:$adlatch t:$dlatchsr
tee -o structural-stat.json stat -json
synth_efinix -top cnc3_frame_endpoint
delete t:$scopeinfo
check -assert -mapped
select -assert-none t:EFX_LATCH t:$_DLATCH_* t:$dlatch t:$adlatch t:$dlatchsr
tee -o mapped-stat.json stat -json
write_json cnc3_frame_endpoint_efinix.json
''', encoding="utf8", newline="\n")
    result = subprocess.run(
        ["wsl", "-d", "GarciaMechBuilder", "--", "sh", unix(out / "run.sh")],
        text=True, capture_output=True, encoding="utf8", errors="replace", timeout=300,
    )
    (out / "command.log").write_text(result.stdout + result.stderr, encoding="utf8")
    unchanged = all(sha(BASE / f) == digest for f, digest in before.items())
    expected = ["structural-stat.json", "mapped-stat.json", "cnc3_frame_endpoint_efinix.json", "synthesis.log", "yosys-version.txt"]
    outputs_present = all((out / f).is_file() for f in expected)
    receipt = {
        "status": "PASS" if result.returncode == 0 and unchanged and outputs_present else "FAIL",
        "source_hashes": before,
        "source_unchanged": unchanged,
        "required_outputs_present": outputs_present,
        "family_synthesis_only": True,
        "Efinity_fit_timing": False,
        "clock_frequency_qualified": False,
        "compiler_result": result.returncode,
        "outputs": {f.relative_to(out).as_posix(): sha(f) for f in out.rglob("*") if f.is_file()},
    }
    (out / "receipt.json").write_text(json.dumps(receipt, indent=2) + "\n", encoding="utf8")
    print(json.dumps(receipt))
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--out", type=Path, required=True)
    args = parser.parse_args()
    raise SystemExit(main(args.out))
