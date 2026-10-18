"""Disconnected pre-hardware bench; never turns a model into hardware evidence.

Run ``python tools/validate_controller.py --full`` or ``--inventory``.  Every
run writes a fresh reports directory.  No source generator, flash tool, spidev,
machine connection, fabricated manufacturing export or vendor download runs.
"""
from __future__ import annotations

import argparse
from collections import Counter
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time
import unittest

ROOT = Path(__file__).resolve().parents[1]
STATUSES = {"PASS", "FAIL", "BLOCKED", "NOT_RUN"}
SCOPES = ("tools", "tests", "controller_config", "controller_backend",
          "controller_lab", "firmware", "gateware", "cnc1", "config", "hardware", "research", "schemas")
SKIP = {"__pycache__", ".git", "node_modules", "vendor-src", "build", "dist",
        "build-default", "build-uart", "build-uart-check"}
EXTENSIONS = {".py", ".sh", ".c", ".cpp", ".h", ".v", ".sv", ".ys", ".json",
              ".ini", ".hal", ".xml", ".csv", ".kicad_sch", ".kicad_mod",
              ".kicad_pcb", ".kicad_pro", ".kicad_dru", ".kicad_sym", ".hpp",
              ".toml", ".yaml", ".yml", ".cfg", ".md", ".txt", ".ps1",
              ".hex", ".edif", ".defaults", ".s", ".ld", ".in"}
SPECIAL_NAMES = {"CMakeLists.txt", "Kconfig.projbuild", "sdkconfig", "fp-lib-table", "sym-lib-table", "SHA256SUMS"}
CONTEXT = {}
KICAD = Path("C:/Program Files/KiCad/10.0/bin")
EXTERNAL = Path("C:/Users/Gluis/claude-worktrees/controller-interface-spec")
LAB_ROOTFS = "/root/.cache/controller-lab-linuxcnc/rootfs"
PARTIAL_RTL_RUNNERS = (
    ("isolated_stepgen12_dynamic", "ACTUAL_RTL_DYNAMIC_COMPONENT_TEST",
     "reports/pre-hardware-characterization-20261001/run_dynamic12_r02.py",
     "reports/pre-hardware-characterization-20261001/tb_stepgen12_dynamic_r01.sv"),
    ("isolated_encoder4_sweep", "ACTUAL_RTL_IDEAL_DIGITAL_COMPONENT_SWEEP",
     "reports/pre-hardware-characterization-20261001/run_encoder4_limits_r01.py",
     "reports/pre-hardware-characterization-20261001/tb_encoder4_limits_r01.sv"),
)
ANALOG_BASE = "reports/pre-hardware-characterization-20261001/"
PARTIAL_SPICE_RUNNERS = (
    ("analog_passive_filter_corners", "ACTUAL_NATIVE_BOUND_PASSIVE_FILTER_SPICE",
     ANALOG_BASE + "run_AI_passive_SPICE_r02.py", 96),
    ("analog_active_buffer_corners", "NATIVE_BOUND_MANUFACTURER_BUFFER_MACROMODEL_SPICE",
     ANALOG_BASE + "run_AI_buffer_SPICE_r03.py", 12),
)
SPICE_INPUTS = (
    ANALOG_BASE + "AI-passive-manufacturer-sources-r01/murata-GRM1885C1H222JA01.pdf",
    ANALOG_BASE + "AI-passive-manufacturer-sources-r01/vishay-CRCW-20035.pdf",
    ANALOG_BASE + "AI-active-model-discovery-r01/SBOMA34/OPAx197.LIB",
    ANALOG_BASE + "INA149-active-model-discovery-r01/SBOMC47/ina149.lib",
)
PLANT_INPUTS = (
    "reports/controller-plant-20261001/run_edge_plant_proof_r01.py",
    "reports/controller-plant-20261001/stage-r01/edge_plant.hpp",
    "reports/controller-plant-20261001/stage-r01/test_edge_plant.cpp",
)
SPI_PLANT_RTL_DIR = "reports/cnc3-stateful-implementation-20261001/serial-actual-SPI-motion-r01"
SPI_PLANT_INPUTS = (
    "reports/controller-plant-20261001/run_spi_edge_plant_r04.py",
    "reports/controller-plant-20261001/stage-r04/edge_plant.hpp",
    "reports/controller-plant-20261001/stage-r04/spi_edge_plant.cpp",
    "gateware/v3/frozen/protocol_v3.py", "gateware/v3/frozen/spec/protocol.json",
) + tuple(SPI_PLANT_RTL_DIR + "/" + name for name in (
    "cnc3_alarm_filter.v", "cnc3_encoder_runtime.v", "cnc3_motion_spi.v",
    "cnc3_motion_state.v", "cnc3_spi_transport_stateful.v", "cnc3_stepgen_runtime.v",
    "cnc3_command_validate.v", "cnc3_rate_admission_serial.v"))
SPI_PLANT_SCENARIOS = frozenset(("clean", "missed_steps", "watchdog", "encoder_unplug",
    "permission_drop", "drive_alarm", "field_power_loss", "provider_missing", "sensor_power_loss",
    "CS_stuck_low", "bad_CRC", "replayed_update", "wrong_session", "MOSI_stuck_high",
    "MOSI_stuck_low", "short_frame", "FPGA_reset", "FPGA_reset_during_CS"))
SEEDED_SPI_RUNNER = "reports/controller-plant-20261002/run_seeded_actual_SPI_faults_r02.py"
SEEDED_SPI_BASE = "reports/controller-plant-20261001/actual-spi-reset-fault-plant-r06"
SEEDED_SPI_INPUTS = (SEEDED_SPI_RUNNER, SEEDED_SPI_BASE + "/receipt.json") + tuple(
    SEEDED_SPI_BASE + "/inputs/" + name for name in (
        "frames.hpp", "edge_plant.hpp", "spi_edge_plant.cpp", "protocol_v3.py", "protocol.json",
        "cnc3_alarm_filter.v", "cnc3_encoder_runtime.v", "cnc3_motion_spi.v",
        "cnc3_motion_state.v", "cnc3_spi_transport_stateful.v", "cnc3_stepgen_runtime.v",
        "cnc3_command_validate.v", "cnc3_rate_admission_serial.v"))
IOL1_BUNDLE = "reports/cnc3-iol1-acquisition-20261001/diagnostic-replay-candidate-r01"
IOL1_STAGES = frozenset(("actual_cached_target_SPI", "compiled_safety_mutations",
    "cycle_exact_optimization", "composed_Efinix_family_mapping"))
IS2_BUNDLE = "reports/cnc3-is2-profile-20261002/profile-candidate-r02"
IS2_MANIFEST_SHA = "6b379afee372b2024c4f2a52f2a3a57fd9614b5672738d0c0db9669702958c3c"
IS2_STAGES = frozenset(("actual_IS2_page_and_two_C_drivers", "mutation_foreign_session_cannot_consume",
    "mutation_CMD_cannot_consume", "mutation_bad_CRC_cannot_queue", "mutation_fake_index_capability_rejected"))
STATEFUL_BUNDLE = "reports/cnc3-stateful-implementation-20261001/serial-replay-candidate-r02"
STATEFUL_STAGES = frozenset(("generator_equivalence", "encoder_alarm_filters", "stateful_motion",
    "rate_boundaries_mutations", "shared_admission_equivalence", "fault_priority", "state_safety_mutations",
    "actual_SPI_motion", "actual_SPI_rejection_sideband", "actual_SPI_rate_frame_binding", "family_synthesis_lint"))


