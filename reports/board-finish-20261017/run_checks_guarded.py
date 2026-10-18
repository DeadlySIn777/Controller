"""Resume saved full-native host audits with a CPU guard for this job tree.

No original source/board is changed. The original audit scripts write their
previously absent AFTER results in their declared evidence directories.
"""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
import time

import psutil

HERE = Path(__file__).resolve().parent
OLD = HERE.parent / "board-finish-20261011" / "continuation-r2"
OUT = HERE / "resumed-full-native-host-audits"
ALLOWED = list(range(16, 28))
PAUSE = 70.0
RESUME = 62.0
LIMIT = 80.0
JOBS = [
    (OLD / "field-power/audit_combined_R753_actual_full_state_conn_scope_r763.generated.py",
     "1b7fabb30f39a5cb6329dd26a7bff3aa6f1a9c778b0a9d28efa19490a655cd8b", ["--after"]),
    (OLD / "field-power/audit_combined_actual_full_source_gains_and_CPP_partitions_r767.py",
     "dced8e7aa48f0217d798d1ede67f283a087a5fa2822d77ae7cbaee0ed0f58b4a", []),
]


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def put(name, value):
    (OUT / name).write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")


def children(proc):
    try:
        return [proc, *proc.children(recursive=True)]
    except psutil.NoSuchProcess:
        return []


def main():
    OUT.mkdir(exist_ok=False)
    me = psutil.Process()
    me.cpu_affinity(ALLOWED)
    me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    for path, expected, _ in JOBS:
        assert sha(path) == expected, path
    env = os.environ.copy()
    env.update({k: "2" for k in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")})
    put("plan.json", {"utc": utc(), "python": sys.executable, "affinity": ALLOWED,
                      "total_CPU_limit_percent": LIMIT, "suspend_at_percent": PAUSE,
                      "resume_below_percent": RESUME, "sample_interval_seconds": 1,
                      "only_this_supervisor_child_tree_controlled": True,
                      "jobs": [{"file": str(p), "sha256": h, "args": a} for p, h, a in JOBS]})
    results = []
    peak = 0.0
    samples = 0
    pauses = 0
    breaches = 0
    for index, (path, expected, args) in enumerate(JOBS, 1):
        assert sha(path) == expected
        print(f"Starting saved host audit {index}: {path.name}", flush=True)
        with (OUT / f"step-{index}.log").open("w", encoding="utf-8") as log:
            run = subprocess.Popen([sys.executable, "-X", "utf8", str(path), *args],
                                   env=env, stdout=log, stderr=subprocess.STDOUT)
            proc = psutil.Process(run.pid)
            suspended = set()
            start = time.monotonic()
            try:
                while run.poll() is None:
                    cpu = psutil.cpu_percent(interval=1)
                    peak = max(peak, cpu)
                    samples += 1
                    breaches += cpu >= LIMIT
                    action = None
                    if cpu >= PAUSE and not suspended:
                        for child in reversed(children(proc)):
                            try:
                                child.suspend()
                                suspended.add(child.pid)
                            except psutil.NoSuchProcess:
                                pass
                        pauses += 1
                        action = "suspend_owned_job_tree"
                    elif cpu < RESUME and suspended:
                        for pid in list(suspended):
                            try:
                                psutil.Process(pid).resume()
                            except psutil.NoSuchProcess:
                                pass
                        suspended.clear()
                        action = "resume_owned_job_tree"
                    for child in children(proc):
                        try:
                            child.cpu_affinity(ALLOWED)
                            child.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
                        except psutil.NoSuchProcess:
                            pass
                    sample = {"utc": utc(), "step": index, "pid": run.pid,
                              "CPU_percent": cpu, "action": action,
                              "suspended_pids": sorted(suspended)}
                    with (OUT / "resource-samples.jsonl").open("a", encoding="utf-8") as out:
                        out.write(json.dumps(sample) + "\n")
                    if samples % 10 == 0 or action:
                        put("status.json", {"phase": "RUNNING", "last_sample": sample,
                            "peak_CPU_percent": peak, "samples": samples,
                            "pauses": pauses, "samples_at_or_above_80_percent": breaches})
            finally:
                for pid in suspended:
                    try:
                        psutil.Process(pid).resume()
                    except psutil.NoSuchProcess:
                        pass
            results.append({"step": index, "exit_code": run.wait(),
                            "elapsed_seconds": time.monotonic() - start,
                            "log_sha256": sha(OUT / f"step-{index}.log")})
            put("job-results.json", results)
        if run.returncode:
            put("status.json", {"phase": "FAILED_RESULTS_PRESERVED", "results": results,
                                 "peak_CPU_percent": peak, "samples": samples,
                                 "pauses": pauses, "samples_at_or_above_80_percent": breaches})
            raise SystemExit(run.returncode)
    put("status.json", {"phase": "COMPLETE_REVIEW_REQUIRED", "results": results,
                        "peak_CPU_percent": peak, "samples": samples, "pauses": pauses,
                        "samples_at_or_above_80_percent": breaches, "adopted": False})
    print("Saved audits completed; design verdicts require review.", flush=True)


if __name__ == "__main__":
    main()
