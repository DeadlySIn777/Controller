"""Service policy unit tests. Actual LinuxCNC/compiled-guard evidence is separate."""
from contextlib import contextmanager
from copy import deepcopy
import math
import unittest

from controller_config.model import ConfigurationError
from controller_config.runtime import RuntimeConfigurationService


class Adapter:
    def __init__(self):
        self.value = {"profile": "explicit-unit-test-double", "instance": ["fixture",1,2], "session": 55, "revision": 0, "epoch": 8,
                      "capabilities": {"step_channels": 6, "encoder_channels": 2,
                                       "max_steps_per_second": 195312.5,
                                       "joint_max_velocity": [10, 10, 10, None, None, None]},
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

    def transaction(self, op, state, scales=None):
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
        self.adapter.value.update(config_locked=True, enabled=True)
        self.reject("RUNTIME_UNSAFE", self.service.recover_inhibit)


if __name__ == "__main__":
    unittest.main()