def bundle_inputs(relative, root=ROOT):
    bundle = root / relative
    manifest = bundle / "bundle-manifest.json"
    if not manifest.is_file():
        return [relative + "/bundle-manifest.json"]
    files = json.loads(manifest.read_text())["files"]
    result = [relative + "/bundle-manifest.json"]
    for name in files:
        path = (bundle / name).resolve()
        if not path.is_relative_to(bundle.resolve()):
            raise ValueError("Replay input escaped its frozen bundle")
        result.append(path.relative_to(root).as_posix())
    return result


def stateful_inputs(root=ROOT):
    return bundle_inputs(STATEFUL_BUNDLE, root)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write(path, value):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    Path(path).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def utc():
    return datetime.now(timezone.utc).isoformat()


def snapshot(root=ROOT):
    return {p.relative_to(root).as_posix(): sha(p) for scope in SCOPES
            for p in sorted((root / scope).rglob("*"))
            if p.is_file() and (p.suffix.lower() in EXTENSIONS or p.name in SPECIAL_NAMES
                                or scope == "research" and p.suffix.lower() == ".pdf")
            and not any(part in SKIP for part in p.relative_to(root).parts)}


def differences(before, after):
    return {k: {"before": before.get(k), "after": after.get(k)}
            for k in sorted(set(before) | set(after)) if before.get(k) != after.get(k)}


def fresh_output(path, root=ROOT):
    path = Path(path).resolve()
    if not path.is_relative_to((root / "reports").resolve()):
        raise ValueError("Bench evidence must be inside this workspace's reports directory")
    if path.exists():
        raise ValueError("Existing evidence is immutable; choose a fresh output directory")
    path.mkdir(parents=True)
    return path


def unix(path):
    path = Path(path).resolve()
    if not path.drive or not path.as_posix()[2:].startswith("/"):
        raise ValueError("WSL runner requires a Windows drive path")
    return "/mnt/" + path.drive[0].lower() + path.as_posix()[2:]


def public_board(root=ROOT):
    revision = json.loads((root / "hardware/board_review/board-view.json").read_text())["current_revision"]
    if "/" in revision or "\\" in revision or ".." in revision:
        raise ValueError("Invalid published revision identity")
    path = root / "hardware/board_review/revisions" / revision / "motherboard-native-candidate.kicad_pcb"
    if not path.is_file():
        raise ValueError("Published full native motherboard is absent; supply --board explicitly")
    return path


def execute(command, directory, *, cwd=ROOT, timeout=600):
    """A literal argv and a fresh log; failed/time-limited commands stay failed."""
    directory.mkdir(parents=True, exist_ok=False)
    log = directory / "command.log"
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8",
               TEMP=str(directory), TMP=str(directory))
    started = time.monotonic()
    with log.open("wb") as stream:
        try:
            result = subprocess.run([str(x) for x in command], cwd=cwd, env=env,
                                    stdout=stream, stderr=subprocess.STDOUT, timeout=timeout)
            code, error = result.returncode, None
        except (OSError, subprocess.TimeoutExpired) as exc:
            code, error = None, str(exc)
    receipt = {"command": [str(x) for x in command], "cwd": str(cwd),
               "exit_code": code, "error": error,
               "wall_seconds": time.monotonic() - started,
               "log": str(log), "log_sha256": sha(log)}
    write(directory / "command.json", receipt)
    return receipt


def stage(name, evidence_type, status, reason, **fields):
    if status not in STATUSES:
        raise ValueError("Unknown validation status")
    return dict(name=name, status=status, evidence_type=evidence_type, reason=reason,
                physical_hardware_connected=False, hardware_qualified=False, **fields)


def result_status(stages, full):
    if any(s["status"] == "FAIL" for s in stages):
        return "FAIL"
    if any(s["status"] == "BLOCKED" for s in stages) and full:
        return "BLOCKED"
    return "PASS" if full and all(s["status"] == "PASS" for s in stages) else "NOT_RUN"


def command_stage(name, kind, command, out, *, artifact=None, predicate=None, cwd=ROOT, timeout=600):
    CONTEXT["stage"] = name
    run = execute(command, out / name, cwd=cwd, timeout=timeout)
    fields = {"execution": run}
    passed = run["exit_code"] == 0 and not run["error"]
    if artifact is not None:
        artifact = Path(artifact)
        fields["artifact"] = str(artifact)
        if artifact.is_file():
            fields["artifact_sha256"] = sha(artifact)
            try:
                value = json.loads(artifact.read_text(encoding="utf-8"))
                accepted = predicate(value) if predicate else True
                passed = passed and bool(accepted)
            except (ValueError, KeyError, TypeError) as exc:
                passed = False
                fields["artifact_error"] = str(exc)
        else:
            passed = False
            fields["missing_artifact"] = True
    return stage(name, kind, "PASS" if passed else "FAIL",
                 "Fresh command and exact artifact checked" if passed else "Command/artifact validation failed",
                 **fields)


def partial_spice_accept(value, count):
    """A passed component study cannot qualify the missing analog chain."""
    cases = value.get("cases", [])
    return (value.get("passed") is True and value.get("source_unchanged") is True
            and value.get("whole_analog_chain_passed") is False
            and value.get("physical_qualified") is False
            and value.get("manufacturing_ready") is False
            and len(cases) == count and all(c.get("passed") is True for c in cases)
            and len(value.get("source_channels", [])) == 4
            and bool(value.get("input_sha256")) and bool(value.get("scope")))


def run_partial_spice_stages(out, caps, distro):
    stages = []
    for name, kind, runner, count in PARTIAL_SPICE_RUNNERS:
        target = out / (name + "-evidence")
        if caps.get("HOST:ngspice") and all((ROOT / p).is_file() for p in (runner, *SPICE_INPUTS)):
            stages.append(command_stage(name, kind,
                [sys.executable, "-X", "utf8", ROOT / runner, "--out", target, "--wsl-distro", distro],
                out, artifact=target / "receipt.json",
                predicate=lambda v, count=count: partial_spice_accept(v, count), timeout=1800))
        else:
            stages.append(stage(name, kind, "BLOCKED", "Required simulator or frozen selected-part component inputs absent"))
    return stages


def isolated_plant_accept(value):
    cases = value.get("cases", [])
    return (value.get("status") == "PASS" and value.get("source_unchanged") is True
            and value.get("actual_FPGA_integration") is False
            and value.get("actual_LinuxCNC_integration") is False
            and value.get("complete_nine_machine_suite") is False
            and value.get("physical_qualified") is False
            and value.get("manufacturing_ready") is False
            and value.get("baseline_checks", 0) >= 1114
            and value.get("compiled_negative_controls") == 12
            and len(cases) == 13 and len({c.get("name") for c in cases}) == 13
            and all(c.get("passed") is True for c in cases)
            and bool(value.get("input_sha256")))


def run_isolated_plant_stage(out, caps, distro):
    name, kind = "isolated_edge_plant", "COMPILED_DISCONNECTED_IDEAL_MECHANICS_FIXTURE"
    target = out / (name + "-evidence")
    if caps.get("HOST:clang++") and all((ROOT / p).is_file() for p in PLANT_INPUTS):
        return command_stage(name, kind,
            [sys.executable, "-X", "utf8", ROOT / PLANT_INPUTS[0], "--out", target, "--wsl-distro", distro],
            out, artifact=target / "receipt.json", predicate=isolated_plant_accept, timeout=600)
    return stage(name, kind, "BLOCKED", "Actual mechanics fixture source or compiler unavailable")


