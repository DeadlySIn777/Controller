"""Kernel CPU hard caps for this task's heavy workers, leaving desktop headroom.

Only workers with this evidence-folder marker in their command ancestry are
eligible. Supervisors and unrelated Python/user processes are excluded. No job
has kill-on-close, memory, time, security, or process-count limits.
"""
import ctypes
from ctypes import wintypes
import datetime as dt
import json
from pathlib import Path
import time
import psutil

H = Path(__file__).resolve().parent
OUT = H / "shared-cpu-cap-r1"
K = ctypes.WinDLL("kernel32", use_last_error=True)
K.CreateJobObjectW.argtypes = [ctypes.c_void_p, wintypes.LPCWSTR]
K.CreateJobObjectW.restype = wintypes.HANDLE
K.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
K.OpenProcess.restype = wintypes.HANDLE
K.AssignProcessToJobObject.argtypes = [wintypes.HANDLE, wintypes.HANDLE]
K.AssignProcessToJobObject.restype = wintypes.BOOL
K.SetInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD]
K.SetInformationJobObject.restype = wintypes.BOOL
K.QueryInformationJobObject.argtypes = [wintypes.HANDLE, ctypes.c_int, ctypes.c_void_p, wintypes.DWORD, ctypes.c_void_p]
K.QueryInformationJobObject.restype = wintypes.BOOL
K.CloseHandle.argtypes = [wintypes.HANDLE]


class Rate(ctypes.Structure):
    _fields_ = [("ControlFlags", wintypes.DWORD), ("CpuRate", wintypes.DWORD)]


def stamp():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def event(row):
    with (OUT / "events.jsonl").open("a", encoding="utf-8") as out:
        out.write(json.dumps({"utc": stamp(), **row}) + "\n")


def task_worker(p):
    try:
        if p.name().lower() not in ("python.exe", "pythonw.exe", "kicad-cli.exe", "java.exe"):
            return False
        cmd = " ".join(p.cmdline()).lower()
        if any(x in cmd for x in ("shared_cpu_cap.py", "guarded", "resource_guard", "resource-guard", "watch.py")):
            return False
        if " -c " in cmd:
            return False
        family = [p, *p.parents()]
        owned = any("board-finish-20261017" in " ".join(q.cmdline()).lower() for q in family)
        if not owned:
            return False
        # Do not cap an ancestor as well as its heavy descendants: nested CPU
        # rates are relative to a capped parent and would compound the quota.
        if any(q.name().lower() in ("python.exe", "kicad-cli.exe", "java.exe") for q in p.children()):
            return False
        t = p.cpu_times()
        return t.user + t.system > 1
    except (psutil.Error, OSError):
        return False


def main():
    OUT.mkdir(exist_ok=False)
    jobs = {}
    assigned = {}
    print("Installing per-worker kernel hard caps with a shared 25% CPU budget.", flush=True)
    (OUT / "plan.json").write_text(json.dumps({"utc": stamp(), "shared_task_budget_percent": 25,
        "native_fill_weight": 5, "other_heavy_worker_weight": 1,
        "Windows_control_flags": 5, "JobObjectCpuRateControlInformation": 15,
        "only_task_owned_heavy_leaves": True, "no_kill_on_close": True,
        "reason": "A prior one-second total CPU sample reached84%; retain additional headroom below the user's80% limit",
        "references": ["https://learn.microsoft.com/en-us/windows/win32/api/winnt/ns-winnt-jobobject_cpu_rate_control_information",
                       "https://learn.microsoft.com/en-us/windows/win32/api/jobapi2/nf-jobapi2-assignprocesstojobobject"]}, indent=2) + "\n", encoding="utf-8")
    peak = 0
    samples = 0
    until = time.monotonic() + 12 * 3600
    try:
        while time.monotonic() < until and not (OUT / "stop").exists():
            targets = {p.pid: p for p in psutil.process_iter() if task_worker(p)}
            live = {}
            for pid, p in targets.items():
                try:
                    identity = (pid, p.create_time())
                    live[identity] = p
                    if identity in jobs:
                        continue
                    handle = K.CreateJobObjectW(None, None)
                    assert handle
                    # Install a conservative cap BEFORE attaching the worker.
                    rate = Rate(5, 100)
                    assert K.SetInformationJobObject(handle, 15, ctypes.byref(rate), ctypes.sizeof(rate))
                    ph = K.OpenProcess(0x0100 | 0x0001 | 0x1000, False, pid)
                    assert ph
                    try:
                        ok = bool(K.AssignProcessToJobObject(handle, ph))
                        error = ctypes.get_last_error() if not ok else 0
                    finally:
                        K.CloseHandle(ph)
                    if not ok:
                        K.CloseHandle(handle)
                        event({"action": "assignment_failed_no_process_terminated", "pid": pid, "WinError": error})
                        continue
                    weight = 5 if "native_combined_actual_full_fill_r1.py" in " ".join(p.cmdline()) else 1
                    jobs[identity] = (handle, weight)
                    event({"action": "kernel_job_attached", "pid": pid, "worker": Path(p.cmdline()[1]).name if len(p.cmdline()) > 1 else p.name(), "weight": weight})
                except (psutil.Error, OSError, AssertionError) as exc:
                    event({"action": "attach_error", "pid": pid, "error": str(exc)})
            for identity in list(jobs):
                if identity not in live:
                    K.CloseHandle(jobs.pop(identity)[0])
            total_weight = sum(v[1] for v in jobs.values())
            current = []
            for identity, (handle, weight) in jobs.items():
                budget = max(1, int(2500 * weight / max(1, total_weight)))
                rate = Rate(5, budget)
                assert K.SetInformationJobObject(handle, 15, ctypes.byref(rate), ctypes.sizeof(rate))
                observed = Rate()
                assert K.QueryInformationJobObject(handle, 15, ctypes.byref(observed), ctypes.sizeof(observed), None)
                assert observed.ControlFlags == 5 and observed.CpuRate == budget
                current.append({"pid": identity[0], "kernel_hard_cap_percent": budget / 100})
            cpu = psutil.cpu_percent(interval=1)
            peak = max(peak, cpu)
            samples += 1
            row = {"utc": stamp(), "total_CPU_percent": cpu, "workers": current,
                   "configured_aggregate_worker_cap_percent": sum(r["kernel_hard_cap_percent"] for r in current),
                   "assignment_failures_may_leave_unattached_workers": len(live) - len(jobs)}
            with (OUT / "samples.jsonl").open("a", encoding="utf-8") as out:
                out.write(json.dumps(row) + "\n")
            if samples % 5 == 0:
                (OUT / "status.json").write_text(json.dumps({"phase": "RUNNING", "last_sample": row,
                    "peak_total_CPU_percent_since_cap": peak, "samples": samples}, indent=2) + "\n", encoding="utf-8")
    finally:
        for handle, _ in jobs.values():
            K.CloseHandle(handle)


if __name__ == "__main__":
    main()
