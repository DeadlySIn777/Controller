import hashlib
import random
import unittest

from controller_lab.supervisor import Config, State, Supervisor, envelope


JOB = b"G21 G90\nG1 X10 F600\nM2\n"
DIGEST = hashlib.sha256(JOB).hexdigest()


def prepared(config=None, *, backend_ready=True):
    c = Supervisor(config, boot_id="boot-A")
    c.set_physical_enable(True)
    c.stage_job(JOB, DIGEST)
    c.backend_accept_job(DIGEST)
    c.report_position_trusted()
    c.connect("session-A")
    if backend_ready:
        c.motion_progress()
    return c


def send(c, action):
    result = c.command(envelope(c, action))
    if not result["accepted"]:
        raise AssertionError(result)


def running(config=None):
    c = prepared(config)
    send(c, "arm")
    send(c, "start")
    return c


class SupervisorTests(unittest.TestCase):
    def test_boot_requires_a_real_backend_cycle_before_arm(self):
        c = prepared(backend_ready=False)
        send(c, "heartbeat")
        self.assertEqual(c.command(envelope(c, "arm"))["reason"], "motion_backend_not_fresh")
        self.assertFalse(c.enable_request)
        c.motion_progress()
        send(c, "arm")

    def test_reboot_discards_previous_backend_cycle(self):
        c = running()
        c.reboot("boot-B")
        c.connect("session-B")
        self.assertEqual(c.command(envelope(c, "arm"))["reason"], "motion_backend_not_fresh")
        self.assertFalse(c.enable_request)
        c.motion_progress()
        send(c, "arm")

    def test_boot_never_requests_enable_or_motion(self):
        c = Supervisor()
        self.assertEqual(c.state, State.DISARMED)
        self.assertFalse(c.enable_request)
        self.assertFalse(c.motion_request)
        self.assertFalse(c.position_trusted)

    def test_remote_start_does_not_arm(self):
        c = prepared()
        result = c.command(envelope(c, "start"))
        self.assertFalse(result["accepted"])
        self.assertEqual(c.state, State.DISARMED)

    def test_job_digest_is_not_backend_validation(self):
        c = prepared()
        c.stage_job(JOB, DIGEST)
        send(c, "arm")
        self.assertEqual(c.command(envelope(c, "start"))["reason"], "job_not_accepted_by_backend")

    def test_corrupt_upload_preserves_existing_job(self):
        c = prepared()
        with self.assertRaisesRegex(ValueError, "digest"):
            c.stage_job(JOB + b"X999", DIGEST)
        self.assertEqual(c.job_digest, DIGEST)

    def test_job_cannot_change_during_run_or_hold(self):
        c = running()
        with self.assertRaises(ValueError):
            c.stage_job(JOB, DIGEST)
        send(c, "hold")
        c.acknowledge_stopped()
        with self.assertRaises(ValueError):
            c.stage_job(JOB, DIGEST)

    def test_rejected_start_cannot_be_replayed_after_arm(self):
        c = prepared()
        old_start = envelope(c, "start")
        self.assertFalse(c.command(old_start)["accepted"])
        send(c, "arm")
        self.assertEqual(c.command(old_start)["reason"], "duplicate_or_reordered")
        self.assertEqual(c.state, State.READY)

    def test_reordered_and_duplicate_commands_have_no_motion_effect(self):
        c = running()
        hold = envelope(c, "hold", 50)
        self.assertTrue(c.command(hold)["accepted"])
        self.assertFalse(c.command(envelope(c, "resume", 49))["accepted"])
        c.acknowledge_stopped()
        self.assertFalse(c.command(hold)["accepted"])
        self.assertEqual(c.state, State.HELD)

    def test_sequence_wrap_requires_a_new_session(self):
        c = prepared()
        self.assertTrue(c.command(envelope(c, "heartbeat", 0xFFFFFFFF))["accepted"])
        self.assertFalse(c.command(envelope(c, "arm", 0))["accepted"])

    def test_second_session_cannot_steal_active_authority(self):
        c = running()
        with self.assertRaises(ValueError):
            c.connect("session-B")
        self.assertEqual(c.session_id, "session-A")

    def test_session_identity_cannot_be_reused(self):
        c = prepared()
        c.disconnect()
        with self.assertRaises(ValueError):
            c.connect("session-A")

    def test_commands_from_previous_session_rejected(self):
        c = prepared()
        old = envelope(c, "arm")
        c.disconnect()
        c.connect("session-B")
        self.assertEqual(c.command(old)["reason"], "wrong_session")

    def test_expired_or_ungranted_deadline_rejected(self):
        c = prepared()
        for deadline in (0, c.lease_end_ms + 1):
            with self.subTest(deadline=deadline):
                packet = envelope(c, "arm")
                packet["deadline_ms"] = deadline
                self.assertFalse(c.command(packet)["accepted"])

    def test_malformed_fields_rejected_without_changing_state(self):
        c = prepared()
        changes = {"version": True, "sequence": True, "deadline_ms": True,
                   "session_id": [], "boot_id": "", "action": {}}
        for key, value in changes.items():
            with self.subTest(key=key):
                p = envelope(c, "arm")
                p[key] = value
                self.assertFalse(c.command(p)["accepted"])
                self.assertEqual(c.state, State.DISARMED)
        self.assertFalse(c.command({})["accepted"])
        p = envelope(c, "arm")
        p["untrusted_extra"] = "anything"
        self.assertFalse(c.command(p)["accepted"])

    def test_backend_watchdog_expires_at_exact_deadline(self):
        c = running()
        c.advance(19)
        self.assertEqual(c.state, State.RUNNING)
        c.advance(1)
        self.assertEqual(c.fault, "motion_watchdog")
        self.assertFalse(c.enable_request)
        self.assertFalse(c.motion_request)

    def test_large_time_jump_processes_first_deadline_not_only_end(self):
        c = running(Config(hmi_lease_ms=50, motion_watchdog_ms=20))
        c.advance(10000)
        fault = next(x for x in c.history if x["event"] == "fault_latched")
        self.assertEqual(fault["time_ms"], 20)
        self.assertEqual(c.now_ms, 10000)

    def test_network_activity_does_not_feed_motion_watchdog(self):
        c = running()
        c.advance(10)
        send(c, "heartbeat")
        c.advance(10)
        self.assertEqual(c.fault, "motion_watchdog")

    def test_hmi_lease_expiry_requests_hold_with_healthy_backend(self):
        c = running(Config(hmi_lease_ms=30, motion_watchdog_ms=20))
        for _ in range(3):
            c.motion_progress()
            c.advance(10)
        self.assertEqual(c.state, State.HOLD_REQUESTED)
        self.assertIsNone(c.session_id)
        self.assertTrue(c.motion_request)  # Stop request still needs backend execution.
        c.acknowledge_stopped()
        self.assertEqual(c.state, State.HELD)
        self.assertFalse(c.motion_request)

    def test_continue_local_policy_never_bypasses_motion_watchdog(self):
        c = running(Config(hmi_loss_policy="continue_local"))
        c.disconnect()
        self.assertEqual(c.state, State.RUNNING)
        c.advance(20)
        self.assertEqual(c.fault, "motion_watchdog")

    def test_stopped_ack_is_required_and_timeout_latches_fault(self):
        c = running(Config(stop_ack_timeout_ms=30, motion_watchdog_ms=20))
        send(c, "hold")
        for _ in range(3):
            c.motion_progress()
            c.advance(10)
        self.assertEqual(c.fault, "stop_ack_timeout")
        self.assertFalse(c.motion_request)

    def test_disarm_during_run_waits_for_stopped_ack(self):
        c = running()
        send(c, "disarm")
        self.assertEqual(c.state, State.HOLD_REQUESTED)
        c.acknowledge_stopped()
        self.assertEqual(c.state, State.DISARMED)

    def test_reconnect_does_not_resume(self):
        c = running()
        c.disconnect()
        c.acknowledge_stopped()
        c.connect("session-B")
        send(c, "heartbeat")
        self.assertEqual(c.state, State.HELD)
        send(c, "resume")
        self.assertEqual(c.state, State.RUNNING)

    def test_fault_cannot_clear_by_network_command_or_heartbeat(self):
        c = running()
        c.set_estop(True)
        c.connect("diagnostic-session")
        send(c, "heartbeat")
        for action in ("arm", "start", "resume"):
            self.assertFalse(c.command(envelope(c, action))["accepted"])
        with self.assertRaises(ValueError):
            c.local_reset()
        c.set_estop(False)
        c.local_reset()
        self.assertEqual(c.state, State.DISARMED)
        self.assertFalse(c.position_trusted)
        self.assertFalse(c.backend_job_accepted)

    def test_reboot_invalidates_queued_commands_and_position(self):
        c = prepared()
        old = envelope(c, "arm")
        c.reboot("boot-B")
        c.connect("session-B")
        self.assertEqual(c.command(old)["reason"], "wrong_boot")
        self.assertFalse(c.position_trusted)
        self.assertIsNone(c.job_digest)
        self.assertEqual(c.state, State.DISARMED)

    def test_reboot_keeps_active_physical_fault_inhibiting(self):
        c = running()
        c.set_estop(True)
        c.reboot("boot-B")
        self.assertEqual(c.state, State.FAULT)
        self.assertTrue(c.estop_active)
        self.assertFalse(c.enable_request)

    def test_physical_faults_in_every_operational_state(self):
        for state in (State.READY, State.RUNNING, State.HOLD_REQUESTED, State.HELD):
            for fault in ("estop", "drive", "physical_enable"):
                with self.subTest(state=state, fault=fault):
                    c = prepared()
                    send(c, "arm")
                    if state != State.READY:
                        send(c, "start")
                    if state in (State.HOLD_REQUESTED, State.HELD):
                        send(c, "hold")
                    if state == State.HELD:
                        c.acknowledge_stopped()
                    if fault == "estop":
                        c.set_estop(True)
                    elif fault == "drive":
                        c.set_drive_fault(True)
                    else:
                        c.set_physical_enable(False)
                    self.assertEqual(c.state, State.FAULT)
                    self.assertFalse(c.motion_request)
                    self.assertFalse(c.enable_request)
                    c.assert_invariants()

    def test_deterministic_fault_injection_traces(self):
        rng = random.Random(82541)
        events = 0
        for trial in range(50):
            c = running(Config(hmi_loss_policy=rng.choice(("hold", "continue_local"))))
            for _ in range(80):
                choice = rng.randrange(8)
                if choice == 0:
                    c.motion_progress()
                elif choice == 1:
                    c.advance(rng.randrange(0, 30))
                elif choice == 2 and c.session_id:
                    c.command(envelope(c, rng.choice(tuple(sorted(c.ACTIONS)))))
                elif choice == 3:
                    c.disconnect()
                elif choice == 4 and c.session_id is None:
                    c.connect(f"trial-{trial}-event-{events}")
                elif choice == 5:
                    c.set_drive_fault(True)
                elif choice == 6 and c.state == State.HOLD_REQUESTED:
                    c.acknowledge_stopped()
                elif choice == 7 and c.session_id:
                    packet = envelope(c, "start")
                    packet["boot_id"] = "foreign-boot"
                    before = c.state
                    self.assertFalse(c.command(packet)["accepted"])
                    self.assertEqual(c.state, before)
                c.assert_invariants()
                if c.state == State.FAULT:
                    self.assertFalse(c.enable_request or c.motion_request)
                events += 1
        self.assertEqual(events, 4000)

    def test_invalid_configuration(self):
        for config in ({"motion_watchdog_ms": 0}, {"hmi_lease_ms": True},
                       {"stop_ack_timeout_ms": -1}, {"hmi_loss_policy": "guess"}):
            with self.subTest(config=config), self.assertRaises(ValueError):
                Config(**config)


if __name__ == "__main__":
    unittest.main()