def spi_plant_accept(value):
    """Real simulated pins/feedback with explicit ideal providers; never a HAL or hardware claim."""
    cases = value.get("cases", [])
    def checked_case(case):
        required = {"actual_stopped_outputs", "all_twelve_pin_counts",
                    "actual_encoder_waveform_drained", "actual_digital_analog_sources_unavailable"}
        if case.get("scenario") in ("clean", "missed_steps"):
            required.update(("four_actual_position_encoders", "continuity_preserved_after_clean_stop"))
        else:
            required.add("fault_continuity_invalid")
        if case.get("scenario") == "missed_steps":
            required.add("physical_encoder_differs_from_step_command")
        if case.get("scenario") in ("FPGA_reset", "FPGA_reset_during_CS"):
            required.add("hardware_counter_reset_is_not_mechanical_home")
        checks = case.get("checks", {})
        return (case.get("passed") is True and case.get("fixture_assertions", 0) >= 65
                and required.issubset(checks) and all(v is True for v in checks.values()))
    return (value.get("status") == "PASS" and value.get("source_unchanged") is True
            and value.get("actual_FPGA_integration") is True
            and value.get("behavioral_FPGA_substitution") is False
            and value.get("actual_LinuxCNC_integration") is False
            and value.get("complete_nine_machine_suite") is False
            and value.get("complete_safety_chain") is False
            and value.get("physical_qualified") is False
            and value.get("manufacturing_ready") is False
            and value.get("post_fault_correct_UPDATE_restart_rejected") is True
            and len(cases) == len(SPI_PLANT_SCENARIOS)
            and {c.get("scenario") for c in cases} == SPI_PLANT_SCENARIOS
            and all(checked_case(c) for c in cases)
            and bool(value.get("input_sha256")) and bool(value.get("gaps")))


def run_spi_plant_stage(out, caps, distro):
    name, kind = "actual_cnc3_SPI_edge_plant", "ACTUAL_VERILATED_CNC3_SPI_PINS_IDEAL_MECHANICS"
    target = out / (name + "-evidence")
    if (caps.get("HOST:clang++") and caps.get("HOST:verilator")
            and all((ROOT / p).is_file() for p in SPI_PLANT_INPUTS)):
        return command_stage(name, kind,
            [sys.executable, "-X", "utf8", ROOT / SPI_PLANT_INPUTS[0], "--out", target,
             "--rtl-dir", ROOT / SPI_PLANT_RTL_DIR, "--wsl-distro", distro],
            out, artifact=target / "receipt.json", predicate=spi_plant_accept, timeout=1200)
    return stage(name, kind, "BLOCKED", "Frozen candidate RTL, mechanics inputs or actual compilers absent")


def seeded_spi_accept(value):
    cases = value.get("cases", [])
    count = value.get("requested_trials")
    if type(count) is not int or not 1024 <= count <= 4096 or count % 8:
        return False
    return (value.get("status") == "PASS" and value.get("failure") is None
            and value.get("inputs_unchanged") is True
            and value.get("seed") == "0x434e4333"
            and value.get("completed_trials") == count and len(cases) == count
            and [c.get("trial") for c in cases] == list(range(count))
            and all(c.get("passed") is True and c.get("kind") == c["trial"] % 8
                    and c.get("checks", 0) >= 57 and 0 < c.get("inhibit_cycles", 0) <= 250001
                    for c in cases)
            and value.get("independently_decoded_responses", 0) >= count * 20
            and set(value.get("response_sha256", {})) == {f"responses-{i}.txt" for i in range(count)}
            and bool(value.get("input_sha256")) and len(value.get("precompile_input_sha256", {})) == 15
            and bool(value.get("generated_sha256"))
            and len(value.get("executions", [])) == 3
            and all(e.get("exit_code") == 0 for e in value.get("executions", []))
            and all(value.get(k) is True for k in ("actual_SPI_and_motion_RTL",
                "ideal_power_permission_and_mechanics", "post_fault_correct_UPDATE_restart_rejected",
                "all_twelve_real_pins_exercised"))
            and all(value.get(k) is False for k in ("actual_LinuxCNC_HAL",
                "complete22fault_electrical_suite", "complete_nine_machine_suite",
                "physical20ms_qualified", "manufacturing_ready")))


def run_seeded_spi_stage(out, caps, distro):
    name, kind = "seeded_actual_SPI_faults", "FRESH_VERILATED_2048_SEEDED_SERIAL_FAULTS_IDEAL_PROVIDERS"
    if not (caps.get("HOST:clang++") and caps.get("HOST:verilator")
            and all((ROOT / p).is_file() for p in SEEDED_SPI_INPUTS)):
        return stage(name, kind, "BLOCKED", "Actual RTL/frozen compiled fixture inputs or compilers absent")
    target = out / (name + "-evidence")
    return command_stage(name, kind,
        [sys.executable, "-X", "utf8", ROOT / SEEDED_SPI_RUNNER, "--out", target,
         "--count", "2048", "--wsl-distro", distro], out,
        artifact=target / "receipt.json", predicate=seeded_spi_accept, timeout=4000)


def stateful_accept(value):
    rows = value.get("stages", [])
    flags = value.get("scope_flags", {})
    required_false = ("actual_physical_SPI_wire", "real_LinuxCNC_HAL",
        "full_CNC3_CAP3_pages_IOL1_events_output_chain", "complete_machine_or_vendor_T20_fit_timing",
        "physical_safety_or_new_ratings", "standalone_experimental_2MHz_authorized_runtime",
        "request_backpressure_queue_in_motion_scope")
    return (value.get("status") == "PASS" and value.get("input_integrity") is True
            and value.get("inputs_unchanged") is True
            and value.get("counts") == {"PASS": 11, "FAIL": 0, "BLOCKED": 0, "NOT_RUN": 0}
            and len(rows) == len(STATEFUL_STAGES) and {r.get("name") for r in rows} == STATEFUL_STAGES
            and all(r.get("status") == "PASS" and r.get("exit_code") == 0
                    and r.get("receipt_sha256") for r in rows)
            and all(flags.get(k) is False for k in required_false)
            and flags.get("actual_simulated_SPI_edges_and_CRC") is True
            and flags.get("ideal_provider_inputs") is True
            and value.get("protocol_rate_max") == 0x01000000
            and bool(value.get("exact_inputs")) and bool(value.get("bundle_manifest_sha256")))


def run_stateful_stage(out, caps, distro):
    name, kind = "bounded_CNC3_stateful_replay", "ACTUAL_CNC3_STATE_RATE_SPI_MUTATIONS_FAMILY_MAPPING"
    bundle, target = ROOT / STATEFUL_BUNDLE, out / (name + "-evidence")
    if not (caps.get("HOST:iverilog") and caps.get("HOST:verilator") and caps.get("ROOTFS:yosys")
            and all((ROOT / p).is_file() for p in stateful_inputs())
            and (bundle / "replay_motion.py").is_file()):
        return stage(name, kind, "BLOCKED", "Frozen stateful bundle or actual simulators/family mapper absent")
    # The mechanics proof and state tests must exercise the same RTL bytes.
    for path in SPI_PLANT_INPUTS[5:]:
        original = ROOT / path
        copied = bundle / original.name
        if original.name == "cnc3_command_validate.v":
            copied = bundle / "inputs/workspace/gateware/v3/rtl/cnc3_command_validate.v"
        if not copied.is_file() or sha(copied) != sha(original):
            return stage(name, kind, "FAIL", "Stateful/actual-SPI mechanics RTL identities disagree", source=path)
    return command_stage(name, kind,
        [sys.executable, "-X", "utf8", bundle / "replay_motion.py", "--out", target, "--wsl-distro", distro],
        out, artifact=target / "report.json", predicate=stateful_accept, timeout=4800)


