"""Wait on the known live native job, then audit its real saved result once."""
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import subprocess
import time
import psutil

H = Path(__file__).resolve().parent
OUT = H / "composed-successor-resource-guard-r1"
RECEIPT = H / "combined-route-stage-r1/native-full/receipt.json"
AUDIT = H / "audit_composed_actual_after.py"
NATIVE_PID = 74184


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def put(name, data):
    (OUT / name).write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main():
    assert not OUT.exists()
    me = psutil.Process()
    me.cpu_affinity(list(range(16, 28)))
    me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    native = psutil.Process(NATIVE_PID)
    identity = native.create_time()
    assert "native_combined_actual_full_fill_r1.py" in " ".join(native.cmdline())
    checked = subprocess.run(["C:/Python314/python.exe", "-X", "utf8", str(AUDIT), "--preflight"],
                             capture_output=True, text=True, check=True)
    OUT.mkdir()
    digest = hashlib.sha256(AUDIT.read_bytes()).hexdigest()
    put("plan.json", {"utc": stamp(), "native_pid": NATIVE_PID, "native_process_created": identity,
                       "audit_file": str(AUDIT), "audit_SHA256": digest,
                       "preflight": json.loads(checked.stdout), "native_restarted_or_refilled": False,
                       "affinity": list(range(16, 28)), "numeric_threads": 2,
                       "total_CPU_pause_percent": 70, "total_CPU_resume_percent": 62,
                       "shared_kernel_worker_cap_controller": "shared-cpu-cap-r1"})
    timeout = time.monotonic() + 12 * 3600
    count = 0
    print(f"Waiting on confirmed live native PID {NATIVE_PID}; no duplicate native job.", flush=True)
    while not RECEIPT.is_file():
        if time.monotonic() >= timeout:
            put("status.json", {"phase": "WAIT_TIMEOUT_NATIVE_STATE_RECHECK_REQUIRED", "utc": stamp()})
            return 3
        live = native.is_running() and native.create_time() == identity
        if not live:
            put("status.json", {"phase": "NATIVE_ENDED_WITHOUT_RECEIPT_REVIEW_REQUIRED", "utc": stamp()})
            return 2
        cpu = psutil.cpu_percent(interval=1)
        count += 1
        if count % 10 == 0:
            put("status.json", {"phase": "WAITING_ON_CONFIRMED_LIVE_NATIVE_PROCESS", "utc": stamp(),
                                 "native_pid": NATIVE_PID, "native_process_created": identity,
                                 "CPU_percent": cpu, "native_restarted_or_refilled": False})
    assert hashlib.sha256(AUDIT.read_bytes()).hexdigest() == digest
    env = dict(os.environ)
    env.update({key: "2" for key in ("OPENBLAS_NUM_THREADS", "OMP_NUM_THREADS", "MKL_NUM_THREADS", "NUMEXPR_NUM_THREADS")})
    peak, breaches, paused = 0.0, 0, set()
    with (OUT / "audit.log").open("w", encoding="utf-8") as log:
        run = subprocess.Popen(["C:/Python314/python.exe", "-X", "utf8", str(AUDIT), "--run"], env=env,
                               stdout=log, stderr=subprocess.STDOUT)
        worker = psutil.Process(run.pid)
        print(f"Actual native receipt is ready; launched independent audit PID {run.pid}.", flush=True)
        try:
            while run.poll() is None:
                cpu = psutil.cpu_percent(interval=1)
                peak = max(peak, cpu)
                breaches += cpu >= 80
                family = [worker, *worker.children(recursive=True)]
                if cpu >= 70:
                    for p in reversed(family):
                        if p.pid not in paused:
                            try:
                                p.suspend()
                                paused.add(p.pid)
                            except psutil.Error:
                                pass
                elif cpu < 62:
                    for p in family:
                        if p.pid in paused:
                            try:
                                p.resume()
                                paused.remove(p.pid)
                            except psutil.Error:
                                pass
                row = {"utc": stamp(), "phase": "ACTUAL_AFTER_AUDIT_RUNNING", "pid": run.pid,
                       "CPU_percent": cpu, "paused_pids": sorted(paused)}
                with (OUT / "samples.jsonl").open("a", encoding="utf-8") as out:
                    out.write(json.dumps(row) + "\n")
                put("status.json", row)
        finally:
            for pid in paused:
                try:
                    psutil.Process(pid).resume()
                except psutil.Error:
                    pass
        rc = run.wait()
    put("receipt.json", {"phase": "AUDIT_PROCESS_COMPLETE_REVIEW_RESULT", "utc": stamp(), "exit_code": rc,
                          "peak_CPU_percent": peak, "samples_at_or_above_80_percent": breaches,
                          "audit_SHA256_unchanged": hashlib.sha256(AUDIT.read_bytes()).hexdigest() == digest,
                          "adopted": False, "manufacturing_ready": False})
    print(f"Actual-after audit process completed with exit code {rc}; inspect its scoped receipt.", flush=True)
    return rc


if __name__ == "__main__":
    raise SystemExit(main())
