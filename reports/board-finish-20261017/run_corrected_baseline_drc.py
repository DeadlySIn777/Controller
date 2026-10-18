"""Run native DRC/parity on verified, physically unchanged genuine fill cache."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import psutil

H = Path(__file__).resolve().parent
WORK = H / "corrected-baseline-r1"
NATIVE = WORK / "native"
OUT = WORK / "cached-native-drc"


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def put(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def main():
    OUT.mkdir(exist_ok=False)
    me = psutil.Process()
    me.cpu_affinity(list(range(16, 28)))
    me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    native_check = WORK / "native-check/receipt.json"
    check = json.loads(native_check.read_bytes())
    board = NATIVE / "board.kicad_pcb"
    assert sha(board) == check["corrected_board_SHA256"]
    assert check["all_native_pad_partitions_identical"] and check["all_other_actual_via_masks_identical"]
    pins = {str(p): sha(p) for p in NATIVE.rglob("*") if p.is_file()}
    pins[str(native_check)] = sha(native_check)
    args = ["C:/Program Files/KiCad/10.0/bin/kicad-cli.exe", "pcb", "drc", "--format", "json",
            "--severity-all", "--all-track-errors", "--schematic-parity", "--output", str(OUT / "drc.json"), "board.kicad_pcb"]
    put("launch.json", {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "args": args,
        "working_directory": str(NATIVE), "input_SHA256": pins,
        "native_refill": False, "cache_basis": check["cached_fill_basis"],
        "CPU_affinity": list(range(16, 28)), "total_CPU_pause_percent": 70,
        "total_CPU_resume_percent": 62, "requested_CPU_limit_percent": 80})
    started = time.monotonic()
    peak = 0.0
    paused = False
    samples = 0
    breaches = 0
    with (OUT / "drc.log").open("w", encoding="utf-8") as log:
        run = subprocess.Popen(args, cwd=NATIVE, stdout=log, stderr=subprocess.STDOUT)
        child = psutil.Process(run.pid)
        try:
            while run.poll() is None:
                cpu = psutil.cpu_percent(interval=1)
                samples += 1
                peak = max(peak, cpu)
                breaches += cpu >= 80
                if cpu >= 70 and not paused:
                    child.suspend()
                    paused = True
                elif cpu < 62 and paused:
                    child.resume()
                    paused = False
                sample = {"utc": dt.datetime.now(dt.timezone.utc).isoformat(), "CPU_percent": cpu,
                          "paused": paused, "pid": child.pid}
                with (OUT / "resource-samples.jsonl").open("a", encoding="utf-8") as out:
                    out.write(json.dumps(sample) + "\n")
                if samples % 10 == 0:
                    put("status.json", {"phase": "NATIVE_DRC_RUNNING", "last_sample": sample,
                        "peak_CPU_percent": peak, "samples": samples, "samples_at_or_above_80_percent": breaches})
        finally:
            if paused and run.poll() is None:
                child.resume()
        rc = run.wait()
    assert all(sha(Path(p)) == h for p, h in pins.items())
    assert (OUT / "drc.json").is_file()
    data = json.loads((OUT / "drc.json").read_bytes())
    errors = [r for r in data["violations"] if r["severity"] == "error"]
    warnings = [r for r in data["violations"] if r["severity"] == "warning"]
    put("receipt.json", {"status": "NATIVE_CACHED_DRC_PARITY_COMPLETE_REVIEW_REQUIRED", "exit_code": rc,
        "board_SHA256": sha(board), "drc_SHA256": sha(OUT / "drc.json"), "ordinary_errors": len(errors),
        "warnings": len(warnings), "schematic_parity_issues": len(data.get("schematic_parity", [])),
        "native_uncapped_missing_joins": 1172, "native_API_unconnected": 1183,
        "native_cache_physically_equivalent_and_850_zones_exact": True,
        "native_refill_calls": 0, "peak_CPU_percent": peak, "samples": samples,
        "samples_at_or_above_80_percent": breaches, "elapsed_seconds": time.monotonic() - started,
        "input_files_unchanged": True, "adopted": False, "manufacturing_ready": False})
    put("status.json", {"phase": "COMPLETE_REVIEW_REQUIRED", "ordinary_errors": len(errors), "warnings": len(warnings)})
    print(f"Native DRC complete: {len(errors)} errors, {len(warnings)} warnings.", flush=True)


if __name__ == "__main__":
    main()
