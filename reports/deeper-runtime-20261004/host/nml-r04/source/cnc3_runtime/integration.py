#!/usr/bin/python3
"""LinuxCNC NML client for the explicitly disconnected SIM2 qualification.

Commands enter the actual task/motion planners. The client never writes joint
command or motion-enable HAL pins. All sensor/fault injections are labelled
virtual and the saved setup store is read-only throughout this execution.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import sys
import time

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from controller_config.service import read_json
from controller_config.setup_service import SetupService
from controller_lab.cnc3_configuration import verify_configuration
from tools.create_cnc3_qualification_fixture import runtime_sources


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("-ini", "--ini")
    args = parser.parse_args()
    if os.environ.get("CNC3_ALLOW_DISCONNECTED_RTL_SIMULATION") != "1":
        raise RuntimeError("Explicit disconnected simulation required")
    import hal
    import linuxcnc
    observer = hal.component("c3_sim_observer_" + str(os.getpid()))
    observer.ready()
    store = Path(os.environ["CNC3_SIM_STORE"])
    before_store = hashlib.sha256(store.read_bytes()).hexdigest()
    manifest = verify_configuration(read_json(args.manifest), SetupService(store),
        source_root=ROOT, expected_source_files=runtime_sources())
    active = manifest["cnc3_host"]["active_mask"]
    count = {255: 8, 4095: 12}.get(active)
    if count is None:
        raise RuntimeError("This NML qualification requires 8 or 12 contiguous active joints")
    if args.ini:
        linuxcnc.nmlfile = linuxcnc.ini(args.ini).find("EMC", "NML_FILE") or "/usr/share/linuxcnc/linuxcnc.nml"
    command, status, error_channel = linuxcnc.command(), linuxcnc.stat(), linuxcnc.error_channel()
    receipt = {"schema_version": 1, "kind": "actual_linuxcnc_sim2_joint_integration",
        "utc": datetime.now(timezone.utc).isoformat(), "manifest_sha256": manifest["manifest_sha256"],
        "configuration_binding": manifest["configuration_binding"], "active_joints": count,
        "fitted_channels": 12, "checks": [], "observations": {}, "linuxcnc_messages": [],
        "physical_authority": False, "physical_commissioning_complete": False,
        "physical_measurements": 0, "paid_api_calls": 0, "physical_device_connections": 0,
        "scope": {"actual_linuxcnc_task_and_free_joint_planners": True,
                  "physical_or_cartesian_machine_kinematics_qualified": False,
                  "physical_or_sensor_homing_qualified": False, "loaded_realtime_deadlines_qualified": False}}
    failure = None

    def check(condition, label, detail=None):
        receipt["checks"].append({"check": label, "status": "PASS" if condition else "FAIL", "detail": detail})
        if not condition:
            raise AssertionError(label)

    def pin(name):
        return hal.get_value("cnc3r." + name)

    def snapshot():
        # Source adapter brackets both callback snapshots with an odd/even
        # sequence. Do not mix pin values from two servo observations.
        for _ in range(200):
            first = pin("snapshot-sequence")
            if first & 1:
                continue
            scalar = ("state", "fault", "fault-code", "commission-phase", "ready", "armed",
                "discovered", "feedback-valid", "sim-permission", "sim-reset-ready", "session", "sequence",
                "endpoint-faults", "fitted-channels", "installed-channels", "encoder-channels", "active-mask",
                "physical-authority", "production-profile-complete", "provider-sequence", "provider-error",
                "di", "di-age", "do-applied", "do-fault", "probe-status", "encoder-valid-mask",
                "index-armed-mask", "rtl-armed-mask", "rtl-enabled-mask", "events-stored", "event-status",
                "sim-seconds", "transactions", "updates", "samples")
            result = {name: pin(name) for name in scalar}
            for field in ("position-cmd", "position-fb", "reported-steps", "observed-step-rises", "model-position-steps", "model-accepted-rises"):
                result[field] = [pin(f"{index}.{field}") for index in range(12)]
            for field in ("count", "model-count", "observed-edges", "model-index-rises"):
                result["encoder-" + field] = [pin(f"encoder.{index}.{field}") for index in range(4)]
            result["probe-events"] = [pin(f"probe.{index}.events") for index in range(2)]
            result["index-events"] = [pin(f"index.{index}.events") for index in range(4)]
            if first == pin("snapshot-sequence"):
                if result["physical-authority"] or result["production-profile-complete"]:
                    raise AssertionError("A simulation cannot grant physical authority")
                status.poll()
                result["task-state"] = status.task_state
                result["task-mode"] = status.task_mode
                result["joint-velocity"] = [status.joint[index]["velocity"] for index in range(count)]
                result["homed"] = [bool(status.homed[index]) for index in range(count)]
                message = error_channel.poll()
                if message:
                    receipt["linuxcnc_messages"].append(list(message))
                return result
        raise RuntimeError("Could not acquire a coherent runtime snapshot")

    def wait(label, predicate, timeout=60, refuse_fault=True):
        deadline = time.monotonic() + timeout
        last = None
        while time.monotonic() < deadline:
            last = snapshot()
            if refuse_fault and last["fault"]:
                raise AssertionError(f"{label}: runtime fault {last['fault-code']}, endpoint {last['endpoint-faults']}, phase {last['commission-phase']}")
            if predicate(last):
                print(json.dumps({"phase": label, "sim_seconds": last["sim-seconds"]}), flush=True)
                return last
            time.sleep(.005)
        receipt["observations"]["timeout_snapshot"] = last
        raise TimeoutError(label)

    def setting(name, value):
        # Only simulated inputs and deliberate protocol reset controls.
        allowed = {"reset", "sim-reset-button", "do-command", "sim-di", "sim-probes", "probe-arm", "index-arm", "sim-alarms", "sim-faults"}
        if name not in allowed:
            raise AssertionError("Client may not write motion command or enable")
        hal.set_p("cnc3r." + name, str(int(value)))

    def send(method, *values):
        method(*values)
        result = command.wait_complete(2)
        if result != linuxcnc.RCS_DONE:
            raise RuntimeError(f"NML command was not acknowledged: {result}")

    def reset_button():
        start = snapshot()["sim-seconds"]
        setting("sim-reset-button", 1)
        wait("deliberate_model_reset_press", lambda value: value["sim-seconds"] - start >= .051 and value["sim-reset-ready"])
        setting("sim-reset-button", 0)

    def start_jogs():
        for index in range(count):
            velocity = min(.5 + .03 * index, manifest["cnc3_host"]["max_velocity"][index] / 5)
            send(command.jog, linuxcnc.JOG_CONTINUOUS, True, index, velocity)

    def stop_jogs():
        for index in range(count):
            send(command.jog, linuxcnc.JOG_STOP, True, index)
        return wait("all_task_jogs_stopped", lambda value: all(abs(v) < 1e-6 for v in value["joint-velocity"]))

    try:
        discovered = wait("capability_discovery", lambda value: value["discovered"] and value["state"] == 4)
        check(discovered["fitted-channels"] == 12 and discovered["installed-channels"] == 12, "twelve_fitted_independent_of_active_joint_count")
        check(discovered["active-mask"] == active and discovered["encoder-channels"] == 4, "exact_reviewed_motion_and_encoder_inventory")
        check(not any(discovered["homed"]), "no_position_or_homing_restored_from_setup")
        send(command.state, linuxcnc.STATE_ESTOP_RESET)
        send(command.state, linuxcnc.STATE_OFF)
        send(command.mode, linuxcnc.MODE_MANUAL)
        setting("reset", 1)
        wait("new_protocol_session", lambda value: value["session"] != discovered["session"] or value["commission-phase"] != 0)
        setting("reset", 0)
        ready = wait("actual_protocol_configuration_selftests_continuity_and_io_enable", lambda value: value["ready"] and not value["armed"])
        check(ready["rtl-enabled-mask"] == 0 and not ready["sim-permission"], "configuration_and_io_selftest_do_not_arm_motion")
        reset_button()
        send(command.state, linuxcnc.STATE_ON)
        send(command.teleop_enable, False)
        running = wait("task_enable_and_actual_rtl_arm", lambda value: value["armed"] and value["rtl-enabled-mask"] == active)
        receipt["observations"]["before_motion"] = running
        setting("index-arm", 15)
        start_jogs()
        moved = wait("all_joints_concurrently_execute_task_jogs", lambda value:
            all(v > 0 for v in value["joint-velocity"]) and
            all(value["observed-step-rises"][i] - running["observed-step-rises"][i] >= 5 for i in range(count)) and
            all(value["model-accepted-rises"][i] - running["model-accepted-rises"][i] >= 5 for i in range(count)))
        check(moved["rtl-armed-mask"] == active and moved["rtl-enabled-mask"] == active, "all_requested_channels_armed_in_same_observation")
        indexed = wait("four_actual_abz_index_events", lambda value: all(v >= 1 for v in value["index-events"]))
        stopped = stop_jogs()
        receipt["observations"]["during_concurrent_motion"] = moved
        receipt["observations"]["after_motion"] = stopped
        for index in range(count):
            pin_delta = stopped["observed-step-rises"][index] - running["observed-step-rises"][index]
            accepted = stopped["model-accepted-rises"][index] - running["model-accepted-rises"][index]
            plant_delta = stopped["model-position-steps"][index] - running["model-position-steps"][index]
            emitted_delta = stopped["reported-steps"][index] - running["reported-steps"][index]
            check(pin_delta > 0 and pin_delta == accepted and abs(plant_delta - emitted_delta) <= 1,
                  f"joint_{index}_command_pin_emission_and_independent_plant_agree",
                  {"observed_rises": pin_delta, "accepted_rises": accepted, "plant_delta": plant_delta, "reported_delta": emitted_delta})
        for index in range(4):
            model_delta = stopped["encoder-model-count"][index] - running["encoder-model-count"][index]
            rtl_delta = stopped["encoder-count"][index] - running["encoder-count"][index]
            check(model_delta > 0 and abs(model_delta - rtl_delta) <= 1 and indexed["index-events"][index] >= 1,
                  f"encoder_{index}_real_abz_feedback_and_index", {"model_delta": model_delta, "rtl_delta": rtl_delta})
        if count == 8:
            check(stopped["observed-step-rises"][8:] == [0] * 4, "eight_joint_selection_keeps_unused_fitted_channels_inhibited")
        for index in range(24):
            setting("sim-di", 1 << index)
            sample = wait(f"di_{index}", lambda value: value["di"] == 1 << index and value["di-age"] != 255)
            check(sample["di"] == 1 << index, f"general_di_{index}_through_actual_feedback")
        setting("sim-di", 0)
        for index in range(16):
            setting("do-command", 1 << index)
            sample = wait(f"do_{index}", lambda value: value["do-applied"] == 1 << index and not value["do-fault"])
            check(sample["do-applied"] == 1 << index, f"general_do_{index}_independent_application_feedback")
        setting("do-command", 0)
        wait("outputs_returned_to_neutral", lambda value: value["do-applied"] == 0)
        setting("sim-probes", 0)
        setting("probe-arm", 3)
        wait("both_probes_armed", lambda value: value["probe-status"] & 0x30 == 0x30)
        setting("sim-probes", 3)
        probes = wait("both_real_probe_capture_events", lambda value: all(v >= 1 for v in value["probe-events"]))
        check(all(v >= 1 for v in probes["probe-events"]), "both_probes_captured_over_frozen_event_transport")
        setting("probe-arm", 0)
        setting("sim-probes", 0)
        start_jogs()
        alarm_baseline = wait("moving_before_individual_alarm", lambda value: all(v > 0 for v in value["joint-velocity"]))
        setting("sim-alarms", 1 << (count - 1))
        faulted = wait("individual_alarm_propagates_to_task_and_all_motion", lambda value:
            value["fault"] and value["rtl-enabled-mask"] == 0 and value["rtl-armed-mask"] == 0,
            refuse_fault=False)
        check(faulted["endpoint-faults"] != 0, "individual_alarm_is_actual_endpoint_fault")
        setting("sim-alarms", 0)
        quiet = wait("clearing_alarm_does_not_restart", lambda value: value["sim-seconds"] - faulted["sim-seconds"] >= .020,
                     refuse_fault=False)
        check(quiet["fault"] and quiet["rtl-enabled-mask"] == 0 and quiet["observed-step-rises"] == faulted["observed-step-rises"],
              "fault_latched_and_no_automatic_motion_restart")
        receipt["observations"]["alarm_before"] = alarm_baseline
        receipt["observations"]["alarm_after"] = quiet
        send(command.abort)
        send(command.state, linuxcnc.STATE_OFF)
        setting("reset", 1)
        reset = wait("stopped_explicit_reset_new_session", lambda value: value["session"] != faulted["session"], refuse_fault=False)
        setting("reset", 0)
        recovered = wait("recovered_unarmed_reviewed_runtime", lambda value: value["ready"] and not value["fault"])
        check(not recovered["sim-permission"] and recovered["rtl-enabled-mask"] == 0 and not any(recovered["homed"]),
              "deliberate_reset_retains_inhibited_unhomed_restart")
        check(recovered["provider-sequence"] > faulted["provider-sequence"], "motion_session_reset_cannot_replay_provider_facts")
        receipt["observations"]["recovered"] = recovered
        check(hashlib.sha256(store.read_bytes()).hexdigest() == before_store, "reviewed_setup_bytes_preserved")
        receipt["status"] = "PASS"
    except Exception as exc:
        failure = repr(exc)
        receipt["status"], receipt["error"] = "FAIL", failure
        try:
            receipt["observations"]["failure_snapshot"] = snapshot()
        except Exception as nested:
            receipt["snapshot_error"] = repr(nested)
    finally:
        try:
            command.abort()
            command.state(linuxcnc.STATE_OFF)
            command.wait_complete(2)
            command.state(linuxcnc.STATE_ESTOP)
        except Exception as exc:
            receipt["shutdown_error"] = repr(exc)
            receipt["status"] = "FAIL"
        receipt["setup_sha256_before"] = before_store
        receipt["setup_sha256_after"] = hashlib.sha256(store.read_bytes()).hexdigest()
        receipt["completed_utc"] = datetime.now(timezone.utc).isoformat()
        observer.exit()
        output = Path(args.output)
        with output.open("x", encoding="utf-8") as handle:
            json.dump(receipt, handle, indent=2, allow_nan=False)
            handle.write("\n")
        print(json.dumps({"status": receipt["status"], "checks": len(receipt["checks"]), "error": failure}), flush=True)
    return 0 if receipt["status"] == "PASS" else 1


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except Exception as error:
        # Preserve startup failures without claiming any execution coverage.
        output_argument = sys.argv.index("--output") + 1 if "--output" in sys.argv else None
        if output_argument is not None and output_argument < len(sys.argv):
            output = Path(sys.argv[output_argument])
            if not output.exists():
                with output.open("x", encoding="utf-8") as handle:
                    json.dump({"status": "FAIL", "startup_error": repr(error), "checks": [],
                        "physical_authority": False, "physical_measurements": 0, "paid_api_calls": 0}, handle, indent=2)
                    handle.write("\n")
        raise
