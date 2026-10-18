"""Bounded background completion of the resumed proof; never adopts a board."""
import ctypes
import datetime
import json
import os
import subprocess
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent


def alive(pid):
    handle = ctypes.windll.kernel32.OpenProcess(0x1000, False, pid)
    if not handle:
        return False
    try:
        code = ctypes.c_ulong()
        ctypes.windll.kernel32.GetExitCodeProcess(handle, ctypes.byref(code))
        return code.value == 259
    finally:
        ctypes.windll.kernel32.CloseHandle(handle)


def fail(reason):
    result = {"phase": "FAILED", "reason": reason, "adopted": False,
              "updated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat()}
    (HERE / "bridge-final-status.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result), flush=True)
    return 2


def main():
    lock = HERE / "watcher.lock"
    try:
        fd = os.open(lock, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
    except FileExistsError:
        print("completion watcher already registered", flush=True)
        return 2
    with os.fdopen(fd, "w") as output:
        output.write(str(os.getpid()))
    try:
        (HERE / "watcher-ready.json").write_text(json.dumps({"pid": os.getpid(), "max_hours": 2,
                                                           "adopts_board": False}), encoding="utf-8")
        deadline = time.monotonic() + 7200
        while time.monotonic() < deadline:
            if (HERE / "watcher.stop").exists():
                return fail("completion watcher stopped by local stop file; native receipts preserved")
            try:
                status = json.loads((HERE / "bridge-status.json").read_text(encoding="utf-8"))
            except (OSError, ValueError):
                time.sleep(5)
                continue
            if status["phase"] == "COMPLETE":
                checker = HERE / "finish_bridge_proof.py"
                if not checker.is_file():
                    return fail("independent final checker is unavailable")
                with (HERE / "final-check.log").open("w", encoding="utf-8") as output:
                    result = subprocess.run([sys.executable, "-B", str(checker)], cwd=HERE,
                                            stdout=output, stderr=subprocess.STDOUT, check=False)
                if not (HERE / "bridge-final-status.json").is_file():
                    return fail(f"independent final checker exited {result.returncode} without a status receipt")
                print(f"final checker exited {result.returncode}; see bridge-final-status.json", flush=True)
                return result.returncode
            if status["phase"] == "FAILED":
                return fail(status.get("reason", "native measurement failed"))
            if not alive(int(status["pid"])):
                return fail("native proof process ended without completing; partial receipts preserved")
            time.sleep(10)
        return fail("two-hour completion window expired; no board adopted")
    finally:
        lock.unlink(missing_ok=True)


if __name__ == "__main__":
    raise SystemExit(main())
