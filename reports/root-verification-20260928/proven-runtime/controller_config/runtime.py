"""Stopped CNC1 calibration service for the explicit actual-RTL LinuxCNC profile.

The file-only machine-profile service stays separate: this adapter advertises only
discovered motion resources and supports step scales, not invented field I/O.
Python is outside the compiled cyclic path. No hardware device is opened.
"""
from contextlib import contextmanager
from copy import deepcopy
import json
import hashlib
import math
import os
from pathlib import Path
import time

from .model import ConfigurationError
from .service import read_json, export_json

PROFILE = Path(__file__).resolve().parents[1] / "cnc1/profiles/sim/controller.ini"
PLAN_KEYS = {"schema", "binding", "before", "after", "diff", "expires_monotonic_ns"}


def binding(snapshot):
    return {key: deepcopy(snapshot[key]) for key in
            ("profile", "instance", "session", "revision", "epoch", "capabilities")}


def require_stopped(snapshot, *, locked=False):
    if (snapshot["enabled"] or not snapshot["machine_off"] or
        not snapshot["interpreter_idle"] or not snapshot["in_position"] or
        snapshot["driver_state"] != 4 or not snapshot["feedback_valid"] or
        snapshot["permission"] or snapshot["config_locked"] != locked):
        raise ConfigurationError("RUNTIME_UNSAFE", "Stopped, idle, ready and disarmed runtime required")


def validate_scales(scales, snapshot):
    if type(scales) is not list or len(scales) != snapshot["capabilities"]["step_channels"]:
        raise ConfigurationError("RUNTIME_SCALES", "Exactly one scale per discovered step channel required")
    for index, value in enumerate(scales):
        if type(value) not in (int, float) or not 1 <= value <= 1_000_000 or not math.isfinite(value):
            raise ConfigurationError("RUNTIME_SCALES", "Finite scale between 1 and 1000000 required", str(index))
        velocity = snapshot["capabilities"]["joint_max_velocity"][index]
        if velocity is None:
            if value != snapshot["scales"][index]:
                raise ConfigurationError("UNMAPPED_CHANNEL", "No LinuxCNC joint/profile for this discovered channel", str(index))
        elif value * velocity > snapshot["capabilities"]["max_steps_per_second"]:
            raise ConfigurationError("PULSE_RATE_LIMIT", "Scale and configured joint velocity exceed discovered DDS ceiling", str(index))
    return [float(value) for value in scales]


def changes(before, after):
    return [{"path": f"/step_channels/{index}/steps_per_unit", "before": old, "after": new}
            for index, (old, new) in enumerate(zip(before, after)) if old != new]


