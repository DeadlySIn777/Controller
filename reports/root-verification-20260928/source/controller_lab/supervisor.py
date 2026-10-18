"""Executable proposal for controller authority and fault semantics.

This is not CNC firmware, a motor simulator, a safety controller, or an
implementation of authentication. All times use one simulated controller clock.
The independent motion backend is represented by explicit local events.
"""

from dataclasses import dataclass
from enum import StrEnum
import hashlib
import json
import uuid


class State(StrEnum):
    DISARMED = "disarmed"
    READY = "ready"
    RUNNING = "running"
    HOLD_REQUESTED = "hold_requested"
    HELD = "held"
    FAULT = "fault"


@dataclass(frozen=True)
class Config:
    hmi_lease_ms: int = 1000
    motion_watchdog_ms: int = 20
    stop_ack_timeout_ms: int = 500
    hmi_loss_policy: str = "hold"
    max_job_bytes: int = 16 * 1024 * 1024

    def __post_init__(self):
        for name in ("hmi_lease_ms", "motion_watchdog_ms", "stop_ack_timeout_ms", "max_job_bytes"):
            value = getattr(self, name)
            if type(value) is not int or value <= 0:
                raise ValueError(f"{name} must be a positive integer")
        if self.hmi_loss_policy not in ("hold", "continue_local"):
            raise ValueError("hmi_loss_policy must be hold or continue_local")


