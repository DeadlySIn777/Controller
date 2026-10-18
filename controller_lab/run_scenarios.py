"""Generate reviewable supervisory traces without connecting to any hardware."""
import argparse
import hashlib
import json
from pathlib import Path

from .supervisor import Config, Supervisor, envelope


def start(config=None):
    c = Supervisor(config, "scenario-boot")
    job = b"G21 G90\nG1 X10 F600\nM2\n"
    digest = hashlib.sha256(job).hexdigest()
    c.set_physical_enable(True)
    c.stage_job(job, digest)
    c.backend_accept_job(digest)
    c.report_position_trusted()
    c.motion_progress()
    c.connect("scenario-session")
    for action in ("arm", "start"):
        assert c.command(envelope(c, action))["accepted"]
    return c


def generate():
    cases = []

    def save(name, c, expected, scope):
        assert str(c.state) == expected, (name, c.snapshot())
        c.assert_invariants()
        cases.append({"name": name, "expectation": expected, "scope": scope,
                      "result": "pass", "final": c.snapshot(), "trace": c.history})

    c = start()
    c.complete_job()
    save("normal_local_job_completion", c, "ready", "Backend completion is an injected event, not G-code execution.")

    c = start()
    c.disconnect()
    c.acknowledge_stopped()
    c.connect("replacement-session")
    save("hmi_loss_and_reconnect", c, "held", "Reconnection does not resume; stop acknowledgment is simulated.")

    c = start(Config(hmi_loss_policy="continue_local"))
    c.disconnect()
    for _ in range(10):
        c.motion_progress()
        c.advance(5)
    c.complete_job()
    save("local_completion_without_hmi", c, "ready", "Optional studied policy; not approved for a physical machine.")

    c = start()
    c.advance(20)
    save("motion_backend_stall", c, "fault", "Model deadline, not a measured hardware watchdog.")

    c = start(Config(stop_ack_timeout_ms=30))
    c.command(envelope(c, "hold"))
    for _ in range(3):
        c.motion_progress()
        c.advance(10)
    save("stop_not_acknowledged", c, "fault", "A request to stop is not assumed to have stopped the machine.")

    c = start()
    queued = envelope(c, "resume")
    c.reboot("new-boot")
    c.connect("after-reboot")
    assert not c.command(queued)["accepted"]
    save("stale_command_after_reboot", c, "disarmed", "Boot identity rejects old authority; no automatic restart.")

    c = start()
    c.set_drive_fault(True)
    c.set_drive_fault(False)
    c.local_reset()
    save("drive_fault_recovery", c, "disarmed", "Reset requires requalification before another start.")

    return {"model": "supervisory-contract-v1", "physical_hardware_connected": False,
            "assumptions": "Timing constants are study values; no mechanics, pulses, electrical protection or safety certification modeled.",
            "cases": cases}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", type=Path, default=Path("reports/supervisor-scenarios.json"))
    args = parser.parse_args()
    report = generate()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(f"{len(report['cases'])} scenarios passed; wrote {args.output}")


if __name__ == "__main__":
    main()
