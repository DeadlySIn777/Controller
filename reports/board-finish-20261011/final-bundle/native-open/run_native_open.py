"""Scheduled explicit-bundle native alias open; no selection, fill, DRC or save."""
import argparse
import json
import os
from pathlib import Path
import stat
import subprocess
import time

from open_check_shared import C05_SHA, PRO_SHA, DRU_SHA, sha, inventory, require, require_native_evidence, validate_report

HERE = Path(__file__).resolve().parent
WORK = HERE.parent.parent
EXTERNAL = Path("Z:/pcb-runs/claude-finish")


def write(path, obj):
    path.write_text(json.dumps(obj, indent=2) + "\n", encoding="utf-8")


def prepare(args):
    bundle, measure, out = args.bundle.resolve(), args.measure.resolve(), args.out.resolve()
    require(bundle.is_relative_to(HERE.parent) and bundle != HERE.parent, "Bundle must be an explicitly supplied isolated final-bundle child")
    require(out.is_relative_to(HERE) and out != HERE and not out.exists(), "Output must be a new native-open child")
    qualification_path = bundle / "qualification.json"
    qualification = json.loads(qualification_path.read_text(encoding="utf-8"))
    proof = json.loads((measure / "proof.json").read_text(encoding="utf-8"))
    status = json.loads((measure / "status.json").read_text(encoding="utf-8"))
    require_native_evidence(qualification, status, proof)
    require(Path(qualification["selection"]["measurement"]).resolve() == measure,
            "Bundle names a different native measurement")
    native = bundle / "native"
    alias_board, measured_board = native / "motherboard.kicad_pcb", measure / "copy/board.kicad_pcb"
    for directory, stem in ((native, "motherboard"), (measure / "copy", "board")):
        for extension, expected in ((".kicad_pcb", C05_SHA), (".kicad_pro", PRO_SHA), (".kicad_dru", DRU_SHA)):
            require(sha(directory / (stem + extension)) == expected, "Exact c05/project/rules input changed")
    for relative, record in qualification["bundle"]["manifest"].items():
        path = (bundle / relative).resolve()
        require(path.is_relative_to(bundle) and path != bundle and sha(path) == record["sha256"],
                "Final bundle manifest changed before native-open check: " + relative)
    original_meta = json.loads((native / "motherboard.kicad_pro").read_text())["meta"]["filename"]
    require(original_meta == "board.kicad_pro", "Original .pro meta.filename was altered for alias")
    wrapper = EXTERNAL / "tools/heavy.sh"
    binaries = [Path("C:/Program Files/KiCad/10.0/bin") / n for n in ("python.exe", "_pcbnew.dll", "kicad-cli.exe")]
    binaries.append(Path("C:/Program Files/KiCad/10.0/bin/Lib/site-packages/pcbnew.py"))
    qualified_runtime = qualification["project_binding"]["raw_receipt"]["runtime"]["installed_file_hashes"]
    require({str(path): sha(path) for path in binaries} == qualified_runtime,
            "Native-open runtime differs from final qualified project-binding runtime")
    inputs = {"scope": "read-only scheduled native alias open; explicit selected c05 bundle only",
         "candidate_sha256": C05_SHA, "bundle": str(bundle), "measurement": str(measure),
         "alias_board": str(alias_board), "measured_board": str(measured_board),
         "alias_directory_before_sha256": inventory(native), "measured_directory_before_sha256": inventory(measure / "copy"),
         "qualification_sha256": sha(qualification_path), "measurement_proof_sha256": sha(measure / "proof.json"),
         "measurement_status_sha256": sha(measure / "status.json"),
         "source_hashes": {str(path): sha(path) for path in (Path(__file__), HERE / "probe_native_open.py", HERE / "open_check_shared.py", wrapper)},
         "native_binary_hashes": {str(path): sha(path) for path in binaries}, "slot": "existing shared heavy.sh",
         "new_slots": 0, "new_gpu_jobs": 0, "native_refill_started": False, "native_drc_started": False,
         "board_saved": False, "project_saved": False, "GUI_started": False}
    out.mkdir(parents=True, exist_ok=False)
    write(out / "inputs.json", inputs)
    inputs["saved_inputs_sha256"] = sha(out / "inputs.json")
    return inputs, out, wrapper


def main():
    ap = argparse.ArgumentParser(description=__doc__)
    for name in ("bundle", "measure", "out"):
        ap.add_argument("--" + name, type=Path, required=True)
    args = ap.parse_args()
    inputs, out, wrapper = prepare(args)
    command = ["C:/Program Files/Git/usr/bin/sh.exe", wrapper.as_posix(), "kicad",
               "C:/Program Files/KiCad/10.0/bin/python.exe", (HERE / "probe_native_open.py").as_posix(),
               "--measured-board", inputs["measured_board"], "--alias-board", inputs["alias_board"],
               "--out", (out / "native-open.json").as_posix()]
    started = time.time()
    write(out / "invocation.json", {"command": command, "started_unix": started, "inputs_sha256": inputs["saved_inputs_sha256"],
                                   "slot": inputs["slot"], "new_slots": 0, "new_gpu_jobs": 0})
    env = os.environ.copy()
    env["PATH"] = "C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;" + env["PATH"]
    env.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
    with (out / "native-open.log").open("w", encoding="utf-8") as log:
        native = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    try:
        require(sha(out / "inputs.json") == inputs["saved_inputs_sha256"], "Saved native-open inputs changed")
        for group in ("source_hashes", "native_binary_hashes"):
            for path, expected in inputs[group].items():
                require(sha(path) == expected, "Source/native runtime changed during open check")
        require(inventory(Path(inputs["alias_board"]).parent) == inputs["alias_directory_before_sha256"]
                and inventory(Path(inputs["measured_board"]).parent) == inputs["measured_directory_before_sha256"],
                "Entire alias or measured input directory changed during native-open job")
        bundle, measure = Path(inputs["bundle"]), Path(inputs["measurement"])
        require(sha(bundle / "qualification.json") == inputs["qualification_sha256"]
                and sha(measure / "proof.json") == inputs["measurement_proof_sha256"]
                and sha(measure / "status.json") == inputs["measurement_status_sha256"],
                "Qualification or native measurement receipt changed")
        require(native.returncode == 0, "Native-open process exited " + str(native.returncode))
        raw_path = out / "native-open.json"
        require(raw_path.stat().st_mtime >= started - 1, "Native-open report predates invocation")
        report = json.loads(raw_path.read_text(encoding="utf-8"))
        require(report["probe_script_sha256"] == inputs["source_hashes"][str(HERE / "probe_native_open.py")], "Native-open producer differs")
        require(report["alias"]["directory_before_sha256"] == inputs["alias_directory_before_sha256"]
                and report["measured"]["directory_before_sha256"] == inputs["measured_directory_before_sha256"],
                "Native report starts from a different input directory state")
        result = validate_report(report)
        result.update(native_exit_code=native.returncode, elapsed_seconds=round(time.time() - started, 3),
                      native_report_sha256=sha(raw_path), bundle=inputs["bundle"], adopted=False, manufacturing_ready=False,
                      inputs_sha256=inputs["saved_inputs_sha256"])
        code = 0
    except (ValueError, TypeError, KeyError, OSError) as exc:
        result = {"verdict": "INVALID_OR_FAIL", "reason": str(exc), "native_exit_code": native.returncode,
                  "elapsed_seconds": round(time.time() - started, 3), "adopted": False, "manufacturing_ready": False}
        code = 1
    write(out / "receipt.json", result)
    print(json.dumps(result))
    return code


if __name__ == "__main__":
    raise SystemExit(main())