class Supervisor:
    ACTIONS = frozenset(("heartbeat", "arm", "start", "hold", "resume", "disarm"))
    FIELDS = frozenset(("version", "boot_id", "session_id", "sequence", "deadline_ms", "action"))
    ARMED = frozenset((State.READY, State.RUNNING, State.HOLD_REQUESTED, State.HELD))

    def __init__(self, config=None, boot_id=None):
        self.config = config or Config()
        self.now_ms = 0
        self.boot_id = boot_id or str(uuid.uuid4())
        self.state = State.DISARMED
        self.fault = None
        self.physical_enable = False
        self.estop_active = False
        self.drive_fault_active = False
        self.position_trusted = False
        self.job_digest = None
        self.backend_job_accepted = False
        self.session_id = None
        self.used_sessions = set()
        self.lease_end_ms = None
        self.last_sequence = -1
        self.last_motion_progress_ms = None
        self.stop_deadline_ms = None
        self.disarm_after_stop = False
        self.history = []
        self._record("boot")

    @property
    def enable_request(self):
        """Logical request only; real brake/STO sequencing is not implemented."""
        return self.state in self.ARMED and self.physical_enable and not self.fault

    @property
    def motion_request(self):
        return self.enable_request and self.state in (State.RUNNING, State.HOLD_REQUESTED)

    def snapshot(self):
        return {
            "time_ms": self.now_ms, "boot_id": self.boot_id, "state": str(self.state),
            "fault": self.fault, "enable_request": bool(self.enable_request),
            "motion_request": bool(self.motion_request), "position_trusted": self.position_trusted,
            "job_digest": self.job_digest, "backend_job_accepted": self.backend_job_accepted,
            "session_id": self.session_id, "lease_end_ms": self.lease_end_ms,
            "last_sequence": self.last_sequence,
        }

    def _record(self, event, **detail):
        self.history.append({"event": event, **detail, **self.snapshot()})

    def _result(self, accepted, reason):
        self._record("command_accepted" if accepted else "command_rejected", reason=reason)
        self.assert_invariants()
        return {"accepted": accepted, "reason": reason, "state": str(self.state)}

    def connect(self, session_id=None):
        """An already-authenticated service acquires authority; auth is out of scope."""
        if self.session_id is not None:
            raise ValueError("an unexpired session already owns command authority")
        if session_id is not None and (not isinstance(session_id, str) or not session_id):
            raise ValueError("session_id must be a nonempty string")
        new_session = session_id or str(uuid.uuid4())
        if new_session in self.used_sessions:
            raise ValueError("session identity cannot be reused in this boot")
        self.session_id = new_session
        self.used_sessions.add(new_session)
        self.last_sequence = -1
        self.lease_end_ms = self.now_ms + self.config.hmi_lease_ms
        self._record("session_opened")
        return {"version": 1, "boot_id": self.boot_id, "session_id": self.session_id,
                "lease_end_ms": self.lease_end_ms, "controller_time_ms": self.now_ms}

    def command(self, envelope):
        if not isinstance(envelope, dict) or set(envelope) != self.FIELDS:
            return self._result(False, "invalid_schema")
        if type(envelope["version"]) is not int or envelope["version"] != 1:
            return self._result(False, "unsupported_version")
        if any(not isinstance(envelope[key], str) or not envelope[key]
               for key in ("boot_id", "session_id", "action")):
            return self._result(False, "invalid_schema")
        if type(envelope["sequence"]) is not int or not 0 <= envelope["sequence"] <= 0xFFFFFFFF:
            return self._result(False, "invalid_sequence")
        if type(envelope["deadline_ms"]) is not int or envelope["deadline_ms"] < 0:
            return self._result(False, "invalid_deadline")
        if envelope["boot_id"] != self.boot_id:
            return self._result(False, "wrong_boot")
        if self.session_id is None or envelope["session_id"] != self.session_id:
            return self._result(False, "wrong_session")
        if not self.now_ms < envelope["deadline_ms"] <= self.lease_end_ms:
            return self._result(False, "expired_or_ungranted_deadline")
        if envelope["sequence"] <= self.last_sequence:
            return self._result(False, "duplicate_or_reordered")
        # Consume a fresh envelope even when its requested state transition is
        # refused. Otherwise the same start could become executable later.
        self.last_sequence = envelope["sequence"]
        action = envelope["action"]
        if action not in self.ACTIONS:
            return self._result(False, "unknown_action")
        if action == "heartbeat":
            self.lease_end_ms = self.now_ms + self.config.hmi_lease_ms
            return self._result(True, "lease_renewed")
        if self.fault:
            return self._result(False, "fault_latched")
        if action == "arm":
            if self.state != State.DISARMED:
                return self._result(False, "not_disarmed")
            if not self.physical_enable or self.estop_active or self.drive_fault_active:
                return self._result(False, "physical_conditions_not_met")
            if (self.last_motion_progress_ms is None
                    or self.now_ms - self.last_motion_progress_ms >= self.config.motion_watchdog_ms):
                return self._result(False, "motion_backend_not_fresh")
            self.state = State.READY
        elif action == "start":
            if self.state != State.READY:
                return self._result(False, "not_ready")
            if not self.job_digest or not self.backend_job_accepted:
                return self._result(False, "job_not_accepted_by_backend")
            if not self.position_trusted:
                return self._result(False, "position_untrusted")
            self.state = State.RUNNING
        elif action == "hold":
            if self.state != State.RUNNING:
                return self._result(False, "not_running")
            self._request_hold("operator")
        elif action == "resume":
            if self.state != State.HELD or not self.position_trusted:
                return self._result(False, "not_held_or_position_untrusted")
            self.state = State.RUNNING
        elif action == "disarm":
            if self.state in (State.RUNNING, State.HOLD_REQUESTED):
                self.disarm_after_stop = True
                if self.state == State.RUNNING:
                    self._request_hold("disarm")
            else:
                self.state = State.DISARMED
        return self._result(True, action)

    def stage_job(self, content, expected_sha256):
        if self.state not in (State.DISARMED, State.READY):
            raise ValueError("job replacement is forbidden while executing or held")
        if not isinstance(content, bytes) or not 0 < len(content) <= self.config.max_job_bytes:
            raise ValueError("job must be nonempty bytes within configured capacity")
        digest = hashlib.sha256(content).hexdigest()
        if digest != expected_sha256:
            raise ValueError("job digest mismatch")
        self.job_digest = digest
        self.backend_job_accepted = False
        self._record("job_staged")

    def backend_accept_job(self, digest):
        """Local backend attestation, not a remote UI command or G-code validator."""
        if self.state not in (State.DISARMED, State.READY) or not self.job_digest or digest != self.job_digest:
            raise ValueError("backend attestation does not match the staged job/state")
        self.backend_job_accepted = True
        self._record("job_accepted_by_backend")

    def set_physical_enable(self, active):
        if type(active) is not bool:
            raise ValueError("physical enable must be Boolean")
        self.physical_enable = active
        if not active and self.state in self.ARMED:
            self._trip("physical_enable_removed")
        self._record("physical_enable_changed")

    def report_position_trusted(self):
        if self.state not in (State.DISARMED, State.READY):
            raise ValueError("position qualification requires stopped non-fault state")
        self.position_trusted = True
        self._record("position_qualified_by_backend")

    def motion_progress(self):
        """Backend declares a completed valid control cycle, not mere CPU activity."""
        self.last_motion_progress_ms = self.now_ms

    def _request_hold(self, reason):
        self.state = State.HOLD_REQUESTED
        self.stop_deadline_ms = self.now_ms + self.config.stop_ack_timeout_ms
        self._record("hold_requested", reason=reason)

    def acknowledge_stopped(self):
        if self.state != State.HOLD_REQUESTED:
            raise ValueError("no stop is awaiting acknowledgment")
        self.state = State.DISARMED if self.disarm_after_stop else State.HELD
        self.stop_deadline_ms = None
        self.disarm_after_stop = False
        self._record("backend_reports_stopped")

    def complete_job(self):
        if self.state != State.RUNNING:
            raise ValueError("no running job to complete")
        self.state = State.READY
        self._record("job_completed")

    def _trip(self, reason):
        if self.fault is None:
            self.fault = reason
        self.state = State.FAULT
        self.position_trusted = False
        self.backend_job_accepted = False
        self.session_id = None
        self.lease_end_ms = None
        self.stop_deadline_ms = None
        self.disarm_after_stop = False
        self._record("fault_latched", cause=reason)

    def set_estop(self, active):
        if type(active) is not bool:
            raise ValueError("estop must be Boolean")
        self.estop_active = active
        if active:
            self._trip("estop")
        self._record("estop_input_changed")

    def set_drive_fault(self, active):
        if type(active) is not bool:
            raise ValueError("drive fault must be Boolean")
        self.drive_fault_active = active
        if active:
            self._trip("drive_fault")
        self._record("drive_fault_input_changed")

    def local_reset(self):
        if self.estop_active or self.drive_fault_active:
            raise ValueError("active physical fault prevents reset")
        if self.state != State.FAULT:
            raise ValueError("no latched fault")
        self.fault = None
        self.state = State.DISARMED
        self.session_id = None
        self.lease_end_ms = None
        self._record("local_fault_reset")

    def reboot(self, boot_id=None):
        new_id = boot_id or str(uuid.uuid4())
        if new_id == self.boot_id:
            raise ValueError("reboot must change boot identity")
        # This event models loss of execution state. Position and backend
        # validation are discarded even if a file survives in real storage.
        now, history = self.now_ms, self.history
        physical, estop, drive_fault = self.physical_enable, self.estop_active, self.drive_fault_active
        self.__init__(self.config, new_id)
        self.now_ms, self.history = now, history
        self.physical_enable, self.estop_active, self.drive_fault_active = physical, estop, drive_fault
        if estop or drive_fault:
            self._trip("physical_fault_at_boot")
        self._record("rebooted")

    def disconnect(self):
        self.session_id = None
        self.lease_end_ms = None
        self._record("hmi_disconnected")
        if self.state == State.RUNNING and self.config.hmi_loss_policy == "hold":
            self._request_hold("hmi_loss")

    def advance(self, milliseconds):
        if type(milliseconds) is not int or milliseconds < 0:
            raise ValueError("time advance must be a nonnegative integer")
        target = self.now_ms + milliseconds
        while True:
            due = []
            if self.state in self.ARMED:
                assert self.last_motion_progress_ms is not None
                due.append((self.last_motion_progress_ms + self.config.motion_watchdog_ms, 0, "watchdog"))
            if self.session_id is not None:
                due.append((self.lease_end_ms, 1, "lease"))
            if self.stop_deadline_ms is not None:
                due.append((self.stop_deadline_ms, 2, "stop"))
            if not due or min(due)[0] > target:
                break
            event_time, _, event = min(due)
            self.now_ms = max(self.now_ms, event_time)
            if event == "watchdog":
                self._trip("motion_watchdog")
            elif event == "lease":
                self.disconnect()
            else:
                self._trip("stop_ack_timeout")
        self.now_ms = target
        self.assert_invariants()

    def assert_invariants(self):
        assert (self.state == State.FAULT) == (self.fault is not None)
        if self.state in self.ARMED:
            assert self.last_motion_progress_ms is not None
        if self.fault or self.estop_active or self.drive_fault_active or not self.physical_enable:
            assert not self.enable_request and not self.motion_request
        if self.state in (State.RUNNING, State.HOLD_REQUESTED, State.HELD):
            assert self.job_digest and self.backend_job_accepted and self.position_trusted
        assert (self.state == State.HOLD_REQUESTED) == (self.stop_deadline_ms is not None)
        assert (self.session_id is None) == (self.lease_end_ms is None)
        assert not self.motion_request or self.enable_request


def envelope(controller, action, sequence=None):
    """Test/client convenience. This does not authenticate a caller."""
    return {"version": 1, "boot_id": controller.boot_id,
            "session_id": controller.session_id,
            "sequence": controller.last_sequence + 1 if sequence is None else sequence,
            "deadline_ms": controller.lease_end_ms, "action": action}


def trace_json(controller):
    return json.dumps(controller.history, indent=2) + "\n"
