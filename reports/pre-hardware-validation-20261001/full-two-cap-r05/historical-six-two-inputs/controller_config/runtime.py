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
import re
import time

from .model import ConfigurationError
from .service import read_json, export_json

PROFILE = Path(__file__).resolve().parents[1] / "cnc1/profiles/sim/controller.ini"
PLAN_KEYS = {"schema", "binding", "before", "after", "diff", "expires_monotonic_ns"}
# cnc1_write (cnc1/src/cnc1.c) commands, every servo period, a rate of
#   (llround(position_cmd * scale) - steps) / period
# and latches CNC1_RANGE if that rate exceeds the discovered DDS ceiling. The
# request is therefore a whole number of counts per period, at most
# floor(ceiling * period). At a steady velocity x = scale * velocity * period
# counts per period, rounding the target to whole counts asks for up to ceil(x)
# counts, and the one-cycle count-error correction adds one more count when the
# DDS lagged by a count in the previous period. Requiring
#   scale * velocity <= ceiling - 2 / period
# gives ceil(x) + 1 < x + 2 <= ceiling * period, so ceil(x) + 1 <= floor(ceiling *
# period). The remainder of that bound covers DDS rate-word rounding. It is a
# consistency check against this driver's arithmetic, not a drive qualification;
# servo jitter larger than one count of lag is not covered.
CORRECTION_MARGIN_COUNTS = 2
# Outer ceiling only: cnc1_write still faults CNC1_TIME for a zero period or one
# above 10 ms. The binding servo-period limit is the discovered watchdog bound
# below, which is 2.5 ms for the default RTL (250000 ticks at 50 MHz).
MAX_SERVO_PERIOD_NS = 10_000_000
# cnc1_read derives watchdog_ns = watchdog_ticks * 10^9 / core_hz (unsigned
# integer division) from the discovered CNC2 capability page, and cnc1_write
# latches CNC1_CONFIG before any SYNC/ARM/UPDATE frame when
#   period > watchdog_ns / 2   (again integer division),
# i.e. it accepts a period only when 2 * period <= watchdog_ns. The service
# mirrors that integer arithmetic exactly; see servo_period_bound_ns().
WATCHDOG_PERIOD_DIVISOR = 2
# The servo period and the discovered watchdog_ticks are top-level snapshot
# fields, deliberately NOT members of snapshot["capabilities"]: persistent scale
# records (cnc1-persistent-scales/1) store the capabilities dict and require an
# exact match on reload, so adding a key there would refuse every authority saved
# before the pulse-rate margin was introduced. [EMCMOT]SERVO_PERIOD lives in the
# hashed controller.ini, so saved records are already bound to it through
# profile_sha256; volatile plans bind both fields explicitly below. Every load
# re-checks the saved scales against the current snapshot's period and watchdog.
# Names for cnc1.config-result (reports/RUNTIME_CONFIGURATION.md). Codes 4 and 6
# come from the HAL wrapper only; the others from cnc1_configure or
# cnc1_persistence_commit. The message always ends with "code N".
CONFIG_RESULT_NAMES = {
    1: "unsafe state",
    2: "stale binding",
    3: "invalid operation, scales or hash/generation",
    4: "stale or duplicate HAL request",
    5: "persistent-authority gate",
    6: "HAL deadline expired",
}


def compiled_guard_error(operation, result):
    """Structured refusal for a non-zero cnc1.config-result; the code is kept as the suffix."""
    name = CONFIG_RESULT_NAMES.get(result, "unknown result")
    return ConfigurationError("COMPILED_GUARD_REJECTED",
                              f"Cyclic guard rejected operation {operation} ({name}): code {result}")


def binding(snapshot):
    result = {key: deepcopy(snapshot[key]) for key in
              ("profile", "instance", "session", "revision", "epoch", "capabilities")}
    result["servo_period_ns"] = snapshot.get("servo_period_ns")
    result["watchdog_ticks"] = snapshot.get("watchdog_ticks")
    return result


def require_stopped(snapshot, *, locked=False):
    if (snapshot["enabled"] or not snapshot["machine_off"] or
        not snapshot["interpreter_idle"] or not snapshot["in_position"] or
        snapshot["driver_state"] != 4 or not snapshot["feedback_valid"] or
        snapshot["permission"] or snapshot["config_locked"] != locked):
        raise ConfigurationError("RUNTIME_UNSAFE", "Stopped, idle, ready and disarmed runtime required")


def _u32_positive(value):
    return type(value) is int and 0 < value <= 0xFFFFFFFF


