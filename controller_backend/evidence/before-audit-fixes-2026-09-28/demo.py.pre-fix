"""Executable DISPLAY client for the dedicated, hardware-free LinuxCNC profile."""
import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import threading
import time
import traceback

from .linuxcnc_backend import BackendError, LinuxCNCBackend


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-ini")
    parser.parse_args()
    if os.environ.get("CONTROLLER_LAB_ALLOW_SIMULATION") != "1":
        raise SystemExit("Explicit simulation launch is required; no connection attempted")
    import linuxcnc

    backend = LinuxCNCBackend(completion_timeout=30, request_ttl=2, status_max_age=2)
    evidence_dir = Path(__file__).resolve().parent / "evidence"
    evidence_dir.mkdir(exist_ok=True)
    report = {"schema": 1, "real_linuxcnc": True, "hardware_connected": False,
              "run_id": os.environ.get("CONTROLLER_LAB_RUN_ID"),
              "utc": datetime.now(timezone.utc).isoformat(), "kernel": platform.release(),
              "python": platform.python_version(), "success": False, "checks": [],
              "runtime": subprocess.check_output(["dpkg-query", "-W", "linuxcnc-uspace", "python3"], text=True)}
    trace = []
    stop = threading.Event()
    sampler = None
    phase = ["startup"]
    trace_error = []

    def sample_trace():
        # An independent read-only status channel; the adapter remains sole error reader.
        status = linuxcnc.stat()
        started = time.monotonic()
        while not stop.is_set():
            try:
                status.poll()
                if Path(status.ini_filename).resolve() != backend.profile:
                    raise RuntimeError("Trace profile identity changed")
                trace.append({"t": round(time.monotonic() - started, 6), "phase": phase[0],
                              "xyz": list(status.actual_position[:3]), "velocity": status.current_vel,
                              "interp_state": status.interp_state, "paused": bool(status.paused),
                              "in_position": bool(status.inpos), "line": status.motion_line})
            except Exception as exc:
                trace_error.append(str(exc))
                return
            stop.wait(0.01)

    def check(name, condition, **detail):
        if not condition:
            raise AssertionError(name + ": " + repr(detail))
        report["checks"].append({"name": name, "passed": True, **detail})
        print("PASS " + name, flush=True)

    def send(action, **args):
        backend.poll()
        return backend.execute(backend.issue(action, **args))

    def wait_for(predicate, timeout=30):
        deadline = time.monotonic() + timeout
        while time.monotonic() < deadline:
            status = backend.poll()
            if status.errors:
                raise RuntimeError("LinuxCNC reported: " + repr(status.errors))
            if predicate(status):
                return status
            time.sleep(0.01)
        raise TimeoutError("Timed out in phase " + phase[0])

    def idle(status):
        return (status.interp_state == linuxcnc.INTERP_IDLE and status.in_position and
                abs(status.velocity) < 1e-6 and
                all(abs(a-b) < 1e-9 for a, b in zip(status.actual_position, status.commanded_position)))

    def load(name):
        path = backend.profile.parent / "programs" / name
        send("open_program", name=name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    try:
        deadline = time.monotonic() + 10
        while True:
            try:
                backend.connect()
                break
            except BackendError:
                if time.monotonic() >= deadline:
                    raise
                time.sleep(0.1)
        check("attached_exact_simulation_profile", backend.sample.ini_filename == str(backend.profile))
        sampler = threading.Thread(target=sample_trace, daemon=True)
        sampler.start()
        send("reset_estop")
        send("power_on")
        send("home_all")
        status = wait_for(lambda s: all(s.homed) and s.in_position)
        check("homed_three_simulated_joints", all(status.homed))

        phase[0] = "mdi"
        send("mdi", line="G21 G90 G1 X1 Y2 Z-1 F300")
        status = wait_for(lambda s: idle(s) and all(abs(a-b) < 1e-6 for a,b in zip(s.actual_position, (1,2,-1))))
        check("mdi_endpoint", all(abs(a-b) < 1e-6 for a, b in zip(status.actual_position, (1, 2, -1))), xyz=status.actual_position[:3])
        send("mdi", line="G1 X0 Y0 Z0 F300")
        wait_for(lambda s: idle(s) and all(abs(v) < 1e-6 for v in s.actual_position[:3]))

        phase[0] = "line_arc"
        load("line_arc.ngc")
        send("run")
        # Require real movement before treating an idle status as completion.
        wait_for(lambda s: s.actual_position[0] > 0.1)
        status = wait_for(idle)
        arc_points = [r for r in trace if r["phase"] == "line_arc"]
        check("line_arc_returned_to_origin", all(abs(v) < 1e-6 for v in status.actual_position[:3]), xyz=status.actual_position[:3])
        check("line_arc_traversed_semicircle", max(r["xyz"][1] for r in arc_points) > 9.9 and max(r["xyz"][0] for r in arc_points) > 19.9,
              sampled_max_x=max(r["xyz"][0] for r in arc_points), sampled_max_y=max(r["xyz"][1] for r in arc_points))

        phase[0] = "hold_resume"
        load("hold_resume.ngc")
        send("run")
        wait_for(lambda s: s.actual_position[0] > 1)
        send("pause")
        status = wait_for(lambda s: s.paused and abs(s.velocity) < 1e-6)
        paused_at = status.actual_position[0]
        time.sleep(0.2)
        status = backend.poll()
        check("feed_hold_stopped_and_held", status.paused and abs(status.actual_position[0] - paused_at) < 1e-6, x=paused_at)
        send("resume")
        wait_for(lambda s: not s.paused and s.actual_position[0] > paused_at + 0.1)
        status = wait_for(idle)
        check("explicit_resume_completed", abs(status.actual_position[0]) < 1e-6)

        phase[0] = "abort"
        load("hold_resume.ngc")
        send("run")
        wait_for(lambda s: s.actual_position[0] > 1)
        send("abort")
        status = wait_for(idle)
        check("abort_stopped_before_destination", 0 < status.actual_position[0] < 10, x=status.actual_position[0])

        phase[0] = "reconnect"
        old_request = backend.issue("mdi", line="G1 X40 F300")
        old_session = backend.session
        before = status.actual_position[:3]
        backend.disconnect()
        backend.connect()
        rejected = False
        try:
            backend.execute(old_request)
        except BackendError:
            rejected = True
        time.sleep(0.2)
        status = backend.poll()
        check("reconnect_rejected_old_command_without_motion", rejected and backend.session != old_session and status.actual_position[:3] == before)
        rejected = False
        try:
            send("run")
        except BackendError:
            rejected = True
        check("reconnect_requires_explicit_program_reopen", rejected)
        send("power_off")
        check("simulation_powered_off", not backend.poll().enabled)
        check("trace_reader_had_no_errors", not trace_error, errors=trace_error)
        report["success"] = True
    except Exception as exc:
        report["error"] = str(exc)
        report["traceback"] = traceback.format_exc()
        print(report["traceback"], flush=True)
    finally:
        if backend.connected:
            try:
                send("abort")
                send("power_off")
            except BackendError as exc:
                report["cleanup_error"] = str(exc)
        stop.set()
        if sampler:
            sampler.join(timeout=2)
        backend.disconnect()
        report["trace_samples"] = len(trace)
        report["profile_sha256"] = hashlib.sha256(backend.profile.read_bytes()).hexdigest()
        (evidence_dir / "linuxcnc-simulation.json").write_text(json.dumps(report, indent=2) + "\n")
        (evidence_dir / "linuxcnc-trace.json").write_text(json.dumps(trace, separators=(",", ":")) + "\n")
    return 0 if report["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