def iol1_acquisition_accept(value):
    rows = value.get("stages", [])
    flags = value.get("scope_flags", {})
    return (value.get("status") == "PASS" and value.get("bundle_integrity") is True
            and value.get("inputs_unchanged") is True
            and value.get("counts") == {"PASS": 4, "FAIL": 0, "BLOCKED": 0, "NOT_RUN": 0}
            and len(rows) == 4 and {r.get("name") for r in rows} == IOL1_STAGES
            and all(r.get("status") == "PASS" and r.get("exit_code") == 0
                    and r.get("receipt_sha256") for r in rows)
            and flags.get("actual_simulated_four_lane_SPI_and_same_C_protocol") is True
            and all(flags.get(k) is False for k in ("actual_ARM_DMA_IRQ_or_ADC",
                "commercial_ACTIVE_or_factory_identity", "outputs_ARM_CAP3_HAL",
                "full_machine_or_vendor_T20_fit_timing", "physical_qualification_or_new_ratings"))
            and bool(value.get("exact_inputs")) and bool(value.get("bundle_manifest_sha256"))
            and bool(value.get("open_dependencies")))


def run_iol1_acquisition_stage(out, caps, distro):
    name, kind = "bounded_IOL1_diagnostic_acquisition", "ACTUAL_C_TARGET_SPI_RTL_AGE_MUTATIONS_FAMILY_MAPPING"
    bundle, target = ROOT / IOL1_BUNDLE, out / (name + "-evidence")
    if not (caps.get("HOST:iverilog") and caps.get("ROOTFS:gcc") and caps.get("ROOTFS:yosys")
            and all((ROOT / p).is_file() for p in bundle_inputs(IOL1_BUNDLE))
            and (bundle / "replay_acquisition.py").is_file()):
        return stage(name, kind, "BLOCKED", "Frozen acquisition bundle or actual target protocol compiler/simulators absent")
    return command_stage(name, kind,
        [sys.executable, "-X", "utf8", bundle / "replay_acquisition.py", "--out", target, "--wsl-distro", distro],
        out, artifact=target / "report.json", predicate=iol1_acquisition_accept, timeout=1200)


def is2_profile_accept(value):
    rows, flags = value.get("stages", []), value.get("scope_flags", {})
    return (value.get("status") == "PASS" and value.get("bundle_integrity") is True
            and value.get("inputs_unchanged") is True
            and value.get("bundle_manifest_sha256") == IS2_MANIFEST_SHA
            and value.get("counts") == {"PASS": 5, "FAIL": 0, "BLOCKED": 0, "NOT_RUN": 0}
            and len(rows) == 5 and {r.get("name") for r in rows} == IS2_STAGES
            and all(r.get("status") == "PASS" and r.get("exit_code") == 0
                    and r.get("receipt_sha256") for r in rows)
            and flags.get("actual_compiled_C_to_actual_simulated_RTL_SPI_CAP3") is True
            and flags.get("explicit_IS2_integrated12_class0_four_encoder_inventory") is True
            and all(flags.get(k) is False for k in ("PROFILE_COMPLETE",
                "ACTUAL_physical_providers_identity_or_full_output_authority",
                "commissioning_ARM_12joint_HAL_physical_qualification",
                "product_rate_frame_layout_shared_sources_changed"))
            and bool(value.get("exact_inputs")) and bool(value.get("open_dependencies")))


def run_is2_profile_stage(out, caps, distro):
    name, kind = "bounded_IS2_CAP3_profile", "ACTUAL_COMPILED_C_RTL_SPI_DISCOVERY_FAIL_CLOSED_MUTATIONS"
    bundle, target = ROOT / IS2_BUNDLE, out / (name + "-evidence")
    if not (caps.get("HOST:verilator") and caps.get("HOST:clang++")
            and all((ROOT / p).is_file() for p in bundle_inputs(IS2_BUNDLE))
            and (bundle / "replay_profile.py").is_file()):
        return stage(name, kind, "BLOCKED", "Frozen IS2 discovery bundle or actual C/RTL compiler absent")
    if sha(bundle / "bundle-manifest.json") != IS2_MANIFEST_SHA:
        return stage(name, kind, "FAIL", "Frozen IS2 discovery manifest differs")
    return command_stage(name, kind,
        [sys.executable, "-X", "utf8", bundle / "replay_profile.py", "--out", target, "--wsl-distro", distro],
        out, artifact=target / "report.json", predicate=is2_profile_accept, timeout=1800)


def capability_inventory(out, distro):
    script = out / "capability-inventory.sh"
    script.write_text("#!/bin/sh\nset -u\n"
        "for t in python3 gcc g++ clang clang++ ld.lld iverilog vvp verilator ngspice efx_run; do\n"
        " p=$(command -v \"$t\" 2>/dev/null || true); printf 'HOST:%s:%s\\n' \"$t\" \"$p\"; done\n"
        f"r='{LAB_ROOTFS}'\n"
        "if test -f \"$r/etc/debian_version\"; then\n"
        " chroot \"$r\" /bin/sh -c 'for t in gcc g++ yosys halrun linuxcnc ngspice efx_run; do p=$(command -v \"$t\" 2>/dev/null || true); printf \"ROOTFS:%s:%s\\n\" \"$t\" \"$p\"; done'\n"
        "fi\n", encoding="utf-8", newline="\n")
    if not shutil.which("wsl"):
        return {"WSL": False, "reason": "wsl executable unavailable"}
    result = execute(["wsl", "-d", distro, "--", "sh", unix(script)], out / "capabilities", timeout=30)
    values = {"WSL": result["exit_code"] == 0, "execution": result}
    for line in Path(result["log"]).read_text(errors="replace").splitlines():
        if line.startswith(("HOST:", "ROOTFS:")):
            scope, name, path = line.split(":", 2)
            values[scope + ":" + name] = path or None
    return values


def run_unittest_worker(mode, out, ids=None):
    """Run real cases, retaining skip IDs for exact native replay, not duplicates."""
    sys.path[:0] = [str(ROOT), str(ROOT / "tests"), str(ROOT / "tools")]
    sys.dont_write_bytecode = True
    loader = unittest.TestLoader()
    suite = loader.discover(str(ROOT / "tests")) if mode == "host" else loader.loadTestsFromNames(ids)
    out.mkdir(parents=True, exist_ok=False)
    before = snapshot()
    with (out / "tests.log").open("w", encoding="utf-8") as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    changed = differences(before, snapshot())
    skipped = [{"id": t.id(), "reason": reason} for t, reason in result.skipped]
    value = {"passed": result.wasSuccessful() and result.testsRun > 0 and not changed,
             "reported_tests": result.testsRun,
             "passed_tests": result.testsRun - len(result.skipped) - len(result.errors) - len(result.failures),
             "skipped": skipped, "failures": [(t.id(), text) for t, text in result.failures],
             "errors": [(t.id(), text) for t, text in result.errors],
             "source_changes": changed, "source_hashes_unchanged": not changed,
             "native_selected_ids": ids if mode == "native" else None,
             "python": sys.executable, "log_sha256": sha(out / "tests.log")}
    if mode == "native" and skipped:
        value["passed"] = False
    write(out / "receipt.json", value)
    return 0 if value["passed"] else 1


def copied_tree(source, dest):
    shutil.copytree(source, dest, ignore=shutil.ignore_patterns(
        "__pycache__", "build", "evidence", ".git", "*.pyc"))
    return {p.relative_to(dest).as_posix(): sha(source / p.relative_to(dest))
            for p in dest.rglob("*") if p.is_file()}


def connectivity_integrity(value):
    native = value["uncapped_unconnected_ratsnest_edges"]
    independent = value["independent_physical_cluster_missing_joins"]
    return (value["source_net_checks_pass"] is True
            and value["complete_source_population_pass"] is True
            and not value["orphan_copper_items"]
            and type(native) is int and type(independent) is int
            and native >= 0 and independent >= 0 and native == independent)


def full_route_stage(value, integrity):
    remaining = value.get("independent_physical_cluster_missing_joins")
    status = "FAIL" if integrity["status"] != "PASS" else "BLOCKED" if remaining else "PASS"
    return stage("complete_PCB_routing", "NATIVE_PHYSICAL_CONNECTIVITY", status,
                 f"{remaining} uncapped Source-cluster joins remain; independent integrity {integrity['status']}",
                 missing_joins=remaining, required_integrity_stage=integrity["name"])


