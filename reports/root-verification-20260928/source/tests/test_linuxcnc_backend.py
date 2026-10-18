"""API-contract tests with a fake LinuxCNC module; these do not prove motion."""
from dataclasses import replace
import hashlib
from pathlib import Path
from types import SimpleNamespace
import unittest

from controller_backend import BackendError, LinuxCNCBackend


class Clock:
    def __init__(self):
        self.now = 10.0

    def __call__(self):
        return self.now


class FakeAPI:
    STATE_ESTOP, STATE_ESTOP_RESET, STATE_OFF, STATE_ON = 1, 2, 3, 4
    MODE_MANUAL, MODE_AUTO, MODE_MDI = 1, 2, 3
    INTERP_IDLE, INTERP_READING, INTERP_PAUSED = 1, 2, 3
    AUTO_RUN, AUTO_PAUSE, AUTO_RESUME = 1, 2, 3
    RCS_DONE, RCS_ERROR = 1, 3
    NML_ERROR, OPERATOR_ERROR = 1, 11

    def __init__(self):
        self.created = []
        self.calls = []
        self.error_queue = []
        self.fail_poll = False
        self.wait_result = self.RCS_DONE
        self.s = SimpleNamespace(
            ini_filename=str(LinuxCNCBackend().profile), joints=3, axis_mask=7,
            task_state=self.STATE_ESTOP, task_mode=self.MODE_MANUAL,
            interp_state=self.INTERP_IDLE, enabled=False, estop=True,
            homed=(False, False, False), actual_position=(0.0,) * 9,
            position=(0.0,) * 9, paused=False, inpos=True, current_vel=0.0,
            motion_line=0, file="", poll=self._poll)

    def _poll(self):
        if self.fail_poll:
            raise RuntimeError("NML unavailable")

    def stat(self):
        self.created.append("stat")
        return self.s

    def command(self):
        self.created.append("command")
        return self

    def error_channel(self):
        self.created.append("error_channel")
        return SimpleNamespace(poll=lambda: self.error_queue.pop(0) if self.error_queue else None)

    def wait_complete(self, timeout):
        return self.wait_result

    def state(self, state):
        self.calls.append(("state", state))
        self.s.task_state = self.STATE_OFF if state == self.STATE_ESTOP_RESET else state
        self.s.estop = state == self.STATE_ESTOP
        self.s.enabled = state == self.STATE_ON

    def mode(self, mode):
        self.calls.append(("mode", mode))
        self.s.task_mode = mode

    def teleop_enable(self, value):
        self.calls.append(("teleop_enable", value))

    def home(self, joint):
        self.calls.append(("home", joint))
        self.s.homed = (True, True, True)

    def mdi(self, line):
        self.calls.append(("mdi", line))

    def program_open(self, path):
        self.calls.append(("program_open", path))
        self.s.file = path

    def auto(self, *args):
        self.calls.append(("auto", *args))
        self.s.paused = args[0] == self.AUTO_PAUSE
        self.s.interp_state = self.INTERP_PAUSED if self.s.paused else self.INTERP_READING

    def abort(self):
        self.calls.append(("abort",))
        self.s.interp_state = self.INTERP_IDLE


