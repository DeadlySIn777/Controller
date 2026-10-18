"""Measure the distinct c04 four-net E1 extension with unchanged native rules."""
import argparse
import datetime
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import traceback

STAGE = Path(__file__).resolve().parent
HERE = STAGE.parent.parent
PREVIOUS = HERE.parent / "routing-resume-20261011"
sys.path.insert(0, str(PREVIOUS))
import importlib.util
guard_spec = importlib.util.spec_from_file_location("composite_partition_guard", HERE / "gate-repair/partition_guard.py")
guard_module = importlib.util.module_from_spec(guard_spec)
guard_spec.loader.exec_module(guard_module)
compare, check_board = guard_module.compare, guard_module.check_board
from finish_bridge_proof import (ReadSet, digest, manifest, library_inventory,
                                 footprint_fingerprint, check_summary, PROJECT_NAMES, require)
sys.path.insert(0, str(STAGE))
from compose_c04 import validate_construction

ROOT = Path("Z:/pcb-runs/claude-finish")
TOOL_NAMES = ("step_measure.sh", "step_summary.py", "net_partitions.py", "heavym.sh")
NATIVE_BINARIES = {
    "kicad_cli": Path("C:/Program Files/KiCad/10.0/bin/kicad-cli.exe"),
    "native_python": Path("C:/Program Files/KiCad/10.0/bin/python.exe"),
    "pcbnew_python": Path("C:/Program Files/KiCad/10.0/bin/Lib/site-packages/pcbnew.py"),
    "pcbnew_extension": Path("C:/Program Files/KiCad/10.0/bin/Lib/site-packages/_pcbnew.pyd"),
}


def write(path, value):
    tmp = path.with_suffix(path.suffix + ".part")
    tmp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    tmp.replace(path)