def servo_period_bound_ns(capabilities, watchdog_ticks):
    """Largest servo period (ns) cnc1_write accepts for the discovered RTL.

    Mirrors cnc1.c exactly: watchdog_ns = watchdog_ticks * 10^9 // core_hz and a
    period is refused when period > watchdog_ns // 2. The 10 ms outer ceiling is
    kept. core_hz comes from the discovered capabilities; watchdog_ticks is the
    separate top-level snapshot field read from cnc1.watchdog-ticks. Either one
    missing or unusable refuses with CAPABILITIES_UNAVAILABLE (fail closed).
    """
    core_hz = capabilities.get("core_hz") if type(capabilities) is dict else None
    if not _u32_positive(core_hz) or not _u32_positive(watchdog_ticks):
        raise ConfigurationError("CAPABILITIES_UNAVAILABLE",
            "Discovered core_hz and cnc1.watchdog-ticks are required for the servo-period check")
    watchdog_ns = watchdog_ticks * 1_000_000_000 // core_hz
    return min(MAX_SERVO_PERIOD_NS, watchdog_ns // WATCHDOG_PERIOD_DIVISOR)


def checked_servo_period_ns(snapshot):
    """Return the snapshot servo period only if the compiled driver would accept it.

    An unusable period (None, non-integer, zero, negative or above the 10 ms outer
    ceiling) keeps the existing CAPABILITIES_UNAVAILABLE refusal. A usable period
    above half the discovered watchdog interval is refused with SERVO_PERIOD_LIMIT,
    matching the CNC1_CONFIG fault cnc1_write latches before any frame.
    """
    period = snapshot.get("servo_period_ns")
    if type(period) is not int or not 0 < period <= MAX_SERVO_PERIOD_NS:
        raise ConfigurationError("CAPABILITIES_UNAVAILABLE", "Discovered DDS ceiling and profile servo period are required for the pulse-rate check")
    bound = servo_period_bound_ns(snapshot.get("capabilities"), snapshot.get("watchdog_ticks"))
    if period > bound:
        raise ConfigurationError("SERVO_PERIOD_LIMIT",
            f"[EMCMOT]SERVO_PERIOD {period} ns exceeds {bound} ns, half the discovered RTL watchdog "
            f"({snapshot['watchdog_ticks']} ticks at {snapshot['capabilities']['core_hz']} Hz); "
            "the compiled driver refuses it with CNC1_CONFIG before any frame")
    return period


def pulse_rate_limit(capabilities, period_ns):
    """Largest scale x joint velocity (steps/s) the compiled write path accepts.

    period_ns is range-checked against the 10 ms outer ceiling only; callers that
    act on a runtime snapshot (validate_scales) first pass it through
    checked_servo_period_ns(), so the margin is only ever derived for a period the
    driver's half-watchdog rule accepts.
    """
    ceiling = capabilities.get("max_steps_per_second")
    if (type(ceiling) not in (int, float) or not math.isfinite(ceiling) or ceiling <= 0 or
            type(period_ns) is not int or not 0 < period_ns <= MAX_SERVO_PERIOD_NS):
        raise ConfigurationError("CAPABILITIES_UNAVAILABLE", "Discovered DDS ceiling and profile servo period are required for the pulse-rate check")
    return {"dds_ceiling_steps_per_second": ceiling, "servo_period_ns": period_ns,
            "max_counts_per_period": math.floor(ceiling * period_ns / 1e9),
            "correction_margin_counts": CORRECTION_MARGIN_COUNTS,
            "limit_steps_per_second": ceiling - CORRECTION_MARGIN_COUNTS * 1e9 / period_ns}


def servo_period_ns(value):
    """Parse [EMCMOT]SERVO_PERIOD; None (refused by the rate check) if unusable.

    Only ASCII decimal digits are accepted (str.isdigit() also admits
    superscripts and other Unicode digits that int() rejects or reinterprets),
    and the length is bounded so int() can never raise on digit-count limits.
    """
    if type(value) is not str:
        return None
    value = value.strip()
    if not re.fullmatch(r"[0-9]{1,18}", value, flags=re.ASCII):
        return None
    return int(value)


def validate_scales(scales, snapshot):
    if type(scales) is not list or len(scales) != snapshot["capabilities"]["step_channels"]:
        raise ConfigurationError("RUNTIME_SCALES", "Exactly one scale per discovered step channel required")
    # Checked on every preview, plan validation, activation and saved-record load:
    # a profile the compiled driver would refuse is never previewed or applied.
    period = checked_servo_period_ns(snapshot)
    for index, value in enumerate(scales):
        if type(value) not in (int, float) or not 1 <= value <= 1_000_000 or not math.isfinite(value):
            raise ConfigurationError("RUNTIME_SCALES", "Finite scale between 1 and 1000000 required", str(index))
        velocity = snapshot["capabilities"]["joint_max_velocity"][index]
        if velocity is None:
            if value != snapshot["scales"][index]:
                raise ConfigurationError("UNMAPPED_CHANNEL", "No LinuxCNC joint/profile for this discovered channel", str(index))
        else:
            limit = pulse_rate_limit(snapshot["capabilities"], period)
            if value * velocity > limit["limit_steps_per_second"]:
                raise ConfigurationError("PULSE_RATE_LIMIT",
                    f"Scale x joint MAX_VELOCITY must not exceed {limit['limit_steps_per_second']:.10g} steps/s: "
                    f"DDS ceiling {limit['dds_ceiling_steps_per_second']:.10g} steps/s minus "
                    f"{limit['correction_margin_counts']} counts per {limit['servo_period_ns']} ns servo period "
                    "for count rounding and one-cycle correction", str(index))
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
                      "capabilities": caps, "servo_period_ns": servo_period_ns(self.ini.find("EMCMOT", "SERVO_PERIOD")),
                      "watchdog_ticks": int(self.get("watchdog-ticks")),
                      "scales": [float(self.get(f"{index}.scale")) for index in range(channels)],
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
                    raise compiled_guard_error(operation, result)
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
        print(json.dumps({"schema_version": 1, "ok": True, "result": value}, allow_nan=False))
        return 0
    except ConfigurationError as error:
        print(json.dumps({"schema_version": 1, "ok": False, "error": error.as_dict()}))
        return 2
    except OSError as error:
        print(json.dumps({"schema_version": 1, "ok": False,
                          "error": {"code": "IO_ERROR", "message": str(error), "path": ""}}))
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
