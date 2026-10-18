"""Run actual LinuxCNC HAL functions in an isolated disconnected namespace."""
import argparse
import json
import subprocess
import time
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument("--module", required=True)
parser.add_argument("--case", choices=["qualification", "crc", "encoder", "mpg", "IS1", "denied"], required=True)
args = parser.parse_args()
checks = 0

def assert_that(value, message):
    global checks
    checks += 1
    if not value:
        raise AssertionError(message)

def cmd(*words, check=True):
    result = subprocess.run(["halcmd", *map(str, words)], capture_output=True, text=True)
    if check and result.returncode:
        raise RuntimeError(f"halcmd {words}: {result.stdout} {result.stderr}")
    return result

def value(name):
    result = cmd("getp", "cnc3a." + name).stdout.strip()
    if result.upper() in ("TRUE", "FALSE"):
        return result.upper() == "TRUE"
    return float(result) if "." in result or "e" in result.lower() else int(result, 0)

def wait_for(predicate, message, timeout=75):
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        if predicate():
            return
        time.sleep(.025)
    raise AssertionError(message)

def snapshot():
    scalars = ["state", "fault-code", "fault", "discovered", "feedback-valid", "supported-channels",
               "installed-channels", "supported-encoders", "installed-encoders", "spi-transactions",
               "cap3-frames", "arm-frames", "update-frames", "configure-frames", "rtl-enabled-mask",
               "rtl-armed-mask", "rtl-session", "rtl-authority", "malformed-transactions", "host-cycles"]
    data = {name: value(name) for name in scalars}
    data["command"] = [value(f"{i}.position-cmd") for i in range(12)]
    data["feedback"] = [value(f"{i}.position-fb") for i in range(12)]
    data["step_rises"] = [value(f"{i}.observed-step-rises") for i in range(12)]
    data["encoders"] = [value(f"encoder.{i}.count") for i in range(4)]
    return data

def inhibited(data):
    for name in ["discovered", "feedback-valid", "arm-frames", "update-frames", "configure-frames",
                 "rtl-enabled-mask", "rtl-armed-mask", "rtl-session", "rtl-authority", "malformed-transactions"]:
        assert_that(not data[name], f"{name} remains zero/false")
    assert_that(data["step_rises"] == [0] * 12, "all twelve independent pin monitors observe no STEP rise")

observations = []
try:
    cmd("loadrt", "threads", "name1=servo-thread", "period1=1000000", "fp1=1")
    if args.case == "denied":
        result = cmd("loadrt", args.module, check=False)
        assert_that(result.returncode != 0, "simulation module refuses without explicit opt-in")
        listing = cmd("list", "pin", "cnc3a.*").stdout.strip()
        assert_that(not listing, "denied module exports no HAL pins")
    else:
        scenario = {"encoder": 1, "mpg": 2}.get(args.case, 0)
        cmd("loadrt", args.module, f"scenario={scenario}")
        listing = cmd("list", "pin", "cnc3a.*").stdout.split()
        assert_that(len([p for p in listing if p.endswith("position-cmd")]) == 12, "twelve HAL command inputs exported")
        assert_that(len([p for p in listing if p.endswith("position-fb")]) == 12, "twelve HAL feedback outputs exported")
        assert_that(len([p for p in listing if p.startswith("cnc3a.encoder.")]) == 4, "four HAL encoder count outputs exported")
        for i in range(12):
            cmd("setp", f"cnc3a.{i}.position-cmd", (i + 1) * .125)
        cmd("setp", "cnc3a.enable", "TRUE")
        cmd("setp", "cnc3a.reset", "TRUE")
        if args.case == "crc":
            cmd("setp", "cnc3a.sim-corrupt-crc", "TRUE")
        cmd("addf", "cnc3a.read", "servo-thread")
        cmd("addf", "cnc3a.write", "servo-thread")
        cmd("start")
        wait_for(lambda: value("state") == 10, "actual driver reaches a latched refusal")
        first = snapshot(); observations.append(first)
        inhibited(first)
        assert_that(first["command"] == [(i + 1) * .125 for i in range(12)], "all twelve HAL command values are present during refusal")
        assert_that(first["host-cycles"] > 0, "actual compiled HAL read function was scheduled")
        expected = {"qualification": (11, 128, 64), "crc": (2, 1, 0), "encoder": (10, 0, 0), "mpg": (10, 0, 0), "IS1": (3, 2, 1)}[args.case]
        assert_that((first["fault-code"], first["spi-transactions"], first["cap3-frames"]) == expected,
                    f"expected actual C-driver fault/serial-transfer/CAP3 counts {expected}")
        if args.case == "qualification":
            assert_that((first["supported-channels"], first["installed-channels"], first["supported-encoders"], first["installed-encoders"]) == (12, 0, 4, 0), "actual serial capability support remains distinct from qualified inventory")
            # Holding reset while enable is asserted never rediscovers or arms.
            cycles = first["host-cycles"]
            wait_for(lambda: value("host-cycles") >= cycles + 4, "callbacks continue after fault")
            held = snapshot(); observations.append(held); inhibited(held)
            assert_that(held["spi-transactions"] == 128, "held reset plus enable cannot bypass qualification")
            # A stopped reset is permitted to rediscover, but still cannot arm.
            cmd("setp", "cnc3a.enable", "FALSE");cmd("setp", "cnc3a.reset", "FALSE")
            cycles = value("host-cycles")
            wait_for(lambda: value("host-cycles") >= cycles + 2, "reset edge cleared")
            cmd("setp", "cnc3a.reset", "TRUE")
            wait_for(lambda: value("spi-transactions") > 128, "stopped reset starts fresh actual discovery")
            cmd("setp", "cnc3a.reset", "FALSE")
            wait_for(lambda: value("state") == 10 and value("spi-transactions") == 256, "repeat incomplete qualification is refused")
            stopped = snapshot();observations.append(stopped);inhibited(stopped)
            assert_that(stopped["fault-code"] == 11 and stopped["cap3-frames"] == 128, "rediscovery has a bounded second refusal")
            # A later enable edge cannot restore unqualified authority.
            cmd("setp", "cnc3a.enable", "TRUE")
            cycles = value("host-cycles")
            wait_for(lambda: value("host-cycles") >= cycles + 4, "post-refusal enable edge observed")
            after = snapshot();observations.append(after);inhibited(after)
            assert_that(after["spi-transactions"] == 256 and after["fault-code"] == 11, "enable edge does not send ARM after refusal")
    result = {"status": "PASS", "case": args.case, "checks": checks,
              "actual_LinuxCNC_HAL_scheduler": args.case != "denied",
              "actual_motion_controller_trajectory": False,
              "HAL_command_pins": 0 if args.case == "denied" else 12,
              "HAL_feedback_pins": 0 if args.case == "denied" else 12,
              "HAL_encoder_pins": 0 if args.case == "denied" else 4,
              "actual_CNC3_serial_SPI_RTL": args.case in ("qualification", "crc", "IS1"),
              "snapshots": observations, "full_requested_milestone_complete": False}
    Path(f"observation-{args.case}.json").write_text(json.dumps(result, indent=2) + "\n")
    print(json.dumps({k: v for k, v in result.items() if k != "snapshots"}))
finally:
    cmd("stop", check=False)
    cmd("unloadrt", "all", check=False)
