"""Resume only the missing native In3 candidate proof; never adopt copper."""
import datetime
import hashlib
import json
import os
import subprocess
import traceback
from pathlib import Path

from partition_guard import compare, check_board

ROOT = Path("Z:/pcb-runs/claude-finish")
HERE = Path(__file__).resolve().parent
OUT = HERE / "bridge-native"
CANDIDATE = ROOT / "agent-work/test-bridges3/applied.kicad_pcb"
BASELINE = ROOT / "integrate/revs/r05-stitch-plane-pads-1.kicad_pcb"
BEFORE = ROOT / "integrate/measure/r05-stitch-plane-pads-1"
EXPECTED = {CANDIDATE: "c28f6c9410cbf0b9bee8f7f1931ad78cffe30a03b401aeb102dc91c35650724e",
            BASELINE: "594a1091d3a0eade7bff5d4fb83418f10640004afd36119faab92a3886f9e6c2"}
SOURCES = [ROOT / ("tools/" + name) for name in
           ("step_measure.sh", "step_summary.py", "net_partitions.py", "heavyt.sh",
            "corridor_router_in3sv3.py")]


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def write(path, value):
    temp = path.with_suffix(path.suffix + ".part")
    temp.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    temp.replace(path)


def status(phase, **extra):
    record = {"phase": phase, "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
              "pid": os.getpid(), "adoption": False, **extra}
    write(HERE / "bridge-status.json", record)
    print(json.dumps(record), flush=True)


def main():
    if (HERE / "bridge-status.json").exists():
        raise RuntimeError("proof already has a status receipt; do not launch a duplicate")
    OUT.mkdir(exist_ok=False)
    for path, expected in EXPECTED.items():
        if sha(path) != expected:
            raise ValueError(f"source board changed: {path}")
    frozen = {str(p): sha(p) for p in SOURCES}
    for p in SOURCES:
        (OUT / p.name).write_bytes(p.read_bytes())
    for name in ("partitions.json", "summary.json", "sha256.txt"):
        (OUT / ("baseline-" + name)).write_bytes((BEFORE / name).read_bytes())
    write(OUT / "inputs.json", {"boards": {str(p): h for p, h in EXPECTED.items()}, "tools": frozen,
                               "slot": "test-kicad (one)", "new_gpu_jobs": 0,
                               "scope": "native KiCad DRC plus uncapped refilled connectivity; no physical measurement"})
    env = os.environ.copy()
    env["HEAVY"] = "heavyt.sh"
    env["PATH"] = "C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;" + env["PATH"]
    env.update(OMP_NUM_THREADS="2", MKL_NUM_THREADS="2", OPENBLAS_NUM_THREADS="2")
    status("NATIVE_MEASUREMENT_RUNNING", candidate_sha256=EXPECTED[CANDIDATE], output=str(OUT))
    with (OUT / "measure.log").open("w", encoding="utf-8") as log:
        command = ["C:/Program Files/Git/usr/bin/sh.exe", str(ROOT / "tools/step_measure.sh"),
                   CANDIDATE.as_posix(), OUT.as_posix(), (ROOT / "integrate").as_posix()]
        result = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    if result.returncode:
        raise RuntimeError(f"native measurement exited {result.returncode}; see bridge-native/measure.log")
    status("EVALUATING_NATIVE_RECEIPTS")
    before = json.loads((OUT / "baseline-partitions.json").read_text(encoding="utf-8"))
    after = json.loads((OUT / "partitions.json").read_text(encoding="utf-8"))
    guard = compare(before, after)
    check_board(before, BASELINE)
    check_board(after, CANDIDATE)
    for path, expected in EXPECTED.items():
        if sha(path) != expected:
            raise ValueError(f"source board changed while measuring: {path}")
    changed_tools = [str(p) for p in SOURCES if sha(p) != frozen[str(p)]]
    b = json.loads((OUT / "baseline-summary.json").read_text(encoding="utf-8"))
    a = json.loads((OUT / "summary.json").read_text(encoding="utf-8"))
    if b["board_sha256"] != before["sha256"] or a["board_sha256"] != after["sha256"]:
        raise ValueError("DRC/partition receipts refer to different board hashes")
    new_errors = {k: n - b["drc_by_category"].get(k, 0) for k, n in a["drc_by_category"].items()
                  if k.endswith("[error]") and n > b["drc_by_category"].get(k, 0)}
    drc_ok = not new_errors and a["drc_errors"] == 0 and b["drc_flags"] == a["drc_flags"]
    proof_ok = guard["verdict"] == "PASS" and drc_ok and not changed_tools
    receipt = {"verdict": "PASS" if proof_ok else "FAIL", "connectivity": guard,
               "drc_errors": a["drc_errors"], "drc_warnings_before": b["drc_warnings"],
               "drc_warnings_after": a["drc_warnings"], "new_error_categories": new_errors,
               "drc_flags": a["drc_flags"], "tools_changed_during_run": changed_tools,
               "adopted": False, "source": "r05 In3 bridge candidate only",
               "limits": ["CLI unconnected list is capped; use uncapped partition/API receipt",
                          "No electrical, current capacity, thermal, SI, manufacturing or physical proof",
                          "No application to r07 or the live power candidate"]}
    write(OUT / "proof.json", receipt)
    status("COMPLETE", verdict=receipt["verdict"], completed=guard["completed"], lost=guard["lost"],
           drc_errors=a["drc_errors"], proof=str(OUT / "proof.json"))
    return 0 if proof_ok else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as exc:
        status("FAILED", reason=str(exc), traceback=traceback.format_exc())
        raise
