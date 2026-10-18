"""Measure an isolated additive board with unchanged native rules and no-loss gate."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

HERE = Path(__file__).resolve().parent
PREVIOUS = HERE.parent / "routing-resume-20261011"
sys.path.insert(0, str(PREVIOUS))
from partition_guard import compare, check_board
from finish_bridge_proof import (ReadSet, digest, manifest, library_inventory,
                                 footprint_fingerprint, check_summary, PROJECT_NAMES, require)
from compose_additions import inventory
from reconcile_dfm import validate as validate_dfm

ROOT = Path("Z:/pcb-runs/claude-finish")
TOOL_NAMES = ("step_measure.sh", "step_summary.py", "net_partitions.py", "heavym.sh")


def write(path, value):
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def status(out, phase, **extra):
    record = {"phase": phase, "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "pid": os.getpid(), "adopted": False, **extra}
    write(out / "status.json", record)
    print(json.dumps(record), flush=True)


def evaluate(args, inputs):
    out, bm = args.out, args.before_measure
    reads = ReadSet()
    boards = {"before": reads.read(args.before_board), "after": reads.read(args.candidate)}
    for role in boards:
        require(digest(boards[role]) == inputs[role + "_sha256"], "source board changed during native run")
    dfm_contract = validate_dfm(boards["before"], boards["after"])
    footprints = {role: footprint_fingerprint(data) for role, data in boards.items()}
    require(footprints["before"]["count"] == footprints["after"]["count"], "footprint counts differ")
    b, a = reads.json(out / "baseline-partitions.json"), reads.json(out / "partitions.json")
    check_board(b, args.before_board)
    check_board(a, args.candidate)
    guard = compare(b, a)
    manifests = {"before": manifest(reads.read(out / "baseline-sha256.txt")),
                 "after": manifest(reads.read(out / "sha256.txt"))}
    for role, directory in (("before", bm / "copy"), ("after", out / "copy")):
        require(manifests[role]["board.kicad_pcb"] == inputs[role + "_sha256"], "manifest board differs")
        for name in PROJECT_NAMES | {"board.kicad_pcb"}:
            require(digest(reads.read(directory / name)) == manifests[role][name], "measured copy changed: " + name)
    for name in PROJECT_NAMES:
        require(manifests["before"][name] == manifests["after"][name], "native rules/source changed: " + name)
    for name in ("partitions.json", "summary.json", "sha256.txt", "drc.json"):
        require(reads.read(out / ("baseline-" + name)) == reads.read(bm / name), "baseline evidence changed")
    before_libs = library_inventory(bm / "copy", reads)
    after_libs = library_inventory(out / "copy", reads)
    require(before_libs == after_libs, "effective footprint resources differ")
    require(after_libs == inputs["library_inventory_at_start"], "footprint resources changed during run")
    drcs = {}
    for role, prefix, parts in (("before", "baseline-", b), ("after", "", a)):
        drcs[role] = check_summary(reads.json(out / (prefix + "drc.json")), parts,
                                  reads.json(out / (prefix + "summary.json")), inputs[role + "_sha256"])
    require(drcs["before"]["kicad"] == drcs["after"]["kicad"], "KiCad versions differ")
    for path, expected in inputs["tools"].items():
        require(digest(reads.read(path)) == expected, "tool changed during native run: " + path)
        require(digest(reads.read(out / "sources" / Path(path).name)) == expected, "tool snapshot differs")
    start = (out / "inputs.json").stat().st_mtime_ns
    for name in ("partitions.json", "drc.json", "summary.json", "sha256.txt"):
        require((out / name).stat().st_mtime_ns >= start, "receipt predates this native run")
    reads.verify()
    passed = guard["verdict"] == "PASS" and drcs["after"]["errors"] == 0
    return {"verdict": "PASS" if passed else "FAIL", "adopted": False,
            "candidate_sha256": inputs["after_sha256"], "connectivity": guard, "drc": drcs,
            "footprints": footprints["after"], "project_hashes": manifests["after"],
            "baseline_copper_retained_exact": True, "approved_dfm_changes": dfm_contract,
            "observed_file_hashes": reads.hashes, "evidence_class": "native KiCad refill/DRC/connectivity",
            "limits": ["No electrical/current/thermal/SI or physical qualification",
                       "Native unconnected report is capped; use uncapped pad partitions/API",
                       "Final manufacture and source adoption gates remain open"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("before-board", "before-measure", "candidate", "out"):
        ap.add_argument("--" + name, type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    try:
        validate_dfm(args.before_board.read_bytes(), args.candidate.read_bytes())
        sources = [ROOT / "tools" / n for n in TOOL_NAMES] + [Path(__file__), HERE / "compose_additions.py",
                   PREVIOUS / "partition_guard.py", PREVIOUS / "finish_bridge_proof.py",
                   ROOT / "tools/integrate/pcbtext.py", HERE / "reconcile_dfm.py"]
        (args.out / "sources").mkdir()
        for p in sources:
            (args.out / "sources" / p.name).write_bytes(p.read_bytes())
        for name in ("partitions.json", "summary.json", "sha256.txt", "drc.json"):
            (args.out / ("baseline-" + name)).write_bytes((args.before_measure / name).read_bytes())
        initial_reads = ReadSet()
        libs = library_inventory(args.before_measure / "copy", initial_reads)
        initial_reads.verify()
        inputs = {"before_sha256": digest(args.before_board.read_bytes()),
                  "after_sha256": digest(args.candidate.read_bytes()),
                  "before_board": str(args.before_board.resolve()), "after_board": str(args.candidate.resolve()),
                  "tools": {str(p): digest(p.read_bytes()) for p in sources},
                  "library_inventory_at_start": libs, "slot": "main-kicad (one, idle integration slot; no live mutation)", "new_gpu_jobs": 0}
        check_board(json.loads((args.out / "baseline-partitions.json").read_text()), args.before_board)
        write(args.out / "inputs.json", inputs)
        env = os.environ.copy()
        env["HEAVY"] = "heavym.sh"
        env["PATH"] = "C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;" + env["PATH"]
        env.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
        status(args.out, "NATIVE_MEASUREMENT_RUNNING", candidate_sha256=inputs["after_sha256"])
        with (args.out / "measure.log").open("w", encoding="utf-8") as log:
            cmd = ["C:/Program Files/Git/usr/bin/sh.exe", str(ROOT / "tools/step_measure.sh"),
                   args.candidate.resolve().as_posix(), args.out.resolve().as_posix(), (ROOT / "integrate").as_posix()]
            result = subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
        require(result.returncode == 0, f"native measurement exited {result.returncode}")
        status(args.out, "EVALUATING_NATIVE_RECEIPTS")
        receipt = evaluate(args, inputs)
        write(args.out / "proof.json", receipt)
        status(args.out, "COMPLETE", verdict=receipt["verdict"], completed=receipt["connectivity"]["completed"],
               lost=receipt["connectivity"]["lost"], drc_errors=receipt["drc"]["after"]["errors"])
        return 0 if receipt["verdict"] == "PASS" else 1
    except Exception as exc:
        status(args.out, "FAILED", reason=str(exc), traceback=traceback.format_exc())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
