"""Actual Verilated CNC3 SPI to actual STEP/DIR pins to disconnected mechanics.

No behavioral FPGA substitution, spidev, hardware, or machine configuration.
Explicit ideal permission providers do not qualify the real electrical chain.
"""
from pathlib import Path
import argparse
import hashlib
import importlib.util
import json
import shutil
import subprocess
import time

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
STAGE = HERE / "stage-r01"
RTL_FILES = ("cnc3_alarm_filter.v", "cnc3_encoder_runtime.v", "cnc3_motion_spi.v",
             "cnc3_motion_state.v", "cnc3_spi_transport_stateful.v", "cnc3_stepgen_runtime.v",
             "cnc3_command_validate.v", "cnc3_rate_admission_serial.v")
SCENARIOS = ("clean", "missed_steps", "watchdog", "encoder_unplug", "permission_drop", "drive_alarm",
             "field_power_loss", "provider_missing", "sensor_power_loss")


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def unix(p):
    p = p.resolve()
    return "/mnt/" + p.drive[0].lower() + p.as_posix()[2:]


def write(p, v):
    def bytes_only(value):
        if isinstance(value, bytes):
            return {"encoding": "hex", "bytes": value.hex()}
        raise TypeError(type(value).__name__ + " is not report serializable")
    p.write_text(json.dumps(v, indent=2, default=bytes_only) + "\n", encoding="utf8")


