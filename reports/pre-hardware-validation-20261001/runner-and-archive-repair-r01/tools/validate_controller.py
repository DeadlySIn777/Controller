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
          "controller_lab", "firmware", "gateware", "cnc1", "config", "hardware")
SKIP = {"__pycache__", ".git", "node_modules", "build", "dist", "evidence",
        "results", "before-audit-fixes-2026-09-28", "board_review"}
EXTENSIONS = {".py", ".sh", ".c", ".cpp", ".h", ".v", ".sv", ".ys", ".json",
              ".ini", ".hal", ".xml", ".csv", ".kicad_sch", ".kicad_mod",
              ".kicad_pcb", ".kicad_pro", ".kicad_dru", ".kicad_sym"}
KICAD = Path("C:/Program Files/KiCad/10.0/bin")
EXTERNAL = Path("C:/Users/Gluis/claude-worktrees/controller-interface-spec")
LAB_ROOTFS = "/root/.cache/controller-lab-linuxcnc/rootfs"


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
            if p.is_file() and p.suffix in EXTENSIONS
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


def capability_inventory(out, distro):
    script = out / "capability-inventory.sh"
    script.write_text("#!/bin/sh\nset -u\n"
        "for t in python3 gcc g++ clang ld.lld iverilog vvp verilator ngspice efx_run; do\n"
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
    return {p.relative_to(source).as_posix(): sha(source / p.relative_to(dest))
            for p in dest.rglob("*") if p.is_file()}


def cnc3_host(out, external, distro):
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
         "Frozen CNC3 is a host codec/core and behavioral endpoint model; actual CNC3 RTL, HAL/Verilated transport and integrated machine profile are absent"),
        ("twelve_joint_simultaneous_machine", "SIMULATED_FULL_MACHINE",
         "No integrated twelve-joint CNC3/RTL/mechanics/encoder/full-I/O machine; standalone step generators do not implement it"),
        ("critical_circuit_spice_corners", "SPICE_CORNER_MONTE_CARLO",
         "No selected-part-complete SPICE benches/models; ngspice availability alone would not qualify them"),
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


def characterization(stages, source_hash, board_hash, stepgen=None, do_contract=None):
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
    before = snapshot()
    write(out / "source-before.json", before)
    board = (a.board or public_board()).resolve()
    source = ROOT / "hardware/motherboard"
    binding = {"source_design": str(source / "design.json"),
               "source_design_sha256": sha(source / "design.json"),
               "source_netlist_sha256": sha(source / "netlist.xml"),
               "board": str(board), "board_sha256": sha(board),
               "runner_sha256": sha(Path(__file__))}
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
                artifact=out / "erc.json", predicate=lambda v: not v.get("ignored_checks") and not any(r["severity"] == "error" for r in v["violations"])))
            stages.append(command_stage("native_DRC", "NATIVE_KICAD_DRC", [a.kicad_cli, "pcb", "drc", "--format", "json", "--all-track-errors", "--severity-all", "--output", out / "drc.json", board], out,
                artifact=out / "drc.json", predicate=lambda v: not v.get("ignored_checks") and not v["violations"]))
            for name, file in (("native_ERC", "erc.json"), ("native_DRC", "drc.json")):
                if (out / file).is_file():
                    try:
                        value = json.loads((out / file).read_text(encoding="utf-8"))
                        row = next(s for s in stages if s["name"] == name)
                        row.update(unsuppressed_violations=dict(Counter(v["severity"] for v in value["violations"])),
                                   ignored_checks=value.get("ignored_checks", []),
                                   complete_routing_qualified=False)
                    except (ValueError, KeyError, TypeError):
                        pass  # Malformed evidence is already a failed command_stage.
        else:
            stages.extend(stage(name, kind, "BLOCKED", "Native KiCad CLI unavailable") for name, kind in (
                ("native_ERC", "NATIVE_KICAD_ERC"), ("native_DRC", "NATIVE_KICAD_DRC")))
        if a.native_python.is_file():
            stages.append(command_stage("source_physical_connectivity", "NATIVE_SOURCE_CLUSTER_INDEPENDENT_COUNT", [a.native_python, "-X", "utf8", "tools/motion_card_routing_inventory.py", "--board", board, "--netlist", source / "netlist.xml", "--source-design", source / "design.json", "--out", out / "connectivity"], out,
                artifact=out / "connectivity/review.json", predicate=lambda v: v["source_net_checks_pass"] and v["complete_source_population_pass"]))
            if (out / "connectivity/review.json").is_file():
                remaining = json.loads((out / "connectivity/review.json").read_text())["independent_physical_cluster_missing_joins"]
                stages.append(stage("complete_PCB_routing", "NATIVE_PHYSICAL_CONNECTIVITY", "BLOCKED" if remaining else "PASS", f"{remaining} uncapped Source-cluster joins remain", missing_joins=remaining))
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
        if caps.get("ROOTFS:gcc") and (a.external_cnc3 / "cnc3/tools/host_tests_rootfs.sh").is_file():
            if all((a.external_cnc3 / p).is_dir() for p in ("cnc3", "spec", "gateware/v3")):
                stages.append(cnc3_layout(out, a.external_cnc3))
            else:
                stages.append(stage("cnc3_layout_contract", "GENERATED_C_PROTOCOL_LAYOUT_CHECK", "BLOCKED", "Complete frozen layout sources absent"))
            stages.append(cnc3_host(out, a.external_cnc3, a.wsl_distro))
        else:
            stages.append(stage("cnc3_host_model", "HOST_C_MODEL", "BLOCKED", "Frozen external host source or isolated compiler absent"))
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
            ("isolated_stepgen12_sweep", "ACTUAL_RTL_FAILURE_BOUNDARY_SWEEP"), ("supervisor_fault_scenarios", "HOST_SUPERVISOR_MODEL"),
            ("IOL1_target", "TARGET_COMPILATION")))
    changed = differences(before, snapshot())
    if sha(board) != binding["board_sha256"]:
        changed[str(board)] = {"before": binding["board_sha256"], "after": sha(board)}
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
    if step_value and step_value.get("status") != "PASS":
        step_value = None  # Failed evidence stays in the stage; it supplies no numerical limit.
    do_path = ROOT / "hardware/motherboard_do/design.json"
    do_data = json.loads(do_path.read_text(encoding="utf-8"))
    do_contract = {k: do_data[k] for k in ("continuous_limit_a_per_channel", "continuous_limit_a_per_quad")}
    do_contract["source_sha256"] = sha(do_path)
    write(out / "provisional-characterization.json", characterization(stages, binding["source_design_sha256"], binding["board_sha256"], step_value, do_contract))
    lines = ["# Disconnected pre-hardware validation", "", f"Overall: **{status}**. Manufacturing ready: **false**.", "",
             "| Stage | Status | Exact evidence class | Boundary |", "|---|---|---|---|"]
    lines += [f"| {s['name']} | {s['status']} | {s['evidence_type']} | {s['reason']} |" for s in stages]
    lines += ["", "Numerical production ratings remain null where complete chain/corners/fit/final-route qualification is absent. Host/model, actual RTL, target compilation, real LinuxCNC, native ERC/DRC and physical measurement are separate."]
    (out / "README.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"status": status, "status_counts": report["status_counts"], "report": str(out / "report.json"), "manufacturing_ready": False}))
    return 1 if status == "FAIL" else (2 if a.full else 0)


if __name__ == "__main__":
    raise SystemExit(main())