def native_violations(value, kind):
    if kind == "ERC":
        sheets = value["sheets"]
        if not isinstance(sheets, list) or not sheets:
            raise ValueError("Native ERC must contain its per-sheet results")
        return [row for sheet in sheets for row in sheet["violations"]]
    return value["violations"]


def native_erc_accept(value):
    return not value["ignored_checks"] and all(row["severity"] == "warning" for row in native_violations(value, "ERC"))


def cnc3_host(out, external, distro):
    CONTEXT["stage"] = "cnc3_host_model"
    folder = out / "cnc3-host-inputs"
    folder.mkdir()
    inputs = copied_tree(external / "cnc3", folder / "cnc3")
    # The unmodified host runner uses ASan in the prepared glibc rootfs. Only
    # its disposable work directory is made run-specific in the copied script.
    script = folder / "cnc3/tools/host_tests_rootfs.sh"
    original = script.read_text()
    work = "pre-hardware-cnc3-" + hashlib.sha256(str(out).encode()).hexdigest()[:16]
    script.write_text(original.replace("cnc3-host", work), newline="\n")
    result = command_stage("cnc3_host_model", "HOST_C_MODEL_ASAN_UBSAN",
        ["wsl", "-d", distro, "--", "sh", unix(script)], out)
    changed = {p: expected for p, expected in inputs.items()
               if not (external / "cnc3" / p).is_file() or sha(external / "cnc3" / p) != expected}
    result.update(external_input_sha256=inputs, original_external_sources_unchanged=not changed,
                  behavioral_endpoint_model=True, actual_RTL=False, real_LinuxCNC=False,
                  copied_runner_path_delta={"before_sha256": hashlib.sha256(original.encode()).hexdigest(),
                                            "after_sha256": sha(script), "unique_lab_work": work})
    if changed:
        result["status"] = "FAIL"
        result["reason"] = "Frozen external source changed during the run"
    return result


def cnc3_layout(out, external):
    CONTEXT["stage"] = "cnc3_layout_contract"
    folder = out / "cnc3-layout-inputs"
    folder.mkdir()
    records = {}
    for name in ("cnc3", "spec", "gateware/v3"):
        records[name] = copied_tree(external / name, folder / name)
    result = command_stage("cnc3_layout_contract", "GENERATED_C_PROTOCOL_LAYOUT_CHECK",
        [sys.executable, "-X", "utf8", folder / "gateware/v3/tools/gen_c_layout.py", "--check"], out)
    changed = {name + "/" + p: h for name, rows in records.items() for p, h in rows.items()
               if not (external / name / p).is_file() or sha(external / name / p) != h}
    result.update(external_input_sha256=records, original_external_sources_unchanged=not changed,
                  actual_RTL=False, target_compilation=False)
    if changed:
        result.update(status="FAIL", reason="Frozen external generated-layout inputs changed")
    return result


def historical_linuxcnc(out, distro):
    CONTEXT["stage"] = "historical_linuxcnc_six_two"
    folder = out / "historical-six-two-inputs"
    folder.mkdir()
    records = {}
    for name in ("cnc1", "gateware/rtl", "controller_config"):
        records[name] = copied_tree(ROOT / name, folder / name)
    # The checked-in runners write only this copy's evidence. The existing
    # isolated lab module is saved/restored; no user machine configuration is
    # touched. The runtime runner uses private mount/PID/IPC/network namespaces.
    script = folder / "run-historical-linuxcnc.sh"
    script.write_text("#!/bin/sh\nset -eu\ncd \"$(dirname \"$0\")\"\n"
        f"r='{LAB_ROOTFS}'\n"
        f"backup=\"$r/work/pre-hardware-module-{hashlib.sha256(str(out).encode()).hexdigest()[:16]}\"\n"
        "mkdir -p \"$backup\"\n"
        "m=\"$r/usr/lib/linuxcnc/modules/cnc1_sim.so\"\n"
        "if test -f \"$m\"; then cp \"$m\" \"$backup/cnc1_sim.so\"; fi\n"
        "restore() { if test -f \"$backup/cnc1_sim.so\"; then cp \"$backup/cnc1_sim.so\" \"$m\"; else rm -f \"$m\"; fi; }\n"
        "trap restore EXIT HUP INT TERM\n"
        "sh cnc1/tools/build.sh\nsh cnc1/tools/run_linuxcnc.sh\n", newline="\n")
    artifact = folder / "cnc1/evidence/linuxcnc.json"
    result = command_stage("historical_linuxcnc_six_two", "REAL_LINUXCNC_VERILATED_CNC1",
        ["wsl", "-d", distro, "--", "sh", unix(script)], out,
        artifact=artifact, predicate=lambda v: v.get("success") is True, timeout=480)
    changed = []
    for name, rows in records.items():
        changed += [name + "/" + p for p, h in rows.items() if sha(ROOT / name / p) != h]
    result.update(original_source_hashes=records, original_sources_unchanged=not changed,
                  active_motion_channels=6, encoder_channels=2,
                  current_twelve_channel_runtime=False, CNC3=False,
                  runtime_interfaces="isolated simulation only; no spidev or machine devices")
    if changed:
        result["status"] = "FAIL"
        result["reason"] = "Historical original source changed"
    return result


def required_blockers():
    return [stage(name, kind, "BLOCKED", reason) for name, kind, reason in (
        ("cnc3_actual_rtl_transport", "REAL_LINUXCNC_CNC3_ACTUAL_RTL",
         "Bounded actual CNC3 motion/session/rate/SPI RTL is tested separately; real CNC3 HAL/LinuxCNC integration and complete CAP3/pages/IOL1/events/output authority remain absent"),
        ("twelve_joint_simultaneous_machine", "SIMULATED_FULL_MACHINE",
         "Actual twelve STEP/DIR outputs and four ABZ algorithms couple to ideal mechanics in a separate fixture; full LinuxCNC machine kinematics, electrical providers and all I/O are not integrated"),
        ("critical_circuit_spice_corners", "SPICE_CORNER_MONTE_CARLO",
         "Selected passive and buffer studies are partial; complete analog models/corners, physical power/permission circuits and coupled worst-case loads remain unqualified"),
        ("efinity_vendor_fit_timing", "VENDOR_PLACEMENT_ROUTE_STATIC_TIMING",
         "No qualified Efinity project/license/actual source/pin-bank/timing flow; Yosys family synthesis is separate"),
        ("simultaneous_full_load", "LOADED_TARGET_REALTIME",
         "No complete target machine coupled to UI/network/ESP/I/O/analog/fieldbus loads; host tests do not prove servo jitter"),
        ("signal_integrity_and_cables", "IBIS_ROUTED_SI",
         "Routing/stackup/process/receiver/cable models and loaded timing remain unqualified"),
        ("thermal_current_qualification", "ELECTROTHERMAL_MODEL",
         "No complete guaranteed load/copper/contact/enclosure model or physical thermal measurements"),
        ("full_setup_operator_workflow", "END_TO_END_UI_MACHINE",
         "Existing host supervisor/configuration cases do not implement provisioning/CAD registration/homing/machining/recovery of every proposed machine"),
    )] + [stage("physical_qualification", "PHYSICAL_MEASUREMENT", "NOT_RUN",
               "No assembled prototype; no physical electrical/EMC/temperature/20ms measurements")]


