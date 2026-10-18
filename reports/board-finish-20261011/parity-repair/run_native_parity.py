"""Scheduled source/native API parity; no refill, DRC, board save or adoption."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import re
import subprocess
import time

from prepare_parity import HERE, EXTERNAL, freeze, sha, write
from project_clone import clone_project, verify_clone


def verify_frozen(out, board):
    inputs = json.loads((out / "inputs.json").read_text(encoding="utf-8"))
    if inputs["host_parity"] != "PASS" or inputs["source_component_identity"] != "PASS":
        raise ValueError("Portable source precheck did not pass")
    if sha(board) != inputs["board_sha256"]:
        raise ValueError("Requested board differs from frozen candidate")
    for name, digest in inputs["snapshots"].items():
        target = (out / name).resolve()
        if not target.is_relative_to(out) or not re.fullmatch(r"[0-9a-f]{64}", digest):
            raise ValueError("Invalid frozen snapshot identity")
        if sha(target) != digest:
            raise ValueError("Frozen snapshot changed: " + name)
    if sha(out / "board.kicad_pcb") != inputs["board_sha256"] or sha(out / "source/sch.net") != inputs["netlist_sha256"]:
        raise ValueError("Frozen board or export does not match receipt")
    return inputs


def gate_report(report, inputs, host):
    if report.get("tool") != "netlist_parity":
        raise ValueError("Unexpected native report tool")
    if report["inputs"]["board"]["sha256"] != inputs["board_sha256"]:
        raise ValueError("Native report board hash differs")
    if report["inputs"]["netlist"]["sha256"] != inputs["netlist_sha256"]:
        raise ValueError("Native report export hash differs")
    summary = report["summary"]
    required_zero = ["parity_defects", "components_missing_on_board", "board_extra_unexpected",
                     "footprint_id_mismatch", "footprint_id_mismatch_case_only", "value_mismatch",
                     "duplicate_refs", "pad_net_mismatch", "netlist_nodes_without_board_pad",
                     "board_pads_without_netlist_node_with_net", "board_pads_unnumbered_with_net",
                     "netlist_nets_without_board_pads", "board_nets_with_pads_not_in_netlist",
                     "net_membership_differences", "normalisation_collisions", "pads_no_net_touched_by_track_or_via"]
    if any(type(summary.get(k)) is not int or summary[k] != 0 for k in required_zero):
        raise ValueError("Native parity defects or invalid result counts")
    if summary.get("status") != "parity_ok":
        raise ValueError("Native parity status is not parity_ok")
    if report["pads"].get("netlist_node_conflicts") != []:
        raise ValueError("Native report has contradictory node assignments")
    for native, portable in [("netlist_components", "netlist_components"), ("netlist_nets", "netlist_nets"),
                             ("netlist_nodes", "netlist_nodes"), ("board_footprints", "board_footprints"),
                             ("board_pads", "board_pads"), ("pads_matched", "physical_pads_matched")]:
        if type(summary.get(native)) is not int or summary[native] != host[portable]:
            raise ValueError("Native and portable inventory counts differ: " + native)
    return {"verdict": "PASS", "evidence_class": "source/native API netlist parity using pcbnew LoadBoard; no connectivity rebuild, refill or DRC",
            "board_sha256": inputs["board_sha256"], "netlist_sha256": inputs["netlist_sha256"],
            "summary": summary, "cli_schematic_parity": "NOT ESTABLISHED by this API parity check",
            "adopted": False, "limits": "No fresh schematic export, routing/DRC, electrical, timing or physical qualification"}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--board", required=True, type=Path)
    ap.add_argument("--out", required=True, type=Path)
    ap.add_argument("--expected-board-sha256")
    ap.add_argument("--with-project", action="store_true")
    ap.add_argument("--slot", choices=["test", "shared", "main"], default="test")
    args = ap.parse_args()
    out, board = args.out.resolve(), args.board.resolve()
    if not out.is_relative_to(HERE) or out == HERE:
        raise ValueError("Output must be an isolated parity-repair child")
    if not out.exists():
        freeze(out, board, args.expected_board_sha256)
    if (out / "native-parity.json").exists() or (out / "native-invocation.json").exists():
        raise ValueError("Native parity output already exists; choose a new output")
    inputs = verify_frozen(out, board)
    if args.expected_board_sha256 and inputs["board_sha256"] != args.expected_board_sha256:
        raise ValueError("Requested board hash differs")
    clone = clone_project(out) if args.with_project else None
    native_board = out / "native-project/board.kicad_pcb" if clone else out / "board.kicad_pcb"
    wrapper = EXTERNAL / ("tools/" + {"test": "heavyt.sh", "shared": "heavy.sh", "main": "heavym.sh"}[args.slot])
    wrapper_sha = sha(wrapper)
    started = time.time()
    entry = [str(HERE / "native_bound_entry.py"), (out / "tools/netlist_parity.py").as_posix()] if clone else [(out / "tools/netlist_parity.py").as_posix()]
    command = ["C:/Program Files/Git/usr/bin/sh.exe", wrapper.as_posix(), "kicad",
               "C:/Program Files/KiCad/10.0/bin/python.exe", *entry,
               native_board.as_posix(), "--netlist", (out / "source/sch.net").as_posix(),
               "--no-connectivity", "--examples", "40", (out / "native-parity.json").as_posix()]
    write(out / "native-invocation.json", {"phase": "WAITING_OR_RUNNING_TEST_SLOT", "command": command,
          "started_unix": started, "slot": args.slot + " KiCad", "slot_wrapper_sha256": wrapper_sha,
          "runner_sha256": sha(__file__), "new_gpu_jobs": 0, "adopted": False})
    env = os.environ.copy()
    env["PATH"] = "C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;" + env["PATH"]
    env.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
    with (out / "native-parity.log").open("w", encoding="utf-8") as log:
        run = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    ended = time.time()
    try:
        if run.returncode != 0:
            raise ValueError("Native API tool exited " + str(run.returncode))
        report_path = out / "native-parity.json"
        if report_path.stat().st_mtime < started - 1:
            raise ValueError("Native report predates invocation")
        verify_frozen(out, board)
        if clone:
            verify_clone(out, clone)
        if sha(wrapper) != wrapper_sha:
            raise ValueError("Slot wrapper changed during native check")
        report = json.loads(report_path.read_text(encoding="utf-8"))
        host = json.loads((out / "host-parity.json").read_text(encoding="utf-8"))
        result = gate_report(report, inputs, host)
        if clone and report.get("project_settings_binding", {}).get("explicit_board_set_project") is not True:
            raise ValueError("Explicit native project binding was not established")
        result.update(native_tool_exit_code=run.returncode, elapsed_seconds=round(ended - started, 3),
                      native_report_sha256=sha(report_path), frozen_inputs_verified_after=True,
                      project_settings_binding=report.get("project_settings_binding"),
                      project_clone_verified_after=bool(clone), slot=args.slot)
        code = 0
    except (OSError, ValueError, KeyError, TypeError) as exc:
        result = {"verdict": "INVALID_OR_FAIL", "reason": str(exc), "native_tool_exit_code": run.returncode,
                  "elapsed_seconds": round(ended - started, 3), "adopted": False}
        code = 1
    write(out / "native-receipt.json", result)
    print(json.dumps({k: v for k, v in result.items() if k != "summary"}))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
