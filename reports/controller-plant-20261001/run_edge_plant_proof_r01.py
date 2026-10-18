"""Compile the disconnected actual-edge plant and test real compiled mutations.

This does not exercise an FPGA, LinuxCNC, or a physical driver. It proves only
the deterministic ideal-mechanics fixture to which those layers can connect.
"""
from pathlib import Path
import argparse
import hashlib
import json
import re
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
INPUTS = HERE / "stage-r01"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def unix(p):
    p = p.resolve()
    return "/mnt/" + p.drive[0].lower() + p.as_posix()[2:]


def write(p, data):
    p.write_text(json.dumps(data, indent=2) + "\n", encoding="utf8")


# Each mutation must compile, execute, and be rejected by an independent
# physical-position/edge/sensor expectation, not merely a static source scan.
MUTATIONS = (
    ("level_instead_of_edge", "uint16_t rises=pin.step&~previous_step_;",
     "uint16_t rises=pin.step;", "high level not extra rising edge"),
    ("missing_permission", "drive.valid&&drive.tx_permit?uint16_t", "drive.valid?uint16_t",
     "inhibit detects emitted rising edges"),
    ("missing_provider", "drive.valid&&drive.tx_permit?uint16_t", "drive.tx_permit?uint16_t",
     "no trusted permission means no physical movement"),
    ("ignore_drive_enable", "(~drive.enable_n)&drive.powered&all_joints", "drive.powered&all_joints",
     "individual drive and power gating"),
    ("invent_lost_motion", "if(lost)++st.lost_steps;", "if(lost && false)++st.lost_steps;",
     "missed steps visible in physical position"),
    ("ignore_reversal", "if(faults_.reverse_motor&bit)sign=-sign;",
     "if((faults_.reverse_motor&bit) && false)sign=-sign;", "reversed motor"),
    ("ignore_backlash", "st.position=st.motor_coordinate-j.backlash/2;",
     "st.position=st.motor_coordinate;", "initial half gap explicit"),
    ("fake_encoder_feedback", "s.encoder_backlog[i]=target-encoder_position_[i];",
     "s.encoder_backlog[i]=0;", "encoder waveform debt explicitly exposed"),
    ("ignore_encoder_unplug", "!(faults_.encoder_unplugged&(1u<<i))",
     "(!(faults_.encoder_unplugged&(1u<<i)) || true)", "encoder unplugged explicit"),
    ("ignore_missing_cycles", "started_&&cycle!=last_cycle_+1",
     "started_&&cycle!=last_cycle_+1&&false", "missing core cycles rejected"),
    ("ignore_sensor_power", "s.sensors_valid=drive.valid&&drive.sensor_supply;",
     "s.sensors_valid=drive.valid;", "unpowered feedback unavailable"),
    ("ignore_index_width", "modulus(signed_position,e.edges_per_output_rev)<e.index_width_edges",
     "modulus(signed_position,e.edges_per_output_rev)<=e.index_width_edges", "index follows actual encoder phase"),
)


def main(out, distro):
    out = out.resolve()
    if not out.is_relative_to(ROOT / "reports") or out.exists():
        raise ValueError("Use a fresh report directory inside this workspace")
    out.mkdir(parents=True)
    inputs = [INPUTS / "edge_plant.hpp", INPUTS / "test_edge_plant.cpp", Path(__file__)]
    before = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    cases = []

    def run(argv, folder, name, timeout=120):
        start = time.monotonic()
        p = subprocess.run(argv, capture_output=True, timeout=timeout)
        log = folder / (name + ".log")
        log.write_bytes(p.stdout + p.stderr)
        data = {"argv": argv, "exit_code": p.returncode,
                "log": str(log.relative_to(out)), "log_sha256": sha(log),
                "seconds": time.monotonic() - start}
        write(folder / (name + ".json"), data)
        return data, (p.stdout + p.stderr).decode("utf8", errors="replace")

    version, version_log = run(["wsl", "-d", distro, "--", "clang++", "--version"], out, "compiler")
    if version["exit_code"]:
        write(out / "receipt.json", {"status": "BLOCKED", "compiler": version,
                                      "physical_qualified": False, "manufacturing_ready": False})
        return 2
    source = inputs[0].read_text(encoding="utf8")
    failures = []
    plan = [("baseline", None, None, None), *MUTATIONS]
    for name, old, replacement, expected_failure in plan:
        folder = out / name
        folder.mkdir()
        text = source
        if old is not None:
            if text.count(old) != 1:
                raise ValueError(f"Mutation requires exactly one site: {name}")
            text = text.replace(old, replacement)
        header = folder / "edge_plant.hpp"
        header.write_text(text, encoding="utf8", newline="\n")
        shutil.copyfile(inputs[1], folder / "test_edge_plant.cpp")
        executable = folder / "edge_plant_test"
        compile_run, compile_log = run(["wsl", "-d", distro, "--", "clang++", "-std=c++17",
            "-Wall", "-Wextra", "-Werror", "-O2", unix(folder / "test_edge_plant.cpp"),
            "-o", unix(executable)], folder, "compile")
        execution = None
        runtime_log = ""
        if compile_run["exit_code"] == 0:
            execution, runtime_log = run(["wsl", "-d", distro, "--", unix(executable)], folder, "execute")
        if expected_failure is None:
            match = re.search(r"EDGE_PLANT_PASS checks=(\d+) joints=12 encoders=4 actual_FPGA_integration=0 physical_qualification=0", runtime_log)
            accepted = bool(execution and execution["exit_code"] == 0 and match and int(match[1]) >= 1114)
        else:
            accepted = bool(execution and execution["exit_code"] == 1 and
                            "EDGE_PLANT_FAIL " + expected_failure in runtime_log)
        result = {"name": name, "passed": accepted, "header_sha256": sha(header),
                  "test_sha256": sha(folder / "test_edge_plant.cpp"),
                  "compile": compile_run, "execute": execution,
                  "expected_runtime_failure": expected_failure,
                  "output": runtime_log.strip()}
        cases.append(result)
        if not accepted:
            failures.append(name)
    unchanged = before == {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    receipt = {"status": "PASS" if not failures and unchanged else "FAIL",
               "evidence_type": "COMPILED_DISCONNECTED_IDEAL_MECHANICS_FIXTURE",
               "input_sha256": before, "source_unchanged": unchanged,
               "compiler": version_log.strip(), "cases": cases, "failures": failures,
               "baseline_checks": 1114, "compiled_negative_controls": len(MUTATIONS),
               "actual_FPGA_integration": False, "actual_LinuxCNC_integration": False,
               "complete_nine_machine_suite": False, "physical_qualified": False,
               "manufacturing_ready": False,
               "scope": "12 emitted STEP/DIR edges to ideal travel/backlash/hard stops; 4 Gray ABZ sources; explicit external physical permission/power provider; deterministic faults",
               "missing": ["torque/inertia and acceleration capability", "receiver/cable electrical model",
                           "actual FPGA/HAL/LinuxCNC integration", "full safety and IOL1 providers",
                           "spindle/frequency and complete 9 kinematics fixtures", "physical validation"]}
    write(out / "receipt.json", receipt)
    print(json.dumps({"status": receipt["status"], "checks": 1114,
                      "compiled_negative_controls": len(MUTATIONS), "failures": failures}))
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--wsl-distro", default="GarciaMechBuilder")
    args = ap.parse_args()
    raise SystemExit(main(args.out, args.wsl_distro))