def characterization(stages, source_hash, board_hash, stepgen=None, do_contract=None, encoder=None):
    """Requested ratings are targets; no numerical simulated limit is invented."""
    rows = []
    for subsystem in ("STEP/DIR12", "encoder_full_chain", "SPI", "servo_deadline",
                      "probe_latency", "24V_input_threshold", "DO_channel_and_bank",
                      "rail_capacity", "analog_accuracy", "watchdog_inhibit",
                      "powerup_brownout", "thermal", "cable_signal_integrity"):
        rows.append({"subsystem": subsystem,
                     "limit_class": "PHYSICAL VALIDATION REQUIRED",
                     "measured_simulated_failure_limit": None,
                     "conservative_provisional_product_rating": None,
                     "hardware_qualified_limit": None,
                     "reason": "Complete chain/corners/vendor fit/final route/physical qualification incomplete"})
    if stepgen is not None:
        if stepgen.get("status") != "PASS" or not stepgen.get("source_hashes_unchanged"):
            raise ValueError("Failed/stale pulse-generator sweep cannot provide a simulated limit")
        for profile in stepgen["profiles"]:
            rows.append({"subsystem": "standalone_cnc_stepgen12/" + profile["name"],
                         "limit_class": "SIMULATED LIMIT",
                         "measured_simulated_failure_limit": profile["first_adversarial_failure_hz"],
                         "analytical_safe_hz_at_assumed_50MHz": profile["design_pulse_ceiling_hz"],
                         "conservative_provisional_product_rating": None,
                         "hardware_qualified_limit": None,
                         "CNC3_full_machine": False,
                         "reason": "Twelve isolated actual RTL instances; endpoint, output-driver/cable, vendor timing and full load excluded"})
    if do_contract is not None:
        for name, field in (("DO_channel", "continuous_limit_a_per_channel"),
                            ("DO_quad_bank", "continuous_limit_a_per_quad")):
            rows.append({"subsystem": name, "limit_class": "DESIGN LIMIT",
                         "configured_design_limit_a": do_contract[field],
                         "measured_simulated_failure_limit": None,
                         "conservative_provisional_product_rating": None,
                         "hardware_qualified_limit": None,
                         "source_contract_sha256": do_contract["source_sha256"],
                         "reason": "Frozen current envelope; not a loaded thermal, contact, firmware-trip or physical measurement result"})
    if encoder is not None:
        if encoder.get("passed") is not True:
            raise ValueError("Failed encoder sweep cannot supply provisional evidence")
        rows.append({"subsystem": "standalone_cnc_encoder4", "limit_class": "SIMULATED LIMIT",
                     "ideal_tested_pass_quadrature_edge_rate_hz": encoder["ideal_pass_edge_rate_hz"],
                     "first_tested_failing_quadrature_edge_rate_hz": encoder["first_tested_failing_edge_rate_hz"],
                     "measured_simulated_failure_limit": None,
                     "continuous_exact_failure_boundary_proved": False,
                     "conservative_provisional_product_rating": None, "hardware_qualified_limit": None,
                     "reason": "Ideal digital component samples only; actual receiver/cable/metastability/vendor timing and twelve-encoder expansion excluded"})
    return {"schema_version": 1, "source_design_sha256": source_hash,
            "board_sha256": board_hash, "entries": rows,
            "requested_motion_target": {"channels": 12, "STEP_hz_per_channel": 2000000,
                                        "servo_hz": 1000, "qualified": False},
            "evidence_categories": sorted({r["evidence_type"] for r in stages}),
            "simulation_is_hardware_qualification": False,
            "manufacturing_ready": False}


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__)
    mode = ap.add_mutually_exclusive_group(required=True)
    mode.add_argument("--full", action="store_true")
    mode.add_argument("--inventory", action="store_true")
    mode.add_argument("--worker", choices=("host", "native"), help=argparse.SUPPRESS)
    ap.add_argument("--out", type=Path)
    ap.add_argument("--board", type=Path)
    ap.add_argument("--external-cnc3", type=Path, default=EXTERNAL)
    ap.add_argument("--wsl-distro", default="GarciaMechBuilder")
    ap.add_argument("--native-python", type=Path, default=KICAD / "python.exe")
    ap.add_argument("--kicad-cli", type=Path, default=KICAD / "kicad-cli.exe")
    ap.add_argument("--ids", type=Path, help=argparse.SUPPRESS)
    a = ap.parse_args(argv)
    if a.worker:
        return run_unittest_worker(a.worker, a.out, json.loads(a.ids.read_text()) if a.ids else None)
    default = ROOT / "reports/pre-hardware-validation-20261001" / (utc().replace(":", "").replace("+", "") + "-" + a.full.__str__())
    out = fresh_output(a.out or default)
    CONTEXT.update(output=out, stage="input_binding")
    before = snapshot()
    write(out / "source-before.json", before)
    board = (a.board or public_board()).resolve()
    source = ROOT / "hardware/motherboard"
    binding = {"source_design": str(source / "design.json"),
               "source_design_sha256": sha(source / "design.json"),
               "source_netlist_sha256": sha(source / "netlist.xml"),
               "board": str(board), "board_sha256": sha(board),
               "runner_sha256": sha(Path(__file__)),
               "report_local_component_inputs": {p: sha(ROOT / p) for p in
                    [p for row in PARTIAL_RTL_RUNNERS for p in row[2:]]
                    + [row[2] for row in PARTIAL_SPICE_RUNNERS] + list(SPICE_INPUTS) + list(PLANT_INPUTS)
                    + list(SPI_PLANT_INPUTS) + list(SEEDED_SPI_INPUTS) + stateful_inputs() + bundle_inputs(IOL1_BUNDLE) + bundle_inputs(IS2_BUNDLE)
                    if (ROOT / p).is_file()}}
    write(out / "binding.json", binding)
    caps = capability_inventory(out, a.wsl_distro)
    write(out / "capabilities.json", caps)
    stages = required_blockers()
    if a.full:
        worker = [sys.executable, "-X", "utf8", str(Path(__file__)), "--worker", "host", "--out", str(out / "host-cases")]
        stages.append(command_stage("host_suite", "HOST_UNIT_CONTRACT_TEST", worker, out,
            artifact=out / "host-cases/receipt.json", predicate=lambda v: v["passed"]))
        host = json.loads((out / "host-cases/receipt.json").read_text()) if (out / "host-cases/receipt.json").exists() else {}
        ids = [r["id"] for r in host.get("skipped", []) if "KiCad" in r["reason"]]
        write(out / "native-ids.json", ids)
        if a.native_python.is_file() and ids:
            stages.append(command_stage("native_test_replay", "NATIVE_KICAD_TEST", [a.native_python, "-X", "utf8", Path(__file__), "--worker", "native", "--out", out / "native-cases", "--ids", out / "native-ids.json"], out,
                artifact=out / "native-cases/receipt.json", predicate=lambda v: v["passed"] and not v["skipped"]))
        else:
            stages.append(stage("native_test_replay", "NATIVE_KICAD_TEST", "BLOCKED", "Native Python or exact host KiCad skip IDs unavailable"))
        stages.append(command_stage("native_source_validation", "SOURCE_PIN_MPN_FOOTPRINT_CHECK", [sys.executable, "-X", "utf8", "tools/hardware_validate_motherboard.py", "--source", source, "--output", out / "native-source.json"], out,
            artifact=out / "native-source.json", predicate=lambda v: v["source_checks_pass"]))
        if a.kicad_cli.is_file():
            stages.append(command_stage("native_ERC", "NATIVE_KICAD_ERC", [a.kicad_cli, "sch", "erc", "--format", "json", "--severity-all", "--output", out / "erc.json", source / "motherboard.kicad_sch"], out,
                artifact=out / "erc.json", predicate=native_erc_accept))
            stages.append(command_stage("native_DRC", "NATIVE_KICAD_DRC", [a.kicad_cli, "pcb", "drc", "--format", "json", "--all-track-errors", "--severity-all", "--output", out / "drc.json", board], out,
                artifact=out / "drc.json", predicate=lambda v: not v.get("ignored_checks") and not v["violations"]))
            for name, file in (("native_ERC", "erc.json"), ("native_DRC", "drc.json")):
                if (out / file).is_file():
                    try:
                        value = json.loads((out / file).read_text(encoding="utf-8"))
                        row = next(s for s in stages if s["name"] == name)
                        row.update(unsuppressed_violations=dict(Counter(v["severity"] for v in native_violations(value, name.removeprefix("native_")))),
                                   ignored_checks=value.get("ignored_checks", []),
                                   complete_routing_qualified=False)
                        row["reason"] = (f"Regular {name.removeprefix('native_')} violations: {row['unsuppressed_violations']}; "
                                         "all warnings/ignored-check records retained; full routing requires uncapped independent connectivity")
                    except (ValueError, KeyError, TypeError):
                        pass  # Malformed evidence is already a failed command_stage.
        else:
            stages.extend(stage(name, kind, "BLOCKED", "Native KiCad CLI unavailable") for name, kind in (
                ("native_ERC", "NATIVE_KICAD_ERC"), ("native_DRC", "NATIVE_KICAD_DRC")))
        if a.native_python.is_file():
            integrity = command_stage("source_physical_connectivity", "NATIVE_SOURCE_CLUSTER_INDEPENDENT_COUNT", [a.native_python, "-X", "utf8", "tools/motion_card_routing_inventory.py", "--board", board, "--netlist", source / "netlist.xml", "--source-design", source / "design.json", "--out", out / "connectivity"], out,
                artifact=out / "connectivity/review.json", predicate=connectivity_integrity)
            stages.append(integrity)
            if (out / "connectivity/review.json").is_file():
                value = json.loads((out / "connectivity/review.json").read_text())
                stages.append(full_route_stage(value, integrity))
        else:
            stages.extend(stage(name, kind, "BLOCKED", "Native KiCad Python unavailable") for name, kind in (
                ("source_physical_connectivity", "NATIVE_SOURCE_CLUSTER_INDEPENDENT_COUNT"),
                ("complete_PCB_routing", "NATIVE_PHYSICAL_CONNECTIVITY")))
        if caps.get("HOST:iverilog") and caps.get("HOST:clang") and caps.get("ROOTFS:yosys"):
            for name, tool, kind in (("watchdog_RTL", "hardware_check_motherboard_watchdog_rtl.py", "RTL_SIMULATION_LINT_FAMILY_SYNTHESIS"),
                                     ("IOL1_target", "hardware_check_motherboard_iol1_firmware.py", "ARM_TARGET_COMPILE_HOST_C_RTL_VPI_FAMILY_SYNTHESIS")):
                target = out / (name + "-evidence")
                stages.append(command_stage(name, kind, [sys.executable, "-X", "utf8", ROOT / "tools" / tool, "--output-dir", target], out,
                    artifact=target / "receipt.json", predicate=lambda v: v.get("passed", v.get("tool_exit") == 0)
                    and v.get("inputs_unchanged", not v.get("source_changed_during_run", False)), timeout=600))
        else:
            stages.extend(stage(name, kind, "BLOCKED", "Required isolated compiler/synthesis tools unavailable") for name, kind in (
                ("watchdog_RTL", "RTL_SIMULATION_LINT_FAMILY_SYNTHESIS"),
                ("IOL1_target", "ARM_TARGET_COMPILE_HOST_C_RTL_VPI_FAMILY_SYNTHESIS")))
        step_path = out / "stepgen12-evidence"
        if caps.get("HOST:iverilog") and (ROOT / "tools/characterize_stepgen12.py").is_file():
            stages.append(command_stage("isolated_stepgen12_sweep", "ACTUAL_RTL_FAILURE_BOUNDARY_SWEEP",
                [sys.executable, "-X", "utf8", ROOT / "tools/characterize_stepgen12.py", "--out", step_path, "--wsl-distro", a.wsl_distro], out,
                artifact=step_path / "receipt.json", predicate=lambda v: v["status"] == "PASS" and v["source_hashes_unchanged"], timeout=1800))
        else:
            stages.append(stage("isolated_stepgen12_sweep", "ACTUAL_RTL_FAILURE_BOUNDARY_SWEEP", "BLOCKED", "Actual pulse generator compiler/bench absent"))
        for name, kind, runner, fixture in PARTIAL_RTL_RUNNERS:
            target = out / (name + "-evidence")
            if caps.get("HOST:iverilog") and (ROOT / runner).is_file() and (ROOT / fixture).is_file():
                stages.append(command_stage(name, kind, [sys.executable, "-X", "utf8", ROOT / runner, "--out", target], out,
                    artifact=target / "receipt.json", predicate=lambda v: v["passed"] is True, timeout=1900))
            else:
                stages.append(stage(name, kind, "BLOCKED", "Required actual component fixture/compiler unavailable"))
        stages.extend(run_partial_spice_stages(out, caps, a.wsl_distro))
        stages.append(run_isolated_plant_stage(out, caps, a.wsl_distro))
        stages.append(run_spi_plant_stage(out, caps, a.wsl_distro))
        stages.append(run_seeded_spi_stage(out, caps, a.wsl_distro))
        stages.append(run_iol1_acquisition_stage(out, caps, a.wsl_distro))
        stages.append(run_is2_profile_stage(out, caps, a.wsl_distro))
        stages.append(run_stateful_stage(out, caps, a.wsl_distro))
        if caps.get("ROOTFS:gcc") and (a.external_cnc3 / "cnc3/tools/host_tests_rootfs.sh").is_file():
            if all((a.external_cnc3 / p).is_dir() for p in ("cnc3", "spec", "gateware/v3")):
                stages.append(cnc3_layout(out, a.external_cnc3))
            else:
                stages.append(stage("cnc3_layout_contract", "GENERATED_C_PROTOCOL_LAYOUT_CHECK", "BLOCKED", "Complete frozen layout sources absent"))
            stages.append(cnc3_host(out, a.external_cnc3, a.wsl_distro))
        else:
            stages.append(stage("cnc3_host_model", "HOST_C_MODEL", "BLOCKED", "Frozen external host source or isolated compiler absent"))
        if caps.get("HOST:iverilog") and caps.get("HOST:verilator") and caps.get("HOST:gcc") and caps.get("ROOTFS:yosys"):
            target = out / "cnc3-structural-RTL-evidence"
            stages.append(command_stage("cnc3_structural_RTL", "ACTUAL_CNC3_TRANSPORT_CODEC_RTL_C_ORACLE_FAMILY_SYNTHESIS",
                [sys.executable, "-X", "utf8", ROOT / "tools/check_cnc3_rtl.py", "--out", target, "--synthesis"], out,
                artifact=target / "receipt.json", predicate=lambda v: v["status"] == "PASS" and v["source_hashes_unchanged"] and v["family_synthesis"] == "PASS", timeout=600))
        else:
            stages.append(stage("cnc3_structural_RTL", "ACTUAL_CNC3_TRANSPORT_CODEC_RTL_C_ORACLE_FAMILY_SYNTHESIS", "BLOCKED", "Required structural RTL compilers/family synthesis unavailable"))
        if caps.get("ROOTFS:linuxcnc") and caps.get("HOST:verilator"):
            stages.append(historical_linuxcnc(out, a.wsl_distro))
        else:
            stages.append(stage("historical_linuxcnc_six_two", "REAL_LINUXCNC_CNC1", "BLOCKED", "Isolated LinuxCNC/Verilator unavailable"))
        stages.append(command_stage("supervisor_fault_scenarios", "HOST_SUPERVISOR_MODEL", [sys.executable, "-X", "utf8", "-m", "controller_lab.run_scenarios", "--output", out / "supervisor.json"], out,
            artifact=out / "supervisor.json", predicate=lambda v: bool(v["cases"]) and all(c["result"] == "pass" for c in v["cases"])))
    else:
        stages.extend(stage(name, kind, "NOT_RUN", "Inventory mode did not execute validation") for name, kind in (
            ("host_suite", "HOST_UNIT_CONTRACT_TEST"), ("native_source_validation", "SOURCE_INSPECTION"),
            ("native_test_replay", "NATIVE_KICAD_TEST"), ("native_ERC", "NATIVE_KICAD_ERC"),
            ("native_DRC", "NATIVE_KICAD_DRC"), ("source_physical_connectivity", "NATIVE_SOURCE_CLUSTER_INDEPENDENT_COUNT"),
            ("complete_PCB_routing", "NATIVE_PHYSICAL_CONNECTIVITY"),
            ("historical_linuxcnc_six_two", "REAL_LINUXCNC_CNC1"), ("cnc3_host_model", "HOST_C_MODEL"),
            ("cnc3_layout_contract", "GENERATED_C_PROTOCOL_LAYOUT_CHECK"), ("watchdog_RTL", "RTL_SIMULATION_LINT_FAMILY_SYNTHESIS"),
            ("cnc3_structural_RTL", "ACTUAL_CNC3_TRANSPORT_CODEC_RTL_C_ORACLE_FAMILY_SYNTHESIS"),
            ("isolated_stepgen12_sweep", "ACTUAL_RTL_FAILURE_BOUNDARY_SWEEP"), ("supervisor_fault_scenarios", "HOST_SUPERVISOR_MODEL"),
            ("IOL1_target", "TARGET_COMPILATION")))
        stages.extend(stage(name, kind, "NOT_RUN", "Inventory mode did not execute component validation") for name, kind, *_ in PARTIAL_RTL_RUNNERS)
        stages.extend(stage(name, kind, "NOT_RUN", "Inventory mode did not execute partial analog simulations") for name, kind, *_ in PARTIAL_SPICE_RUNNERS)
        stages.append(stage("isolated_edge_plant", "COMPILED_DISCONNECTED_IDEAL_MECHANICS_FIXTURE", "NOT_RUN", "Inventory mode did not compile the isolated mechanics fixture"))
        stages.append(stage("actual_cnc3_SPI_edge_plant", "ACTUAL_VERILATED_CNC3_SPI_PINS_IDEAL_MECHANICS", "NOT_RUN", "Inventory mode did not compile or execute the actual SPI/mechanics candidate"))
        stages.append(stage("seeded_actual_SPI_faults", "FRESH_VERILATED_2048_SEEDED_SERIAL_FAULTS_IDEAL_PROVIDERS", "NOT_RUN", "Inventory mode did not execute seeded serial fault trials"))
        stages.append(stage("bounded_IOL1_diagnostic_acquisition", "ACTUAL_C_TARGET_SPI_RTL_AGE_MUTATIONS_FAMILY_MAPPING", "NOT_RUN", "Inventory mode did not execute the diagnostic acquisition bundle"))
        stages.append(stage("bounded_IS2_CAP3_profile", "ACTUAL_COMPILED_C_RTL_SPI_DISCOVERY_FAIL_CLOSED_MUTATIONS", "NOT_RUN", "Inventory mode did not execute the incomplete IS2 profile discovery bundle"))
        stages.append(stage("bounded_CNC3_stateful_replay", "ACTUAL_CNC3_STATE_RATE_SPI_MUTATIONS_FAMILY_MAPPING", "NOT_RUN", "Inventory mode did not execute the eleven bounded stateful FPGA stages"))
    changed = differences(before, snapshot())
    if sha(board) != binding["board_sha256"]:
        changed[str(board)] = {"before": binding["board_sha256"], "after": sha(board)}
    for path, value in binding["report_local_component_inputs"].items():
        actual = sha(ROOT / path) if (ROOT / path).is_file() else None
        if actual != value:
            changed[path] = {"before": value, "after": actual}
    if changed:
        stages.append(stage("input_integrity", "EXACT_SOURCE_HASHES", "FAIL", "Inputs changed during run", changes=changed))
    else:
        stages.append(stage("input_integrity", "EXACT_SOURCE_HASHES", "PASS", "Scoped source and frozen PCB hashes retained"))
    status = result_status(stages, a.full)
    report = {"schema_version": 1, "started_from": binding, "finished_utc": utc(),
              "mode": "full" if a.full else "inventory", "status": status,
              "stages": stages, "status_counts": dict(Counter(s["status"] for s in stages)),
              "source_hashes_unchanged": not changed, "source_changes": changed,
              "original_source_file_count": len(before), "physical_measurements": False,
              "manufacturing_ready": False, "complete_machine_validation_passed": False,
              "historical_evidence_overwritten": False, "capabilities": caps}
    write(out / "report.json", report)
    step_receipt = out / "stepgen12-evidence/receipt.json"
    step_value = json.loads(step_receipt.read_text()) if step_receipt.is_file() else None
    if step_value and (step_value.get("status") != "PASS" or not step_value.get("source_hashes_unchanged")):
        step_value = None  # Failed evidence stays in the stage; it supplies no numerical limit.
    do_path = ROOT / "hardware/motherboard_do/design.json"
    do_data = json.loads(do_path.read_text(encoding="utf-8"))
    do_contract = {k: do_data[k] for k in ("continuous_limit_a_per_channel", "continuous_limit_a_per_quad")}
    do_contract["source_sha256"] = sha(do_path)
    encoder_path = out / "isolated_encoder4_sweep-evidence/receipt.json"
    encoder_value = json.loads(encoder_path.read_text()) if encoder_path.is_file() else None
    if encoder_value and encoder_value.get("passed") is not True:
        encoder_value = None
    write(out / "provisional-characterization.json", characterization(stages, binding["source_design_sha256"], binding["board_sha256"], step_value, do_contract, encoder_value))
    lines = ["# Disconnected pre-hardware validation", "", f"Overall: **{status}**. Manufacturing ready: **false**.", "",
             "| Stage | Status | Exact evidence class | Boundary |", "|---|---|---|---|"]
    lines += [f"| {s['name']} | {s['status']} | {s['evidence_type']} | {s['reason']} |" for s in stages]
    lines += ["", "Numerical production ratings remain null where complete chain/corners/fit/final-route qualification is absent. Host/model, actual RTL, target compilation, real LinuxCNC, native ERC/DRC and physical measurement are separate."]
    (out / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "status_counts": report["status_counts"], "report": str(out / "report.json"), "manufacturing_ready": False}))
    return 1 if status == "FAIL" else (2 if a.full else 0)


def guarded_main(argv=None):
    try:
        return main(argv)
    except Exception as exc:
        # A tool/staging exception is a failed bench, with all completed logs
        # preserved. It must never disappear as an unexplained missing report.
        out = CONTEXT.get("output")
        if out:
            before_path = out / "source-before.json"
            before = json.loads(before_path.read_text()) if before_path.is_file() else {}
            changes = differences(before, snapshot())
            write(out / "report.json", {"schema_version": 1, "status": "FAIL",
                  "execution_aborted": True, "stage_of_exception": CONTEXT.get("stage"),
                  "exception_type": type(exc).__name__, "reason": str(exc),
                  "source_hashes_unchanged": not changes, "source_changes": changes,
                  "manufacturing_ready": False, "complete_machine_validation_passed": False,
                  "completed_receipt_artifacts": [{"path": str(p), "sha256": sha(p)}
                       for p in out.rglob("receipt.json") if "inputs" not in p.parts]})
        print(json.dumps({"status": "FAIL", "exception": type(exc).__name__, "reason": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(guarded_main())
