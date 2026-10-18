"""Bounded resource watch; samples and alarms only, no process control."""
import datetime
import json
import os
from pathlib import Path
import subprocess
import time
import psutil

HERE = Path(__file__).resolve().parent
STATE = HERE / "resource-status.json"
SAMPLES = HERE / "resource-samples.jsonl"


def utc():
    return datetime.datetime.now(datetime.timezone.utc).isoformat()


def state(**data):
    STATE.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")


def main():
    if STATE.exists() or SAMPLES.exists():
        raise FileExistsError("Preserve existing monitor evidence")
    until = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)
    deadline = time.monotonic() + 3600
    state(phase="RUNNING", pid=os.getpid(), start_utc=utc(), until_utc=until.isoformat(),
          cpu_limit_percent=70, gpu_limit_c=80, gpu_limit_w=350,
          alert="audible beep and logged breach", heavy_slots_added=0)
    try:
        while time.monotonic() < deadline:
            cpu = psutil.cpu_percent(interval=10)
            result = subprocess.run(
                ["C:/Windows/System32/nvidia-smi.exe", "--query-gpu=temperature.gpu,power.draw",
                 "--format=csv,noheader,nounits"], check=True, capture_output=True,
                text=True, timeout=5)
            rows = [line.split(",") for line in result.stdout.splitlines() if line.strip()]
            if not rows:
                raise ValueError("No GPU reading")
            gpu_c = max(float(row[0].strip()) for row in rows)
            gpu_w = max(float(row[1].strip()) for row in rows)
            breached = []
            if cpu > 70:
                breached.append("cpu")
            if gpu_c > 80:
                breached.append("gpu_temperature")
            if gpu_w > 350:
                breached.append("gpu_power")
            sample = dict(utc=utc(), cpu_percent=cpu, gpu_c=gpu_c, gpu_w=gpu_w,
                          breached=breached)
            with SAMPLES.open("a", encoding="utf-8") as out:
                out.write(json.dumps(sample) + "\n")
            if breached:
                print(json.dumps(sample), flush=True)
                try:
                    import winsound
                    winsound.Beep(1000, 500)
                except Exception as exc:
                    print("Audible alert unavailable: " + str(exc), flush=True)
        state(phase="COMPLETE", pid=os.getpid(), utc=utc())
    except BaseException as exc:
        state(phase="FAILED", pid=os.getpid(), utc=utc(), reason=str(exc))
        raise


if __name__ == "__main__":
    main()