def main(out, rtl_dir, distro):
    out = out.resolve()
    rtl_dir = rtl_dir.resolve()
    if not out.is_relative_to(ROOT / "reports") or out.exists():
        raise ValueError("Fresh workspace report directory required")
    out.mkdir(parents=True)
    inputs = [rtl_dir / name for name in RTL_FILES]
    inputs += [STAGE / "edge_plant.hpp", STAGE / "spi_edge_plant.cpp", Path(__file__),
               ROOT / "gateware/v3/frozen/protocol_v3.py", ROOT / "gateware/v3/frozen/spec/protocol.json"]
    before = {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    write(out / "input-sha256.json", before)
    copied = out / "inputs"
    copied.mkdir()
    for path in inputs:
        shutil.copyfile(path, copied / path.name)
    codec_spec = importlib.util.spec_from_file_location("frozen_cnc3_codec", copied / "protocol_v3.py")
    codec = importlib.util.module_from_spec(codec_spec)
    codec_spec.loader.exec_module(codec)
    codec._SPEC = codec.Spec(str(copied / "protocol.json"))
    frames = {"configure": (True, codec.encode_configure(expected_module_class=1,
                      required_mask=0xfff, alarm_trip_mask=0xfff, encoder_filter_ticks=4, required_encoder_mask=15)),
              "sync": (False, codec.encode_command(1, session=0x11223344)[1]),
              "test_m": (False, codec.encode_command(13, session=0x11223344, sequence=1, fields={"rate_0": 0x01000000})[1]),
              "test_o": (False, codec.encode_command(13, session=0x11223344, sequence=2, fields={"rate_0": 0x02000000})[1]),
              "clear": (False, codec.encode_command(14, session=0x11223344, sequence=3, channel_mask=0xfff)[1]),
              "arm": (False, codec.encode_command(2, session=0x11223344, sequence=4, channel_mask=0xfff)[1]),
              "disarm": (False, codec.encode_command(4, session=0x11223344, sequence=17)[1]),
              "read": (True, codec.encode_fb_read())}
    for i in range(12):
        # Rates vary independently with a zero segment and complete reversal;
        # these are simulation inputs, not qualified motor speed ratings.
        rates = [0 if i in (4, 8) else (1 if (k % 2 == 0) == (i < 6) else -1) * (0x200000 + k * 0x70000 + i * 0x8000)
                 for k in range(12)]
        frames["update_" + str(i)] = (False, codec.encode_update(session=0x11223344,
                                          sequence=5 + i, rates=rates, channel_mask=0xfff))
    header = ["#pragma once", "#include <vector>", "#include <cstdint>",
              "struct Frame {bool feedback;std::vector<uint8_t> bytes;};", "namespace frames {"]
    for name, (fb, data) in frames.items():
        header.append("inline const Frame " + name + "{" + str(fb).lower() + ",{"
                      + ",".join(str(x) for x in data) + "}};")
    header.append("inline const std::vector<Frame> updates{" + ",".join("update_" + str(i) for i in range(12)) + "};\n}")
    (copied / "frames.hpp").write_text("\n".join(header) + "\n", encoding="utf8", newline="\n")
    write(out / "command-frames.json", {k: {"CS": "CS_FB" if f else "CS_CMD", "hex": b.hex()} for k, (f, b) in frames.items()})
    executions = []

    def run(argv, folder, name, timeout=600):
        started = time.monotonic()
        result = subprocess.run(argv, capture_output=True, timeout=timeout)
        log = folder / (name + ".log")
        log.write_bytes(result.stdout + result.stderr)
        record = {"argv": argv, "exit_code": result.returncode, "log": str(log.relative_to(out)),
                  "log_sha256": sha(log), "seconds": time.monotonic() - started}
        write(folder / (name + ".json"), record)
        executions.append(record)
        return result.returncode, (result.stdout + result.stderr).decode("utf8", errors="replace")

    status, failure, cases = "FAIL", None, []
    try:
        obj = out / "obj"
        code, log = run(["wsl", "-d", distro, "--", "verilator", "--cc", "--compiler", "clang",
                         "--top-module", "cnc3_motion_spi", "--Mdir", unix(obj), "-Wall", "-Wno-fatal",
                         *[unix(copied / name) for name in RTL_FILES]], out, "verilate")
        if code:
            raise RuntimeError("Actual Verilator source translation failed; see verilate.log")
        # Link the generated source directly. This uses the actual Verilator
        # runtime and C++ compiler without modifying the host build toolchain.
        generated = sorted(obj.glob("*.cpp"))
        if not generated:
            raise RuntimeError("Verilator emitted no actual model source")
        executable = out / "spi_edge_plant"
        code, log = run(["wsl", "-d", distro, "--", "clang++", "-std=c++17", "-O1", "-pthread",
                         "-I/usr/share/verilator/include", "-I/usr/share/verilator/include/vltstd",
                         "-I" + unix(obj), "-I" + unix(copied), unix(copied / "spi_edge_plant.cpp"),
                         *[unix(q) for q in generated], "/usr/share/verilator/include/verilated.cpp",
                         "/usr/share/verilator/include/verilated_threads.cpp", "-o", unix(executable)], out, "compile", 900)
        if code:
            raise RuntimeError("Actual generated model compilation failed; see compile.log")
        for scenario in SCENARIOS:
            folder = out / scenario
            folder.mkdir()
            code, log = run(["wsl", "-d", distro, "--cd", unix(folder), "--", unix(executable), scenario], folder, "execute", 600)
            if code or f"ACTUAL_SPI_EDGE_PLANT_PASS scenario={scenario}" not in log:
                raise RuntimeError(scenario + " actual RTL/plant test failed: " + log[-2000:])
            state = json.loads((folder / "state.json").read_text())
            decoded = {}
            for line in (folder / "responses.txt").read_text().splitlines():
                label, n, hex_bytes = line.split()
                b = bytes.fromhex(hex_bytes)
                if len(b) != int(n):
                    raise RuntimeError("Actual response byte count mismatch")
                decoded[label] = codec.decode_response("CS_FB" if len(b) == 176 else "CS_CMD", b)
            write(folder / "decoded-responses.json", decoded)
            fb = decoded["stopped_feedback"]
            assertions = {
                "actual_stopped_outputs": fb["armed_mask"] == 0,
                "all_twelve_pin_counts": all(fb[f"step_count_{i}"] == (state["joints"][i]["pin_signed_steps"] & 0xffffff) for i in range(12)),
                "actual_encoder_waveform_drained": state["encoder_backlog"] == [0] * 4,
                "actual_digital_analog_sources_unavailable": fb["din_age"] == 255 and fb["ain_age"] == 255 and fb["ain_status"] == 0,
            }
            if scenario in ("clean", "missed_steps"):
                assertions["four_actual_position_encoders"] = all(
                    fb[f"encoder_count_{i}"] == (round((state["joints"][i]["position"] - 50) * 40) & 0xffffff)
                    for i in range(4))
                assertions["continuity_preserved_after_clean_stop"] = fb["pos_continuity"] == 0xfff
            else:
                assertions["fault_continuity_invalid"] = fb["pos_continuity"] == 0 and fb["fault_word"] != 0
            if scenario == "missed_steps":
                assertions["physical_encoder_differs_from_step_command"] = fb["encoder_count_0"] != fb["step_count_0"]
            cases.append({"scenario": scenario, "passed": all(assertions.values()), "checks": assertions,
                          "state_sha256": sha(folder / "state.json"), "responses_sha256": sha(folder / "responses.txt"),
                          "fixture_assertions": state["checks"]})
            if not all(assertions.values()):
                raise RuntimeError(scenario + " independent actual response reconciliation failed")
        status = "PASS"
    except Exception as exc:
        failure = f"{type(exc).__name__}: {exc}"
    unchanged = before == {str(p.relative_to(ROOT)): sha(p) for p in inputs}
    if not unchanged:
        status, failure = "FAIL", "Actual input source changed during run"
    receipt = {"status": status, "failure": failure, "input_sha256": before, "source_unchanged": unchanged,
               "command_frames_sha256": sha(out / "command-frames.json"), "cases": cases, "executions": executions,
               "actual_FPGA_integration": True, "actual_LinuxCNC_integration": False,
               "behavioral_FPGA_substitution": False, "physical_qualified": False, "manufacturing_ready": False,
               "complete_nine_machine_suite": False, "complete_safety_chain": False,
               "scope": "Actual Verilated CNC3 serial transport/state/12 DDS/4 encoder RTL; emitted pins drive disconnected ideal mechanics; real serial feedback decoded independently",
               "gaps": ["actual CNC3 HAL and LinuxCNC", "selected-part physical power/permission/watchdog circuits",
                        "IOL1 and complete output authority", "home/limit/probe computed but not yet connected to actual RTL event acquisition",
                        "inertia/torque/acceleration capability", "complete nine machine kinematics/UI", "vendor fit/static timing and physical measurements"]}
    write(out / "receipt.json", receipt)
    print(json.dumps({"status": status, "failure": failure, "completed_scenarios": len(cases)}))
    return 0 if status == "PASS" else 1


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--rtl-dir", required=True, type=Path)
    ap.add_argument("--wsl-distro", default="GarciaMechBuilder")
    a = ap.parse_args()
    raise SystemExit(main(a.out, a.rtl_dir, a.wsl_distro))