def status(out, phase, **extra):
    record = {"phase": phase, "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "pid": os.getpid(), "adopted": False, **extra}
    write(out / "status.json", record)
    print(json.dumps(record), flush=True)


def binary_identities(reads):
    identities = {}
    for role, path in NATIVE_BINARIES.items():
        require(path.is_file(), "expected native binary unavailable: " + str(path))
        identities[role] = {"path": str(path.resolve()), "sha256": digest(reads.read(path))}
    return identities


def verify_inputs(out, inputs, inputs_sha256, reads):
    raw = reads.read(out / "inputs.json")
    require(digest(raw) == inputs_sha256, "saved inputs.json bytes changed during native run")
    require(json.loads(raw) == inputs, "saved inputs.json disagrees with run inputs")
    require(binary_identities(reads) == inputs["native_binaries"], "native binary identity changed during run")


def evaluate(args, inputs, inputs_sha256):
    out, bm = args.out, args.before_measure
    reads = ReadSet()
    verify_inputs(out, inputs, inputs_sha256, reads)
    boards = {"before": reads.read(args.before_board), "after": reads.read(args.candidate)}
    for role in boards:
        require(digest(boards[role]) == inputs[role + "_sha256"], "source board changed during native run")
    construction = validate_construction(args.construction, args.candidate)
    require(reads.read(args.construction) == reads.read(out / "construction.json"), "construction receipt changed")
    for path, expected in inputs["construction_file_hashes"].items():
        require(digest(reads.read(path)) == expected, "construction input changed: " + path)
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
    cli_log = reads.read(out / "drc.log").decode("utf-8", errors="replace")
    cli_parity = ("NOT_EXECUTED" if "Failed to fetch schematic netlist" in cli_log
                  or "Schematic parity tests require" in cli_log else "NO_REPORTED_DIAGNOSTIC; execution needs independent source/API proof")
    validate_construction(args.construction, args.candidate)
    reads.verify()
    passed = guard["verdict"] == "PASS" and drcs["after"]["errors"] == 0
    return {"verdict": "PASS" if passed else "FAIL", "adopted": False, "manufacturing_ready": False,
            "candidate_sha256": inputs["after_sha256"], "connectivity": guard, "drc": drcs,
            "inputs_sha256": inputs_sha256, "native_binaries": inputs["native_binaries"],
            "footprints": footprints["after"], "project_hashes": manifests["after"],
            "exact_reconstructed_source_contract": construction,
            "cli_schematic_parity": cli_parity,
            "explicit_native_netlist_parity": "SEPARATE_SAME_HASH_RECEIPT_REQUIRED",
            "observed_file_hashes": reads.hashes, "evidence_class": "native KiCad refill/DRC/connectivity",
            "limits": ["No electrical/current/thermal/SI or physical qualification",
                       "Native unconnected report is capped; use uncapped pad partitions/API",
                       "Final manufacture and source adoption gates remain open"]}


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("before-board", "before-measure", "candidate", "out"):
        ap.add_argument("--" + name, type=Path, required=True)
    ap.add_argument("--construction", type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    try:
        construction = validate_construction(args.construction, args.candidate)
        receipt = json.loads(args.construction.read_text(encoding="utf-8"))
        require(digest(args.before_board.read_bytes()) == receipt["base_bindings"]["native_sources"]["r06"]["sha256"], "baseline is not approved r06")
        records = []
        def collect(value):
            if isinstance(value, dict):
                if {"path", "sha256"} <= set(value):
                    records.append(value)
                else:
                    for item in value.values(): collect(item)
            elif isinstance(value, list):
                for item in value: collect(item)
        collect(receipt)
        construction_hashes = {str(Path(r["path"]).resolve()): r["sha256"] for r in records}
        for path, expected in construction_hashes.items():
            require(digest(Path(path).read_bytes()) == expected, "construction binding changed")
        (args.out / "construction.json").write_bytes(args.construction.read_bytes())
        sources = [ROOT / "tools" / n for n in TOOL_NAMES] + [Path(__file__), HERE / "compose_additions.py",
                   HERE / "gate-repair/partition_guard.py", PREVIOUS / "finish_bridge_proof.py",
                   ROOT / "tools/integrate/pcbtext.py", HERE / "recovery-composite/compose_recovery.py",
                   HERE / "reconcile_dfm.py", HERE / "dfm_contract_v2.py", STAGE / "compose_c04.py"]
        require(len({p.name for p in sources}) == len(sources), "source snapshot names collide")
        (args.out / "sources").mkdir()
        for p in sources:
            (args.out / "sources" / p.name).write_bytes(p.read_bytes())
        for name in ("partitions.json", "summary.json", "sha256.txt", "drc.json"):
            (args.out / ("baseline-" + name)).write_bytes((args.before_measure / name).read_bytes())
        initial_reads = ReadSet()
        libs = library_inventory(args.before_measure / "copy", initial_reads)
        native_binaries = binary_identities(initial_reads)
        initial_reads.verify()
        inputs = {"before_sha256": digest(args.before_board.read_bytes()),
                  "after_sha256": digest(args.candidate.read_bytes()),
                  "before_board": str(args.before_board.resolve()), "after_board": str(args.candidate.resolve()),
                  "tools": {str(p): digest(p.read_bytes()) for p in sources},
                  "library_inventory_at_start": libs, "slot": "main-kicad (one, isolated copy)", "new_gpu_jobs": 0,
                  "native_binaries": native_binaries,
                  "construction_file_hashes": construction_hashes, "construction_check": construction}
        check_board(json.loads((args.out / "baseline-partitions.json").read_text()), args.before_board)
        write(args.out / "inputs.json", inputs)
        inputs_sha256 = digest((args.out / "inputs.json").read_bytes())
        env = os.environ.copy()
        env["HEAVY"] = "heavym.sh"
        env["PATH"] = "C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;" + env["PATH"]
        env.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
        status(args.out, "NATIVE_MEASUREMENT_RUNNING", candidate_sha256=inputs["after_sha256"])
        with (args.out / "measure.log").open("w", encoding="utf-8") as log:
            cmd = ["C:/Program Files/Git/usr/bin/sh.exe", str(ROOT / "tools/step_measure.sh"),
                   args.candidate.resolve().as_posix(), args.out.resolve().as_posix(), (STAGE / "inputs/project").resolve().as_posix()]
            result = subprocess.run(cmd, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
        require(result.returncode == 0, f"native measurement exited {result.returncode}")
        status(args.out, "EVALUATING_NATIVE_RECEIPTS")
        receipt = evaluate(args, inputs, inputs_sha256)
        write(args.out / "proof.json", receipt)
        status(args.out, "COMPLETE", verdict=receipt["verdict"], completed=receipt["connectivity"]["completed"],
               lost=receipt["connectivity"]["lost"], drc_errors=receipt["drc"]["after"]["errors"])
        return 0 if receipt["verdict"] == "PASS" else 1
    except Exception as exc:
        status(args.out, "FAILED", reason=str(exc), traceback=traceback.format_exc())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
