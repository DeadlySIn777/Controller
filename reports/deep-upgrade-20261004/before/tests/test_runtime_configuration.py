"""Service policy unit tests. Actual LinuxCNC/compiled-guard evidence is separate."""
from contextlib import contextmanager
from copy import deepcopy
import math
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout
import io
import json

from controller_config.model import ConfigurationError
from controller_config.runtime import (PROFILE, LinuxCNCRTLAdapter, RuntimeConfigurationService,
                                       pulse_rate_limit, servo_period_bound_ns, servo_period_ns,
                                       validate_scales)


def llround(value):
    """C llround: nearest integer with halves away from zero (Python round() differs)."""
    return math.floor(value + .5) if value >= 0 else -math.floor(-value + .5)


def compiled_rate_accepts(pps, core_hz=50_000_000, max_rate=0x01000000):
    """Mirror of cnc1_rate in cnc1/src/cnc1.c; False means cnc1_write latches CNC1_RANGE."""
    raw = pps * 4294967296.0 / core_hz
    return math.isfinite(raw) and abs(raw) <= max_rate


def steady_motion_faults(scale, velocity, lag_counts, period_ns=1_000_000, periods=64, phases=256):
    """Replay cnc1_write's per-period request at a steady joint velocity.

    The step counter lags the previously rounded target by lag_counts (the DDS
    emitted that many counts fewer than requested); the driver requests the whole
    difference in the next period (its one-cycle count-error correction).
    """
    per_period = scale * velocity * period_ns / 1e9
    for phase in range(phases):
        start = phase / phases
        for k in range(1, periods):
            target = start + k * per_period
            steps = llround(start + (k - 1) * per_period) - lag_counts
            if not compiled_rate_accepts((llround(target) - steps) * 1e9 / period_ns):
                return True
    return False


# Capabilities exactly as the pre-margin adapter stored them in the archived
# persistent authority cnc1/evidence/persistent/final-authority.json (generation
# 2, record sha256 3ae9fef3...). The current adapter must still produce this
# dict, because persistent records require an exact capabilities match.
PRE_MARGIN_CAPABILITIES = {"core_hz": 50000000, "encoder_channels": 2, "features": 31, "frequency_channels": 0,
                           "joint_max_velocity": [10.0, 10.0, 10.0, None, None, None], "max_dds_rate": 16777216,
                           "max_steps_per_second": 195312.5, "step_channels": 6}
DEFAULT_WATCHDOG_TICKS = 250_000


def compiled_period_accepts(period_ns, watchdog_ticks, core_hz=50_000_000):
    """Mirror of cnc1_read/cnc1_write in cnc1/src/cnc1.c (uint64 integer division).

    False means cnc1_write latches CNC1_CONFIG (half-watchdog rule) or CNC1_TIME
    (zero or above the 10 ms outer ceiling) before any frame.
    """
    watchdog_ns = watchdog_ticks * 1_000_000_000 // core_hz
    return not period_ns > watchdog_ns // 2 and 0 < period_ns <= 10_000_000


class Adapter:
    def __init__(self):
        self.value = {"profile": "explicit-unit-test-double", "instance": ["fixture",1,2], "session": 55, "revision": 0, "epoch": 8,
                      "capabilities": {"step_channels": 6, "encoder_channels": 2, "core_hz": 50_000_000,
                                       "max_steps_per_second": 195312.5,
                                       "joint_max_velocity": [10, 10, 10, None, None, None]},
                      "servo_period_ns": 1_000_000,
                      # Default RTL CNC2 page: 250000 ticks at 50 MHz = 5 ms watchdog.
                      "watchdog_ticks": DEFAULT_WATCHDOG_TICKS,
                      "scales": [200.] * 6, "enabled": False, "machine_off": True,
                      "interpreter_idle": True, "in_position": True, "homed": [True]*3,
                      "driver_state": 4, "feedback_valid": True, "permission": False,
                      "config_locked": False, "physical_hardware": False}
        self.operations = []
        self.unhome_error = False
        self.guard_error = False
        self.unhome_mutation = None

    def snapshot(self):
        return deepcopy(self.value)

    @contextmanager
    def exclusive(self):
        yield

    def transaction(self, op, state, scales=None, *, deadline=None):
        if self.guard_error:
            raise ConfigurationError("COMPILED_GUARD_REJECTED", "Injected compiled guard refusal")
        self.operations.append(op)
        if op == 1:
            self.value["config_locked"] = True
        elif op == 2:
            self.value["scales"] = scales[:]
            self.value["revision"] += 1
        elif op == 3:
            self.value["config_locked"] = False

    def unhome(self):
        if self.unhome_error:
            raise ConfigurationError("UNHOME_FAILED", "Injected failed unhome")
        self.value["homed"] = [False]*3
        if self.unhome_mutation:
            self.value.update(self.unhome_mutation)


