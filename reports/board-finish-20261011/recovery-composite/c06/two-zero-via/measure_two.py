"""Measure two pure-add r07 signals against both r07/live and r06 with unchanged native rules."""
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
HERE = STAGE.parent.parent.parent
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
from compose_two import validate_construction, R07_SHA

ROOT = Path("Z:/pcb-runs/claude-finish")
TOOL_NAMES = ("step_measure.sh", "step_summary.py", "net_partitions.py", "heavy.sh")
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


def combined_verdict(live_guard, r06_guard, drc_errors):
    return "PASS" if live_guard["verdict"] == "PASS" and r06_guard["verdict"] == "PASS" and drc_errors == 0 else "FAIL"


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
    for path, expected in inputs["baseline_file_hashes"].items():
        require(digest(reads.read(path)) == expected, "frozen baseline evidence changed: " + path)
    footprints = {role: footprint_fingerprint(data) for role, data in boards.items()}
    require(footprints["before"] == footprints["after"], "pure-add candidate changes footprints/pads/poses")
    b, a = reads.json(out / "baseline-partitions.json"), reads.json(out / "partitions.json")
    check_board(b, args.before_board)
    check_board(a, args.candidate)
    guard = compare(b, a)
    r06 = reads.json(out / "r06-partitions.json")
    check_board(r06, args.r06_board)
    r06_guard = compare(r06, a)
    require(digest(reads.read(args.r06_board)) == inputs["r06_sha256"], "r06 source board changed")
    require(digest(reads.read(args.live_board)) == inputs["before_sha256"], "actual live board changed")
    for name in ("partitions.json", "summary.json", "sha256.txt", "drc.json"):
        require(reads.read(out / ("r06-" + name)) == reads.read(args.r06_measure / name), "r06 evidence changed")
    r06_manifest = manifest(reads.read(out / "r06-sha256.txt"))
    require(r06_manifest["board.kicad_pcb"] == inputs["r06_sha256"], "r06 manifest board differs")
    for name in PROJECT_NAMES | {"board.kicad_pcb"}:
        require(digest(reads.read(args.r06_measure / "copy" / name)) == r06_manifest[name], "r06 measured copy changed")
    manifests = {"before": manifest(reads.read(out / "baseline-sha256.txt")),
                 "after": manifest(reads.read(out / "sha256.txt"))}
    for role, directory in (("before", bm / "copy"), ("after", out / "copy")):
        require(manifests[role]["board.kicad_pcb"] == inputs[role + "_sha256"], "manifest board differs")
        for name in PROJECT_NAMES | {"board.kicad_pcb"}:
            require(digest(reads.read(directory / name)) == manifests[role][name], "measured copy changed: " + name)
    for name in PROJECT_NAMES:
        require(manifests["before"][name] == manifests["after"][name] == r06_manifest[name], "native rules/source changed: " + name)
    for name in ("partitions.json", "summary.json", "sha256.txt", "drc.json"):
        require(reads.read(out / ("baseline-" + name)) == reads.read(bm / name), "baseline evidence changed")
    before_libs = library_inventory(bm / "copy", reads)
    after_libs = library_inventory(out / "copy", reads)
    require(before_libs == after_libs == library_inventory(args.r06_measure / "copy", reads), "effective footprint resources differ")
    require(after_libs == inputs["library_inventory_at_start"], "footprint resources changed during run")
    drcs = {}
    for role, prefix, parts in (("before", "baseline-", b), ("after", "", a)):
        drcs[role] = check_summary(reads.json(out / (prefix + "drc.json")), parts,
                                  reads.json(out / (prefix + "summary.json")), inputs[role + "_sha256"])
    require(drcs["before"]["kicad"] == drcs["after"]["kicad"], "KiCad versions differ")
    drcs["r06"] = check_summary(reads.json(out / "r06-drc.json"), r06,
                                reads.json(out / "r06-summary.json"), inputs["r06_sha256"])
    require(drcs["r06"]["kicad"] == drcs["after"]["kicad"], "r06 KiCad version differs")
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
    passed = combined_verdict(guard, r06_guard, drcs["after"]["errors"]) == "PASS"
    return {"verdict": "PASS" if passed else "FAIL", "adopted": False, "manufacturing_ready": False,
            "candidate_sha256": inputs["after_sha256"], "connectivity": guard, "connectivity_r07_live": guard, "connectivity_r06": r06_guard, "drc": drcs,
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
    for name in ("r06-board", "r06-measure", "live-board"):
        ap.add_argument("--" + name, type=Path, required=True)
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=False)
    try:
        construction = validate_construction(args.construction, args.candidate)
        receipt = json.loads(args.construction.read_text(encoding="utf-8"))
        require(digest(args.before_board.read_bytes()) == R07_SHA, "baseline is not frozen actual r07")
        require(digest(args.live_board.read_bytes()) == R07_SHA, "actual live board is not frozen r07")
        require(digest(args.r06_board.read_bytes()) == "0e90568af6efa53e8bb15b3de60dbc5d167c1ed84b013b07fa902762582cfe53", "r06 source differs")
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
        construction_hashes = dict(receipt["source_files_sha256"])
        for path, expected in construction_hashes.items():
            require(digest(Path(path).read_bytes()) == expected, "construction binding changed")
        (args.out / "construction.json").write_bytes(args.construction.read_bytes())
        sources = [ROOT / "tools" / n for n in TOOL_NAMES] + [Path(__file__), STAGE / "compose_two.py",
                   HERE / "compose_additions.py", HERE / "gate-repair/partition_guard.py",
                   PREVIOUS / "finish_bridge_proof.py", ROOT / "tools/integrate/pcbtext.py",
                   STAGE / "audit_two.py", STAGE.parent / "screen_c06.py", STAGE.parent / "screen_dive_c06.py",
                   STAGE.parent / "alternate-r07/screen_r07.py", HERE / "reconcile_dfm.py",
                   HERE / "power-audit/prepare_sbc_c05_proposal.py", HERE / "power-audit/prepare_sbc_plan.py",
                   HERE / "power-audit/prepare_sbc_hubs.py"]
        require(len({p.name for p in sources}) == len(sources), "source snapshot names collide")
        (args.out / "sources").mkdir()
        for p in sources:
            (args.out / "sources" / p.name).write_bytes(p.read_bytes())
        for name in ("partitions.json", "summary.json", "sha256.txt", "drc.json"):
            (args.out / ("baseline-" + name)).write_bytes((args.before_measure / name).read_bytes())
            (args.out / ("r06-" + name)).write_bytes((args.r06_measure / name).read_bytes())
        initial_reads = ReadSet()
        libs = library_inventory(args.before_measure / "copy", initial_reads)
        native_binaries = binary_identities(initial_reads)
        baseline_file_hashes = {}
        for directory in (args.before_measure, args.r06_measure):
            paths = [directory / name for name in ("partitions.json", "summary.json", "sha256.txt", "drc.json")]
            paths += [directory / "copy" / name for name in PROJECT_NAMES | {"board.kicad_pcb"}]
            for path in paths:
                baseline_file_hashes[str(path.resolve())] = digest(initial_reads.read(path))
        initial_reads.verify()
        inputs = {"before_sha256": digest(args.before_board.read_bytes()),
                  "after_sha256": digest(args.candidate.read_bytes()),
                  "r06_sha256": digest(args.r06_board.read_bytes()),
                  "live_board": str(args.live_board.resolve()),
                  "before_board": str(args.before_board.resolve()), "after_board": str(args.candidate.resolve()),
                  "tools": {str(p): digest(p.read_bytes()) for p in sources},
                  "library_inventory_at_start": libs, "slot": "shared-kicad (one, isolated copy)", "new_gpu_jobs": 0,
                  "native_binaries": native_binaries,
                  "baseline_file_hashes": baseline_file_hashes,
                  "construction_file_hashes": construction_hashes, "construction_check": construction}
        check_board(json.loads((args.out / "baseline-partitions.json").read_text()), args.before_board)
        check_board(json.loads((args.out / "r06-partitions.json").read_text()), args.r06_board)
        write(args.out / "inputs.json", inputs)
        inputs_sha256 = digest((args.out / "inputs.json").read_bytes())
        env = os.environ.copy()
        env["HEAVY"] = "heavy.sh"
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
               lost=receipt["connectivity"]["lost"], r06_lost=receipt["connectivity_r06"]["lost"], drc_errors=receipt["drc"]["after"]["errors"])
        return 0 if receipt["verdict"] == "PASS" else 1
    except Exception as exc:
        status(args.out, "FAILED", reason=str(exc), traceback=traceback.format_exc())
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