class LinuxCNCBackendTests(unittest.TestCase):
    def setUp(self):
        self.api, self.clock = FakeAPI(), Clock()
        self.backend = LinuxCNCBackend(api=self.api, clock=self.clock)

    def connect(self):
        return self.backend.connect()

    def send(self, action, **args):
        self.backend.poll()
        return self.backend.execute(self.backend.issue(action, **args))

    def ready(self):
        self.connect()
        self.send("reset_estop")
        self.send("power_on")
        self.send("home_all")

    def load(self):
        path = self.backend.profile.parent / "programs/line_arc.ngc"
        return self.send("open_program", name=path.name, sha256=hashlib.sha256(path.read_bytes()).hexdigest())

    def test_constructor_does_not_connect_or_import(self):
        self.assertFalse(self.backend.connected)
        self.assertEqual(self.api.created, [])
        with self.assertRaises(BackendError):
            self.backend.issue("power_on")

    def test_live_hardware_mode_is_not_implemented(self):
        with self.assertRaises(ValueError):
            LinuxCNCBackend(simulation_only=False)

    def test_configuration_rejects_invalid_freshness(self):
        for value in (0, -1, float("nan"), float("inf"), True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                LinuxCNCBackend(status_max_age=value)

    def test_foreign_profile_rejected_before_command_channel(self):
        self.api.s.ini_filename = "/real-machine/machine.ini"
        with self.assertRaises(BackendError):
            self.connect()
        self.assertEqual(self.api.created, ["stat"])
        self.assertFalse(self.backend.connected)

    def test_uninitialized_status_rejected(self):
        self.api.s.axis_mask = 0
        with self.assertRaises(BackendError):
            self.connect()

    def test_connect_is_read_only(self):
        self.connect()
        self.assertEqual(self.api.calls, [])

    def test_expired_request_is_consumed_without_api_command(self):
        self.connect()
        request = self.backend.issue("reset_estop")
        self.clock.now += 0.5
        with self.assertRaisesRegex(BackendError, "expired"):
            self.backend.execute(request)
        self.assertEqual(self.api.calls, [])
        with self.assertRaisesRegex(BackendError, "replayed"):
            self.backend.execute(request)

    def test_stale_status_rejects_fresh_request(self):
        self.connect()
        self.clock.now += 0.6
        request = self.backend.issue("reset_estop")
        with self.assertRaisesRegex(BackendError, "stale"):
            self.backend.execute(request)
        self.assertEqual(self.api.calls, [])

    def test_reordered_request_cannot_execute(self):
        self.connect()
        older = self.backend.issue("reset_estop")
        newer = self.backend.issue("reset_estop")
        self.backend.execute(newer)
        with self.assertRaisesRegex(BackendError, "reordered"):
            self.backend.execute(older)

    def test_modified_request_cannot_execute(self):
        self.connect()
        request = self.backend.issue("reset_estop")
        with self.assertRaisesRegex(BackendError, "modified"):
            self.backend.execute(replace(request, action="power_on"))
        with self.assertRaises(BackendError):
            self.backend.execute(request)

    def test_state_rejection_cannot_be_replayed_when_ready(self):
        self.connect()
        request = self.backend.issue("mdi", line="G1 X1 F100")
        with self.assertRaisesRegex(BackendError, "not enabled"):
            self.backend.execute(request)
        self.send("reset_estop")
        self.send("power_on")
        self.send("home_all")
        with self.assertRaisesRegex(BackendError, "replayed"):
            self.backend.execute(request)

    def test_reconnect_invalidates_requests(self):
        self.connect()
        request = self.backend.issue("reset_estop")
        old_session = self.backend.session
        self.backend.disconnect()
        self.connect()
        self.assertNotEqual(old_session, self.backend.session)
        with self.assertRaisesRegex(BackendError, "expired connection"):
            self.backend.execute(request)
        self.assertEqual(self.api.calls, [])

    def test_reconnect_does_not_resume_program(self):
        self.ready()
        self.load()
        self.backend.disconnect()
        self.connect()
        with self.assertRaisesRegex(BackendError, "reopened"):
            self.send("run")
        self.assertFalse(any(c[0] == "auto" for c in self.api.calls))

    def test_mdi_requires_homing(self):
        self.connect()
        self.send("reset_estop")
        self.send("power_on")
        with self.assertRaisesRegex(BackendError, "homed"):
            self.send("mdi", line="G1 X1 F100")

    def test_mdi_calls_real_api_shape(self):
        self.ready()
        self.send("mdi", line="G1 X1 F100")
        self.assertEqual(self.api.calls[-2:], [("mode", self.api.MODE_MDI), ("mdi", "G1 X1 F100")])

    def test_mdi_rejects_multiline(self):
        self.ready()
        with self.assertRaisesRegex(BackendError, "one nonempty line"):
            self.send("mdi", line="G1 X1\nM3")

    def test_program_cannot_escape_profile(self):
        self.ready()
        with self.assertRaises(BackendError):
            self.send("open_program", name="../machine.ngc", sha256="0" * 64)

    def test_program_digest_must_match(self):
        self.ready()
        with self.assertRaisesRegex(BackendError, "digest"):
            self.send("open_program", name="line_arc.ngc", sha256="0" * 64)

    def test_run_pause_resume_are_explicit(self):
        self.ready()
        self.load()
        self.send("run")
        self.send("pause")
        self.send("resume")
        self.assertEqual([c for c in self.api.calls if c[0] == "auto"], [("auto", self.api.AUTO_RUN, 0), ("auto", self.api.AUTO_PAUSE), ("auto", self.api.AUTO_RESUME)])

    def test_resume_requires_reported_pause(self):
        self.ready()
        self.load()
        with self.assertRaisesRegex(BackendError, "reported paused"):
            self.send("resume")

    def test_timeout_drops_authority_and_never_retries(self):
        self.connect()
        self.api.wait_result = -1
        with self.assertRaisesRegex(BackendError, "not be retried"):
            self.send("reset_estop")
        self.assertFalse(self.backend.connected)
        self.assertEqual(len(self.api.calls), 1)

    def test_status_failure_drops_authority(self):
        self.connect()
        self.api.fail_poll = True
        with self.assertRaises(BackendError):
            self.backend.poll()
        self.assertFalse(self.backend.connected)

    def test_error_channel_is_read_and_exposed(self):
        self.connect()
        self.api.error_queue.append((self.api.OPERATOR_ERROR, "test error"))
        sample = self.backend.poll()
        self.assertEqual(sample.errors, ((self.api.OPERATOR_ERROR, "test error"),))

    def test_abort_can_be_requested_when_status_age_is_stale(self):
        self.connect()
        self.clock.now += 10
        self.backend.execute(self.backend.issue("abort"))
        self.assertEqual(self.api.calls, [("abort",)])

    def test_preexisting_error_blocks_motion_even_after_error_channel_consumed(self):
        self.ready()
        self.api.error_queue.append((self.api.OPERATOR_ERROR, "unhandled controller fault"))
        self.backend.poll()
        before = list(self.api.calls)
        with self.assertRaisesRegex(BackendError, "error latched"):
            self.send("mdi", line="G1 X1 F100")
        self.assertEqual(before, self.api.calls)
        self.send("abort")

    def test_error_arriving_at_command_precheck_blocks_motion(self):
        self.ready()
        request = self.backend.issue("mdi", line="G1 X1 F100")
        self.api.error_queue.append((self.api.OPERATOR_ERROR, "new controller fault"))
        before = list(self.api.calls)
        with self.assertRaisesRegex(BackendError, "error latched"):
            self.backend.execute(request)
        self.assertEqual(before, self.api.calls)

    def test_expiry_during_status_refresh_sends_nothing(self):
        self.connect()
        request = self.backend.issue("reset_estop")
        self.api.s.poll = lambda: setattr(self.clock, "now", self.clock.now + 0.6)
        with self.assertRaisesRegex(BackendError, "expired during status"):
            self.backend.execute(request)
        self.assertEqual(self.api.calls, [])

    def test_expiry_during_mode_change_cannot_send_mdi(self):
        self.ready()
        original_mode = self.api.mode
        def delayed_mode(mode):
            original_mode(mode)
            self.clock.now += 0.6
        self.api.mode = delayed_mode
        request = self.backend.issue("mdi", line="G1 X1 F100")
        with self.assertRaisesRegex(BackendError, "expired before sending"):
            self.backend.execute(request)
        self.assertFalse(any(call[0] == "mdi" for call in self.api.calls))
        with self.assertRaisesRegex(BackendError, "replayed"):
            self.backend.execute(request)

    def test_nonfinite_velocity_discards_authority(self):
        self.connect()
        self.api.s.current_vel = float("nan")
        with self.assertRaises(BackendError):
            self.backend.poll()
        self.assertFalse(self.backend.connected)

    def test_run_is_asynchronous_to_keep_hold_and_abort_available(self):
        self.ready()
        self.load()
        self.api.wait_result = -1
        self.send("run")
        self.assertTrue(self.backend.connected)


if __name__ == "__main__":
    unittest.main()