class RuntimeConfigurationService:
    """One service contract used by CLI, tests and future UI; no auto-enable API."""
    def __init__(self, adapter, clock=time.monotonic_ns):
        self.adapter, self.clock = adapter, clock

    def snapshot(self):
        return self.adapter.snapshot()

    def preview(self, scales):
        state = self.snapshot()
        require_stopped(state)
        after = validate_scales(scales, state)
        if after == state["scales"]:
            raise ConfigurationError("NO_CHANGE", "The requested scales already match the runtime")
        return {"schema": "cnc1-runtime-scale-plan/1", "binding": binding(state),
                "before": state["scales"], "after": after,
                "diff": changes(state["scales"], after),
                "expires_monotonic_ns": self.clock() + 60_000_000_000}

    def _validate_plan(self, plan, state):
        if type(plan) is not dict or set(plan) != PLAN_KEYS or plan["schema"] != "cnc1-runtime-scale-plan/1":
            raise ConfigurationError("RUNTIME_PLAN", "Unsupported runtime plan structure")
        expiry = plan["expires_monotonic_ns"]
        if type(expiry) is not int or not self.clock() < expiry <= self.clock() + 60_000_000_000:
            raise ConfigurationError("RUNTIME_EXPIRED", "Preview expired or has an invalid deadline")
        if plan["binding"] != binding(state) or plan["before"] != state["scales"]:
            raise ConfigurationError("RUNTIME_STALE", "Runtime session, epoch, revision, capabilities or scales changed")
        after = validate_scales(plan["after"], state)
        if plan["diff"] != changes(plan["before"], after) or not plan["diff"]:
            raise ConfigurationError("RUNTIME_PLAN", "Plan diff does not match its requested scales")
        return after

    def apply(self, plan):
        plan = deepcopy(plan)
        with self.adapter.exclusive():
            state = self.snapshot()
            self._require_volatile(state)
            require_stopped(state)
            after = self._validate_plan(plan, state)
            self.adapter.transaction(1, state, deadline=plan['expires_monotonic_ns'])
            committed = self._activate_locked(after, state, lambda stopped: self._validate_plan(plan, stopped), deadline=plan['expires_monotonic_ns'])
            self.adapter.transaction(3, committed, deadline=plan['expires_monotonic_ns'])
            result = self.snapshot()
            require_stopped(result)
            return {"applied": True, "diff": plan["diff"], "runtime": result,
                    "homing_required": True, "motion_started": False,
                    "persistence": "runtime_only; no machine-profile or cartridge mutation"}

    @staticmethod
    def _require_volatile(state):
        if state.get("persistence_required", False):
            raise ConfigurationError("PERSISTENT_AUTHORITY_REQUIRED", "Use the persistent configuration service; ordinary apply/recover cannot bypass it")

    def _activate_locked(self, scales, before, validate=None, *, deadline=None):
        """Shared activation core. Caller owns lock, journal policy and release."""
        require_stopped(self.snapshot(), locked=True)
        self.adapter.unhome()
        stopped = self.snapshot()
        require_stopped(stopped, locked=True)
        if any(stopped["homed"]):
            raise ConfigurationError("UNHOME_FAILED", "LinuxCNC still reports a homed joint; inhibit remains acquired")
        if binding(stopped) != binding(before):
            raise ConfigurationError("RUNTIME_STALE", "Runtime changed during activation; inhibit remains acquired")
        if validate:
            validate(stopped)
        after = validate_scales(scales, stopped)
        self.adapter.transaction(2, stopped, after, deadline=deadline)
        committed = self.snapshot()
        require_stopped(committed, locked=True)
        if committed["scales"] != after or committed["revision"] != before["revision"] + 1:
            raise ConfigurationError("COMMIT_UNCERTAIN", "Inspect runtime; inhibit remains acquired")
        return committed

    def recover_inhibit(self):
        with self.adapter.exclusive():
            state = self.snapshot()
            self._require_volatile(state)
            require_stopped(state, locked=True)
            self.adapter.unhome()
            state = self.snapshot()
            require_stopped(state, locked=True)
            if any(state["homed"]):
                raise ConfigurationError("UNHOME_FAILED", "Cannot release inhibit while joints remain homed")
            self.adapter.transaction(3, state)
            return {"inhibit_released": True, "motion_started": False, "runtime": self.snapshot()}