class RuntimeConfigurationTests(unittest.TestCase):
    def setUp(self):
        self.adapter = Adapter()
        self.now = 1_000_000_000
        self.service = RuntimeConfigurationService(self.adapter, clock=lambda: self.now)

    def preview(self):
        return self.service.preview([250,200,200,200,200,200])

    def reject(self, code, function, *args):
        with self.assertRaises(ConfigurationError) as caught:
            function(*args)
        self.assertEqual(caught.exception.code, code)

    def test_preview_is_diff_without_mutation(self):
        plan = self.preview()
        self.assertEqual(plan["diff"], [{"path": "/step_channels/0/steps_per_unit", "before":200., "after":250.}])
        self.assertEqual(self.adapter.value["scales"], [200.]*6)
        self.assertEqual(self.adapter.operations, [])

    def test_apply_acquires_unhomes_commits_releases(self):
        result = self.service.apply(self.preview())
        self.assertEqual(self.adapter.operations, [1,2,3])
        self.assertEqual(result["runtime"]["scales"][0], 250)
        self.assertEqual(result["runtime"]["revision"], 1)
        self.assertFalse(any(result["runtime"]["homed"]))
        self.assertFalse(result["runtime"]["enabled"])
        self.assertFalse(result["motion_started"])

    def test_reverse_change_uses_new_preview(self):
        original = self.preview()["before"]
        self.service.apply(self.preview())
        self.service.apply(self.service.preview(original))
        self.assertEqual(self.adapter.value["scales"], original)
        self.assertEqual(self.adapter.value["revision"], 2)

    def test_noop_rejected(self):
        self.reject("NO_CHANGE", self.service.preview, [200]*6)

    def test_wrong_channel_count_rejected(self):
        self.reject("RUNTIME_SCALES", self.service.preview, [250]*8)

    def test_numerical_limits_rejected(self):
        for value in (True, "250", 0, -1, float("nan"), float("inf"), 10**1000):
            with self.subTest(value=repr(value)[:50]):
                self.reject("RUNTIME_SCALES", self.service.preview, [value,200,200,200,200,200])

    def test_actual_dds_rate_checked(self):
        self.reject("PULSE_RATE_LIMIT", self.service.preview, [20000,200,200,200,200,200])

    def test_pulse_rate_limit_keeps_driver_correction_margin(self):
        # 195312.5 steps/s DDS ceiling at a 1 ms servo period is 195 whole counts
        # per period; two counts are reserved, leaving 193312.5 steps/s.
        limit = pulse_rate_limit(self.adapter.value["capabilities"], self.adapter.value["servo_period_ns"])
        self.assertEqual(195, limit["max_counts_per_period"])
        self.assertEqual(193312.5, limit["limit_steps_per_second"])
        plan = self.service.preview([19331.25,200,200,200,200,200])
        self.assertEqual(19331.25, plan["after"][0])
        for value in (19331.26, 19500, 19531.25, 19531.26):
            with self.subTest(value=value):
                with self.assertRaises(ConfigurationError) as caught:
                    self.service.preview([value,200,200,200,200,200])
                self.assertEqual("PULSE_RATE_LIMIT", caught.exception.code)
                self.assertEqual("0", caught.exception.path)
                self.assertIn("193312.5", str(caught.exception))

    def test_apply_rechecks_margin_against_current_capabilities(self):
        plan = self.service.preview([19331.25,200,200,200,200,200])
        self.assertEqual(1_000_000, plan["binding"]["servo_period_ns"])
        self.adapter.value["servo_period_ns"] = 500_000
        self.reject("RUNTIME_STALE", self.service.apply, plan)
        self.assertEqual([], self.adapter.operations)

    def test_margin_derivation_matches_compiled_driver_arithmetic(self):
        # Accepted boundary survives count rounding plus one count of DDS lag.
        self.assertFalse(steady_motion_faults(19331.25, 10, lag_counts=0))
        self.assertFalse(steady_motion_faults(19331.25, 10, lag_counts=1))
        # The former ceiling-equal acceptance faults from rounding alone, and
        # above the new limit one count of lag can fault.
        self.assertTrue(steady_motion_faults(19531.25, 10, lag_counts=0))
        self.assertTrue(steady_motion_faults(19401, 10, lag_counts=1))
        # Documented limitation: two counts of lag (servo jitter) are not covered.
        self.assertTrue(steady_motion_faults(19331.25, 10, lag_counts=2))

    def test_limit_follows_servo_period_and_fails_closed_without_it(self):
        caps = self.adapter.value["capabilities"]
        self.adapter.value["servo_period_ns"] = 500_000
        self.assertEqual(97, pulse_rate_limit(caps, 500_000)["max_counts_per_period"])
        self.assertEqual(191312.5, pulse_rate_limit(caps, 500_000)["limit_steps_per_second"])
        self.service.preview([19131.25,200,200,200,200,200])
        self.reject("PULSE_RATE_LIMIT", self.service.preview, [19131.26,200,200,200,200,200])
        for value in (None, 0, -1, 10_000_001, 1e6, True, "1000000"):
            with self.subTest(servo_period_ns=value):
                self.adapter.value["servo_period_ns"] = value
                self.reject("CAPABILITIES_UNAVAILABLE", self.service.preview, [250,200,200,200,200,200])
        del self.adapter.value["servo_period_ns"]
        self.reject("CAPABILITIES_UNAVAILABLE", self.service.preview, [250,200,200,200,200,200])
        # A period stored inside capabilities is not a substitute for the
        # snapshot field; the check never reads the persisted identity dict.
        caps["servo_period_ns"] = 1_000_000
        self.reject("CAPABILITIES_UNAVAILABLE", self.service.preview, [250,200,200,200,200,200])

    def test_servo_period_parser_accepts_only_integer_nanoseconds(self):
        self.assertEqual(1_000_000, servo_period_ns("1000000"))
        self.assertEqual(1_000_000, servo_period_ns(" 1000000 "))
        self.assertEqual(1_000_000, servo_period_ns("1000000\n"))
        # Unicode digits: "\u00b2".isdigit() is True but int() rejects it, and
        # Arabic-Indic or fullwidth digits would otherwise parse as a period.
        # Over-long digit strings would make int() raise on Python's digit limit.
        for value in (None, "", " ", "1e6", "-1000000", "+1000000", "1000000.0", "1_000_000", 1000000,
                      "\u00b2", "1000\u00b2", "\u0661\u0660\u0660\u0660\u0660\u0660\u0660",
                      "\uff11\uff10\uff10\uff10\uff10\uff10\uff10", "1" * 5000, "1" * 19):
            with self.subTest(value=repr(value)[:40]):
                self.assertIsNone(servo_period_ns(value))

    def assert_period(self, period_ns, code=None):
        self.adapter.value["servo_period_ns"] = period_ns
        if code is None:
            self.assertEqual(250., self.service.preview([250,200,200,200,200,200])["after"][0])
        else:
            self.reject(code, self.service.preview, [250,200,200,200,200,200])
        self.assertEqual([], self.adapter.operations)

    def test_servo_period_bound_is_half_the_discovered_watchdog(self):
        # Default RTL: 250000 ticks at 50 MHz = 5 ms watchdog, so 2.5 ms is the
        # largest period cnc1_write accepts (CNC1_CONFIG above it).
        caps = self.adapter.value["capabilities"]
        self.assertEqual(2_500_000, servo_period_bound_ns(caps, DEFAULT_WATCHDOG_TICKS))
        for period in (1_000_000, 2_499_999, 2_500_000):
            with self.subTest(period=period):
                self.assertTrue(compiled_period_accepts(period, DEFAULT_WATCHDOG_TICKS))
                self.assert_period(period)
        for period in (2_500_001, 3_000_000, 6_000_000, 10_000_000):
            with self.subTest(period=period):
                self.assertFalse(compiled_period_accepts(period, DEFAULT_WATCHDOG_TICKS))
                self.assert_period(period, "SERVO_PERIOD_LIMIT")
        with self.assertRaises(ConfigurationError) as caught:
            self.service.preview([250,200,200,200,200,200])
        self.assertIn("2500000 ns", str(caught.exception))
        self.assertIn("CNC1_CONFIG", str(caught.exception))

    def test_servo_period_bound_follows_a_shorter_discovered_watchdog(self):
        # 20000 ticks at 50 MHz = 400 us watchdog: the shipped 1 ms period is refused.
        self.adapter.value["watchdog_ticks"] = 20_000
        self.assertEqual(200_000, servo_period_bound_ns(self.adapter.value["capabilities"], 20_000))
        self.assert_period(1_000_000, "SERVO_PERIOD_LIMIT")
        self.assert_period(200_001, "SERVO_PERIOD_LIMIT")
        self.assert_period(200_000)

    def test_servo_period_bound_mirrors_compiled_integer_division(self):
        # Odd and non-integral watchdog intervals: truncation happens twice in
        # cnc1.c (ticks*1e9/core_hz, then /2); the service must not round up.
        for core_hz in (50_000_000, 30_000_000, 7):
            for ticks in (1, 3, 7, 19_999, 20_000, 250_000, 250_001, 0xFFFFFFFF):
                caps = {"core_hz": core_hz}
                bound = servo_period_bound_ns(caps, ticks)
                with self.subTest(core_hz=core_hz, ticks=ticks):
                    for period in {bound - 1, bound, bound + 1} - {0, -1}:
                        self.assertEqual(compiled_period_accepts(period, ticks, core_hz),
                                         0 < period <= bound, period)

    def test_missing_watchdog_capability_refuses(self):
        for value in (None, 0, -1, True, 250_000.0, "250000", 2**32):
            with self.subTest(watchdog_ticks=value):
                self.adapter.value["watchdog_ticks"] = value
                self.assert_period(1_000_000, "CAPABILITIES_UNAVAILABLE")
        del self.adapter.value["watchdog_ticks"]
        self.assert_period(1_000_000, "CAPABILITIES_UNAVAILABLE")
        # A watchdog stored inside capabilities is not a substitute for the
        # snapshot field (the persisted identity dict is never read for it).
        self.adapter.value["capabilities"]["watchdog_ticks"] = DEFAULT_WATCHDOG_TICKS
        self.assert_period(1_000_000, "CAPABILITIES_UNAVAILABLE")
        self.adapter.value["watchdog_ticks"] = DEFAULT_WATCHDOG_TICKS
        for value in (None, 0, True, 5e7):
            with self.subTest(core_hz=value):
                self.adapter.value["capabilities"]["core_hz"] = value
                self.assert_period(1_000_000, "CAPABILITIES_UNAVAILABLE")
        del self.adapter.value["capabilities"]["core_hz"]
        self.assert_period(1_000_000, "CAPABILITIES_UNAVAILABLE")

    def test_outer_ten_millisecond_ceiling_is_kept(self):
        # Even a long discovered watchdog cannot raise the period above 10 ms,
        # where cnc1_write latches CNC1_TIME.
        self.adapter.value["watchdog_ticks"] = 0xFFFFFFFF
        self.assertEqual(10_000_000, servo_period_bound_ns(self.adapter.value["capabilities"], 0xFFFFFFFF))
        self.assert_period(10_000_000)
        self.assert_period(10_000_001, "CAPABILITIES_UNAVAILABLE")

    def test_pulse_margin_is_derived_only_for_an_accepted_period(self):
        # At the 2.5 ms bound the margin is 2 counts / 2.5 ms = 800 steps/s.
        self.adapter.value["servo_period_ns"] = 2_500_000
        limit = pulse_rate_limit(self.adapter.value["capabilities"], 2_500_000)
        self.assertEqual(488, limit["max_counts_per_period"])
        self.assertEqual(194512.5, limit["limit_steps_per_second"])
        self.service.preview([19451.25,200,200,200,200,200])
        self.reject("PULSE_RATE_LIMIT", self.service.preview, [19451.26,200,200,200,200,200])
        self.assertFalse(steady_motion_faults(19451.25, 10, lag_counts=1, period_ns=2_500_000))
        # One nanosecond above the bound, the servo-period refusal comes first:
        # no margin is ever derived for a period the driver would refuse.
        self.adapter.value["servo_period_ns"] = 2_500_001
        self.reject("SERVO_PERIOD_LIMIT", self.service.preview, [250,200,200,200,200,200])
        self.reject("SERVO_PERIOD_LIMIT", self.service.preview, [19451.25,200,200,200,200,200])

    def test_watchdog_change_after_preview_invalidates_plan(self):
        plan = self.preview()
        self.assertEqual(DEFAULT_WATCHDOG_TICKS, plan["binding"]["watchdog_ticks"])
        self.adapter.value["watchdog_ticks"] = 20_000
        self.reject("RUNTIME_STALE", self.service.apply, plan)
        self.assertEqual([], self.adapter.operations)

    def test_activation_rechecks_servo_period_before_commit(self):
        # If the bound is violated between lock and commit, activation refuses
        # before op 2 and the inhibit stays held.
        plan = self.preview()
        self.adapter.value["config_locked"] = True
        self.adapter.value["watchdog_ticks"] = 20_000
        changed = self.adapter.snapshot()
        self.reject("SERVO_PERIOD_LIMIT", self.service._activate_locked, plan["after"], changed)
        self.assertNotIn(2, self.adapter.operations)
        self.assertTrue(self.adapter.value["config_locked"])
        self.assertEqual([200.] * 6, self.adapter.value["scales"])

    def test_compiled_guard_rejection_names_result_code(self):
        names = {1: "unsafe state", 2: "stale binding", 3: "invalid operation, scales or hash/generation",
                 4: "stale or duplicate HAL request", 5: "persistent-authority gate",
                 6: "HAL deadline expired", 7: "unknown result"}
        for result, name in names.items():
            with self.subTest(result=result):
                adapter = LinuxCNCRTLAdapter.__new__(LinuxCNCRTLAdapter)
                pins = {}

                class HAL:
                    def set_p(self, pin, value):
                        pins[pin] = value

                def get(pin, result=result):
                    if pin == "config-ack":
                        return int(pins.get("cnc1.config-request", 0))
                    if pin == "config-result":
                        return result
                    return 0
                adapter.hal, adapter.get = HAL(), get
                with self.assertRaises(ConfigurationError) as caught:
                    adapter.transaction(5, self.adapter.snapshot(), persistent={"generation": 1, "sha256": "0" * 63 + "1"})
                self.assertEqual("COMPILED_GUARD_REJECTED", caught.exception.code)
                # cnc1/persistent_integration.py relies on this exact suffix.
                self.assertTrue(str(caught.exception).endswith(f"code {result}"), str(caught.exception))
                self.assertIn(f"operation 5 ({name})", str(caught.exception))

    def test_adapter_snapshot_reads_servo_period_from_profile_ini(self):
        sections, section = {}, None
        for line in PROFILE.read_text(encoding="utf-8").splitlines():
            line = line.split("#", 1)[0].strip()
            if line.startswith("[") and line.endswith("]"):
                section = sections.setdefault(line[1:-1], {})
            elif "=" in line and section is not None:
                key, value = (part.strip() for part in line.split("=", 1))
                section.setdefault(key, value)

        class Ini:
            def find(self, name, key):
                return sections.get(name, {}).get(key)

        class Stat:
            ini_filename = str(PROFILE); joints = 3; axis_mask = 7; enabled = False
            task_state = 1; interp_state = 1; inpos = True; homed = [0, 0, 0]

            def poll(self):
                pass

        class LinuxCNC:
            STATE_OFF, STATE_ESTOP_RESET, INTERP_IDLE = 1, 2, 1

        pins = {"snapshot-sequence": 2, "step-channels": 6, "encoder-channels": 2, "frequency-channels": 0,
                "features": 31, "core-hz": 50_000_000, "max-rate": 0x01000000, "discovered": True,
                "watchdog-ticks": DEFAULT_WATCHDOG_TICKS, **{f"{index}.scale": 200.0 for index in range(6)}}
        adapter = LinuxCNCRTLAdapter.__new__(LinuxCNCRTLAdapter)
        adapter.stat, adapter.ini, adapter.linuxcnc, adapter.boot_id = Stat(), Ini(), LinuxCNC(), "fixture"
        adapter.get = lambda name: pins.get(name, 0)
        snapshot = adapter.snapshot()
        self.assertEqual(1_000_000, snapshot["servo_period_ns"])
        # The watchdog is read from the cnc1.watchdog-ticks HAL pin as a separate
        # top-level field; the shipped 1 ms profile is inside the 2.5 ms bound.
        self.assertEqual(DEFAULT_WATCHDOG_TICKS, snapshot["watchdog_ticks"])
        self.assertNotIn("watchdog_ticks", snapshot["capabilities"])
        self.assertEqual(2_500_000, servo_period_bound_ns(snapshot["capabilities"], snapshot["watchdog_ticks"]))
        self.assertEqual([250., 200., 200., 200., 200., 200.], validate_scales([250, 200, 200, 200, 200, 200], snapshot))
        pins["watchdog-ticks"] = 0  # undiscovered page: fail closed
        with self.assertRaises(ConfigurationError) as caught:
            validate_scales([250, 200, 200, 200, 200, 200], adapter.snapshot())
        self.assertEqual("CAPABILITIES_UNAVAILABLE", caught.exception.code)
        pins["watchdog-ticks"] = DEFAULT_WATCHDOG_TICKS
        # The persisted identity dict is unchanged from the pre-margin adapter,
        # so authorities saved before the margin was added still match.
        self.assertEqual(PRE_MARGIN_CAPABILITIES, snapshot["capabilities"])
        self.assertNotIn("servo_period_ns", snapshot["capabilities"])
        self.assertEqual(193312.5, pulse_rate_limit(snapshot["capabilities"], snapshot["servo_period_ns"])["limit_steps_per_second"])
        # An unusable INI period reaches the service as a structured refusal,
        # never as an unstructured ValueError from snapshot().
        good_ini = adapter.ini

        class BadIni:
            def __init__(self, raw):
                self.raw = raw

            def find(self, name, key):
                if (name, key) == ("EMCMOT", "SERVO_PERIOD"):
                    return self.raw
                return good_ini.find(name, key)

        for raw in ("\u00b2", "1000\u00b2", "\u0661\u0660\u0660\u0660", None, "1e6"):
            with self.subTest(raw=repr(raw)):
                adapter.ini = BadIni(raw)
                bad = adapter.snapshot()
                self.assertIsNone(bad["servo_period_ns"])
                with self.assertRaises(ConfigurationError) as caught:
                    validate_scales([250, 200, 200, 200, 200, 200], bad)
                self.assertEqual("CAPABILITIES_UNAVAILABLE", caught.exception.code)
        adapter.ini = good_ini

    def test_unmapped_hardware_channel_not_fake_joint(self):
        self.reject("UNMAPPED_CHANNEL", self.service.preview, [250,200,200,250,200,200])

    def test_enabled_running_or_untrusted_snapshot_rejected(self):
        for key, value in (("enabled", True), ("machine_off",False), ("interpreter_idle",False),
                           ("in_position",False), ("driver_state",6), ("feedback_valid",False),
                           ("permission",True), ("config_locked",True)):
            old = self.adapter.value[key]
            self.adapter.value[key] = value
            with self.subTest(key=key):
                self.reject("RUNTIME_UNSAFE", self.preview)
            self.adapter.value[key] = old

    def test_enable_after_preview_rejected_without_write(self):
        plan = self.preview()
        self.adapter.value["enabled"] = True
        self.reject("RUNTIME_UNSAFE", self.service.apply, plan)
        self.assertEqual(self.adapter.operations, [])

    def test_stale_binding_rejected(self):
        for key in ("session", "revision", "epoch"):
            plan = self.preview()
            self.adapter.value[key] += 1
            self.reject("RUNTIME_STALE", self.service.apply, plan)
        self.assertEqual(self.adapter.operations, [])

    def test_changed_capability_invalidates_preview(self):
        plan = self.preview()
        self.adapter.value["capabilities"]["max_steps_per_second"] = 100000
        self.reject("RUNTIME_STALE", self.service.apply, plan)

    def test_new_driver_instance_invalidates_preview(self):
        plan = self.preview()
        self.adapter.value["instance"][2] += 1
        self.reject("RUNTIME_STALE", self.service.apply, plan)

    def test_expired_plan_rejected(self):
        plan = self.preview()
        self.now = plan["expires_monotonic_ns"]
        self.reject("RUNTIME_EXPIRED", self.service.apply, plan)

    def test_future_deadline_rejected(self):
        plan = self.preview()
        plan["expires_monotonic_ns"] += 1
        self.reject("RUNTIME_EXPIRED", self.service.apply, plan)

    def test_modified_diff_rejected(self):
        plan = self.preview()
        plan["after"][0] = 300
        self.reject("RUNTIME_PLAN", self.service.apply, plan)

    def test_unsupported_plan_key_rejected(self):
        plan = self.preview()
        plan["enable"] = True
        self.reject("RUNTIME_PLAN", self.service.apply, plan)

    def test_replay_rejected(self):
        plan = self.preview()
        self.service.apply(plan)
        self.reject("RUNTIME_STALE", self.service.apply, plan)

    def test_unhome_failure_leaves_compiled_inhibit(self):
        plan = self.preview()
        self.adapter.unhome_error = True
        self.reject("UNHOME_FAILED", self.service.apply, plan)
        self.assertTrue(self.adapter.value["config_locked"])
        self.assertEqual(self.adapter.operations, [1])
        self.assertEqual(self.adapter.value["scales"][0], 200)

    def test_runtime_transition_between_acquire_commit_leaves_inhibit(self):
        plan = self.preview()
        self.adapter.unhome_mutation = {"epoch": 9}
        self.reject("RUNTIME_STALE", self.service.apply, plan)
        self.assertTrue(self.adapter.value["config_locked"])
        self.assertEqual(self.adapter.operations, [1])

    def test_compiled_guard_rejection_propagates(self):
        plan = self.preview()
        self.adapter.guard_error = True
        self.reject("COMPILED_GUARD_REJECTED", self.service.apply, plan)
        self.assertEqual(self.adapter.operations, [])

    def test_callers_plan_mutation_cannot_change_inflight_commit_or_diff(self):
        plan = self.preview()
        original_unhome = self.adapter.unhome
        def mutate_callers_plan():
            original_unhome()
            plan["after"][0] = 300
            plan["diff"][0]["after"] = 300
        self.adapter.unhome = mutate_callers_plan
        result = self.service.apply(plan)
        self.assertEqual(result["runtime"]["scales"][0], 250)
        self.assertEqual(result["diff"][0]["after"], 250)

    def test_explicit_inhibit_recovery_never_enables(self):
        self.adapter.value["config_locked"] = True
        result = self.service.recover_inhibit()
        self.assertFalse(result["runtime"]["enabled"])
        self.assertFalse(any(result["runtime"]["homed"]))
        self.assertEqual(self.adapter.operations, [3])

    def test_recovery_requires_acquired_stopped_runtime(self):
        self.reject("RUNTIME_UNSAFE", self.service.recover_inhibit)

    def test_adapter_slow_staging_does_not_publish_expired_request(self):
        adapter=LinuxCNCRTLAdapter.__new__(LinuxCNCRTLAdapter)
        writes=[]
        class HAL:
            def set_p(self,name,value):writes.append((name,value))
        adapter.hal=HAL();adapter.get=lambda name:0
        with patch('controller_config.runtime.time.monotonic_ns',side_effect=[10,20]):
            self.reject('RUNTIME_EXPIRED',lambda:adapter.transaction(3,self.adapter.snapshot(),deadline=15))
        self.assertFalse(any(name=='cnc1.config-request' for name,value in writes))

    def test_cli_versioned_success_and_structured_failures(self):
        from controller_config.runtime import main
        for error,code in ((None,None),(ConfigurationError('SIMULATION_REQUIRED','opt in'),'SIMULATION_REQUIRED'),(OSError('unavailable state'),'IO_ERROR')):
            with self.subTest(code=code), patch('controller_config.runtime.LinuxCNCRTLAdapter',return_value=self.adapter,side_effect=error), redirect_stdout(io.StringIO()) as output:
                result=main(['snapshot'])
            value=json.loads(output.getvalue())
            self.assertEqual(value['schema_version'],1)
            self.assertEqual(result,2 if error else 0)
            self.assertEqual(value['ok'],not bool(error))
            if error:self.assertEqual(value['error']['code'],code)
        self.adapter.value.update(config_locked=True, enabled=True)
        self.reject("RUNTIME_UNSAFE", self.service.recover_inhibit)


if __name__ == "__main__":
    unittest.main()
