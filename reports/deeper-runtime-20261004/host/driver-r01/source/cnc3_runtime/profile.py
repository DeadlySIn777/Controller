"""Generate an isolated LinuxCNC FREE-joint qualification profile from review.

All joints are authored linear millimetre simulation coordinates. The nine-axis
trivkins mapping exists to load LinuxCNC's real motion/task stack; it is not an
inference of the customer's machine kinematics or a homing/commissioning claim.
"""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from controller_config.service import read_json
from controller_config.setup_service import SetupService
from controller_lab.cnc3_configuration import verify_configuration
from tools.create_cnc3_qualification_fixture import runtime_sources


def create_profile(manifest_path, store_path, module, output, observation):
    manifest_path, store_path = Path(manifest_path).resolve(), Path(store_path).resolve()
    manifest = verify_configuration(read_json(manifest_path), SetupService(store_path),
        source_root=ROOT, expected_source_files=runtime_sources())
    host = manifest["cnc3_host"]
    count = {0x00FF: 8, 0x0FFF: 12}.get(host["active_mask"])
    if count is None or host["fitted_mask"] != 0x0FFF:
        raise ValueError("This qualification profile requires contiguous 8 or 12 active joints, with all 12 fitted in the model")
    if not re.fullmatch(r"[a-zA-Z][a-zA-Z0-9_]{0,39}", module):
        raise ValueError("Unsafe temporary RTAPI module name")
    output, observation = Path(output).resolve(), Path(observation).resolve()
    script = Path(__file__).with_name("integration.py").resolve()
    # LinuxCNC DISPLAY's command parser does not provide a portable quoting
    # contract. Copied isolated workspaces use simple absolute POSIX paths.
    if os.name != "posix" or any(" " in str(path) or "\n" in str(path) for path in (script, manifest_path, observation)):
        raise ValueError("Generate this profile inside the isolated LinuxCNC POSIX workspace")
    output.mkdir(parents=True, exist_ok=False)
    coordinates = "XYZABCUVWXYZ"[:count]
    ini = ["[EMC]", "VERSION = 1.1", f"MACHINE = Disconnected CNC3 SIM2 {count} linear joints", "DEBUG = 0",
           "", "[DISPLAY]", f"DISPLAY = /usr/bin/python3 {script} --manifest {manifest_path} --output {observation}",
           "POSITION_OFFSET = MACHINE", "POSITION_FEEDBACK = ACTUAL", "", "[TASK]", "TASK = milltask", "CYCLE_TIME = 0.005",
           "", "[RS274NGC]", f"PARAMETER_FILE = {output / 'sim2.var'}", "", "[EMCMOT]", "EMCMOT = motmod",
           "COMM_TIMEOUT = 1.0", "SERVO_PERIOD = 1000000", "", "[EMCIO]", "EMCIO = io", "CYCLE_TIME = 0.010",
           "", "[KINS]", f"JOINTS = {count}", f"KINEMATICS = trivkins coordinates={coordinates} kinstype=BOTH",
           "", "[TRAJ]", f"COORDINATES = {''.join(dict.fromkeys(coordinates))}", "LINEAR_UNITS = mm", "ANGULAR_UNITS = degree",
           "NO_FORCE_HOMING = 0", "DEFAULT_LINEAR_VELOCITY = 1.0", f"MAX_LINEAR_VELOCITY = {min(host['max_velocity'][:count]):.17g}",
           "", "[HAL]", "HALFILE = sim2.hal", ""]
    for axis in dict.fromkeys(coordinates):
        indices = [index for index, coordinate in enumerate(coordinates) if coordinate == axis]
        velocity = min(host["max_velocity"][index] for index in indices)
        ini.extend([f"[AXIS_{axis}]", "MIN_LIMIT = -1000", "MAX_LIMIT = 1000",
                    f"MAX_VELOCITY = {velocity:.17g}", "MAX_ACCELERATION = 40", ""])
    for channel in range(count):
        ini.extend([f"[JOINT_{channel}]", "TYPE = LINEAR", "MIN_LIMIT = -1000", "MAX_LIMIT = 1000",
                    f"MAX_VELOCITY = {host['max_velocity'][channel]:.17g}", "MAX_ACCELERATION = 40",
                    "FERROR = 1.0", "MIN_FERROR = 0.05", "HOME = 0", "HOME_OFFSET = 0", ""])
    hal = ["loadrt [KINS]KINEMATICS",
           "loadrt [EMCMOT]EMCMOT servo_period_nsec=[EMCMOT]SERVO_PERIOD num_joints=[KINS]JOINTS",
           f"loadrt {module}", "addf cnc3r.read servo-thread", "addf motion-command-handler servo-thread",
           "addf motion-controller servo-thread", "addf cnc3r.write servo-thread",
           "# Authored disconnected e-stop loopback; real permission remains model-owned.",
           "net sim-task-estop iocontrol.0.user-enable-out => iocontrol.0.emc-enable-in",
           "net sim-motion-enabled motion.motion-enabled => cnc3r.enable",
           "net sim-runtime-fault cnc3r.fault"]
    for channel in range(count):
        hal.extend([f"net sim-j{channel}-command joint.{channel}.motor-pos-cmd => cnc3r.{channel}.position-cmd",
                    f"net sim-j{channel}-feedback cnc3r.{channel}.position-fb => joint.{channel}.motor-pos-fb",
                    f"net sim-runtime-fault => joint.{channel}.amp-fault-in"])
    with (output / "sim2.ini").open("x", encoding="utf-8") as handle:
        handle.write("\n".join(ini) + "\n")
    with (output / "sim2.hal").open("x", encoding="utf-8") as handle:
        handle.write("\n".join(hal) + "\n")
    metadata = {"schema_version": 1, "kind": "authored_linuxcnc_free_joint_profile",
        "manifest_sha256": manifest["manifest_sha256"], "motor_joints": count, "fitted_channels": 12,
        "coordinates_for_loading_only": coordinates, "all_joints_linear_mm": True,
        "derived_maximum_velocity": host["max_velocity"], "authored_acceleration_mm_s2": 40,
        "single_command_writer": "actual LinuxCNC motion controller",
        "single_enable_writer": "motion.motion-enabled", "physical_backend_allowed": False,
        "physical_homing_measured": False, "physical_authority": False}
    with (output / "profile.json").open("x", encoding="utf-8") as handle:
        json.dump(metadata, handle, indent=2)
        handle.write("\n")
    return output / "sim2.ini"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--store", required=True)
    parser.add_argument("--module", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--observation", required=True)
    args = parser.parse_args()
    print(create_profile(args.manifest, args.store, args.module, args.output, args.observation))


if __name__ == "__main__":
    main()