class LinuxCNCRTLAdapter:
    """LinuxCNC status is authoritative here; fixture flags are never consulted."""
    def __init__(self):
        if os.environ.get("CNC1_ALLOW_RTL_SIMULATION") != "1":
            raise ConfigurationError("SIMULATION_REQUIRED", "Explicit CNC1 RTL simulation environment required")
        try:
            import hal
            import linuxcnc
        except ImportError as error:
            raise ConfigurationError("RUNTIME_UNAVAILABLE", "LinuxCNC Python and HAL modules are required inside the isolated simulator") from error
        self.hal, self.linuxcnc = hal, linuxcnc
        self.observer = hal.component("cnc1_runtime_config_" + str(os.getpid()))
        self.observer.ready()
        self.stat, self.command = linuxcnc.stat(), linuxcnc.command()
        self.ini = linuxcnc.ini(str(PROFILE))
        self.boot_id = Path('/proc/sys/kernel/random/boot_id').read_text().strip()
        self.snapshot()

    def get(self, name):
        return self.hal.get_value("cnc1." + name)

    def snapshot(self):
        for _ in range(1000):
            serial = self.get("snapshot-sequence")
            if serial & 1:
                time.sleep(.001)
                continue
            self.stat.poll()
            stat = self.stat
            if not stat.ini_filename or Path(stat.ini_filename).resolve() != PROFILE.resolve() or stat.joints != 3 or stat.axis_mask != 7:
                raise ConfigurationError("FOREIGN_RUNTIME", "Only the exact CNC1 XYZ actual-RTL profile is supported")
            channels = int(self.get("step-channels"))
            caps = {"step_channels": channels, "encoder_channels": int(self.get("encoder-channels")),
                    "frequency_channels": int(self.get("frequency-channels")), "features": int(self.get("features")),
                    "core_hz": int(self.get("core-hz")), "max_dds_rate": int(self.get("max-rate")),
                    "joint_max_velocity": [float(self.ini.find(f"JOINT_{index}", "MAX_VELOCITY")) if index < stat.joints else None for index in range(channels)]}
            caps["max_steps_per_second"] = caps["core_hz"] * caps["max_dds_rate"] / 4294967296
            profile_hash = hashlib.sha256(PROFILE.read_bytes() + (PROFILE.parent/'simulation.hal').read_bytes()).hexdigest()
            result = {"profile": str(PROFILE.resolve()),
                      "instance": [self.boot_id, int(self.get("instance-hi")), int(self.get("instance-lo"))],
                      "session": int(self.get("session")),
                      "revision": int(self.get("config-revision")), "epoch": int(self.get("runtime-epoch")),
                      "capabilities": caps, "scales": [float(self.get(f"{index}.scale")) for index in range(channels)],
                      "enabled": bool(stat.enabled), "machine_off": stat.task_state in (self.linuxcnc.STATE_OFF, self.linuxcnc.STATE_ESTOP_RESET),
                      "interpreter_idle": stat.interp_state == self.linuxcnc.INTERP_IDLE,
                      "in_position": bool(stat.inpos), "homed": list(stat.homed[:stat.joints]),
                      "driver_state": int(self.get("state")), "feedback_valid": bool(self.get("feedback-valid")),
                      "permission": bool(self.get("sim-permission")), "config_locked": bool(self.get("config-locked")),
                      "physical_hardware": False}
            result.update(persistence_required=bool(self.get('persistence-required')),
                          persistence_pending=bool(self.get('persistence-pending')),
                          persistence_generation=int(self.get('persistence-generation')),
                          persistence_hash=''.join(f'{int(self.get(f"persistence-hash-{index}")):08x}' for index in range(8)),
                          machine_id=self.ini.find('CONTROLLER_LAB','MACHINE_ID'), profile_sha256=profile_hash)
            expected_hash = os.environ.get('CNC1_PROFILE_SHA256')
            if result['persistence_required'] and expected_hash != profile_hash:
                raise ConfigurationError('PROFILE_CHANGED', 'Persistent runtime requires its launch-bound unchanged INI/HAL fingerprint')
            if serial == self.get("snapshot-sequence"):
                if channels != 6 or not self.get("discovered"):
                    raise ConfigurationError("CAPABILITIES_UNAVAILABLE", "Six-channel reference RTL discovery required")
                return result
        raise ConfigurationError("SNAPSHOT_BUSY", "Could not obtain a coherent driver snapshot")

    @contextmanager
    def exclusive(self):
        import fcntl
        with open("/tmp/cnc1-runtime-configuration.lock", "a") as handle:
            try:
                fcntl.flock(handle, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except BlockingIOError as error:
                raise ConfigurationError("RUNTIME_BUSY", "Another runtime configuration writer is active") from error
            try:
                yield
            finally:
                fcntl.flock(handle, fcntl.LOCK_UN)

    def transaction(self, operation, state, scales=None, persistent=None, *, deadline=None):
        if deadline is None:
            deadline=time.monotonic_ns()+5_000_000_000
        if time.monotonic_ns()>=deadline:
            raise ConfigurationError('RUNTIME_EXPIRED','Configuration request expired before staging')
        nonce = int(self.get("config-ack")) + 1
        if nonce >= 4294967295:
            raise ConfigurationError("REQUEST_EXHAUSTED", "Restart the disconnected profile before sequence exhaustion")
        values = {"config-op": operation, "config-session": state["session"],
                  "config-expected-revision": state["revision"], "config-expected-epoch": state["epoch"],
                  'config-deadline-hi':deadline>>32, 'config-deadline-lo':deadline&0xffffffff}
        if scales is not None:
            values.update({f"{index}.config-scale": value for index, value in enumerate(scales)})
        if persistent is not None:
            values['persistent-generation-request'] = persistent['generation']
            values.update({f'persistent-hash-request-{index}':int(persistent['sha256'][index*8:index*8+8],16) for index in range(8)})
        for name, value in values.items():
            self.hal.set_p("cnc1." + name, str(value))
        if time.monotonic_ns()>=deadline:
            raise ConfigurationError('RUNTIME_EXPIRED','Configuration request expired while staging; no request published')
        self.hal.set_p("cnc1.config-request", str(nonce))
        until = time.monotonic() + 5
        while time.monotonic() < until:
            if self.get("config-ack") == nonce:
                result = int(self.get("config-result"))
                if result:
                    raise ConfigurationError("COMPILED_GUARD_REJECTED", f"Cyclic guard rejected operation {operation}: code {result}")
                # Ack is set during write before outputs; wait for published result.
                current = self.snapshot()
                expected_revision = state["revision"] + (operation == 2)
                persistent_ok = (operation != 4 or current['persistence_pending']) and (
                    operation != 5 or (not current['persistence_pending'] and
                    current['persistence_generation'] == persistent['generation'] and
                    current['persistence_hash'] == persistent['sha256']))
                if current["revision"] == expected_revision and current["config_locked"] == (operation != 3) and persistent_ok:
                    return
            time.sleep(.002)
        raise ConfigurationError("COMMIT_UNCERTAIN", "Cyclic transaction timed out; inspect runtime and acquired inhibit")

    def unhome(self):
        for function, argument in ((self.command.mode, self.linuxcnc.MODE_MANUAL),
                                   (self.command.teleop_enable, 0), (self.command.unhome, -1)):
            require_stopped(self.snapshot(), locked=True)
            function(argument)
            if self.command.wait_complete(5) != self.linuxcnc.RCS_DONE:
                raise ConfigurationError("UNHOME_FAILED", "LinuxCNC rejected stopped unhome sequence")
        until = time.monotonic() + 5
        while time.monotonic() < until:
            current = self.snapshot()
            require_stopped(current, locked=True)
            if not any(current["homed"]):
                return
            time.sleep(.01)
        raise ConfigurationError("UNHOME_FAILED", "LinuxCNC did not confirm unhomed state")


def main(argv=None):
    from .__main__ import JsonArgumentParser
    parser = JsonArgumentParser(prog="python -m controller_config.runtime", description=__doc__)
    commands = parser.add_subparsers(dest="operation", required=True)
    commands.add_parser("snapshot")
    preview = commands.add_parser("preview")
    preview.add_argument("--scales", nargs=6, required=True, type=float)
    preview.add_argument("--output")
    apply = commands.add_parser("apply")
    apply.add_argument("plan")
    commands.add_parser("recover-inhibit")
    try:
        args = parser.parse_args(argv)
        service = RuntimeConfigurationService(LinuxCNCRTLAdapter())
        if args.operation == "snapshot":
            value = service.snapshot()
        elif args.operation == "preview":
            value = service.preview(args.scales)
            if args.output:
                export_json(args.output, value)
        elif args.operation == "apply":
            value = service.apply(read_json(args.plan))
        else:
            value = service.recover_inhibit()
        print(json.dumps({"ok": True, "result": value}, allow_nan=False))
        return 0
    except ConfigurationError as error:
        print(json.dumps({"ok": False, "error": error.as_dict()}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
