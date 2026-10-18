"""LinuxCNC NML adapter, restricted to this repository's software simulation.

Construction imports no LinuxCNC module and opens no channel. The caller must
explicitly connect. This is a service adapter, not a servo loop, safety system,
authentication layer, or hardware driver. A successful poll proves API access,
not a deadline-qualified motion cycle.
"""
from dataclasses import asdict, dataclass
import hashlib
import importlib
import json
import math
from pathlib import Path
import time
import uuid


class BackendError(RuntimeError):
    pass


@dataclass(frozen=True)
class ControlRequest:
    session: str
    sequence: int
    token: str
    expires_at: float
    action: str
    arguments_json: str


@dataclass(frozen=True)
class StatusSample:
    session: str
    sequence: int
    sampled_at: float
    ini_filename: str
    task_state: int
    task_mode: int
    interp_state: int
    enabled: bool
    estop: bool
    homed: tuple
    actual_position: tuple
    commanded_position: tuple
    paused: bool
    in_position: bool
    velocity: float
    motion_line: int
    program: str
    errors: tuple

    def as_dict(self):
        return asdict(self)


class LinuxCNCBackend:
    ACTIONS = frozenset({"reset_estop", "power_on", "power_off", "home_all", "mdi", "open_program", "run", "pause", "resume", "abort"})

    def __init__(self, *, api=None, clock=time.monotonic, status_max_age=0.5,
                 request_ttl=0.5, completion_timeout=5.0, simulation_only=True):
        for name, value in (("status_max_age", status_max_age), ("request_ttl", request_ttl), ("completion_timeout", completion_timeout)):
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not math.isfinite(value) or value <= 0:
                raise ValueError(name + " must be positive and finite")
        if simulation_only is not True:
            raise ValueError("Hardware control is not implemented by this adapter")
        self.profile = Path(__file__).resolve().parent / "profiles/sim/controller.ini"
        self._api = api
        self._clock = clock
        self.status_max_age = status_max_age
        self.request_ttl = request_ttl
        self.completion_timeout = completion_timeout
        self.connected = False
        self.session = None
        self.sample = None
        self._command = self._status = self._errors = None
        self._pending = {}
        self._issue_sequence = 0
        self._consumed_sequence = 0
        self._sample_sequence = 0
        self._loaded = None
        self._controller_error = None

    def _verify_profile_files(self):
        try:
            manifest = json.loads(self.profile.with_name("manifest.json").read_text())
        except (OSError, ValueError) as exc:
            raise BackendError("Simulation profile manifest is unreadable or malformed") from exc
        if not isinstance(manifest, dict) or manifest.get("mode") != "software-only" or manifest.get("schema") != 1:
            raise BackendError("Simulation profile manifest is invalid")
        digests = manifest.get("sha256")
        if not isinstance(digests, dict):
            raise BackendError("Simulation profile manifest is invalid")
        for name in ("controller.ini", "simulation.hal", "display-client"):
            try:
                digest = hashlib.sha256(self.profile.with_name(name).read_bytes()).hexdigest()
            except OSError as exc:
                raise BackendError("Simulation profile file is unreadable: " + name) from exc
            if digests.get(name) != digest:
                raise BackendError("Simulation profile changed: " + name)

    def connect(self):
        """Attach only to the exact checked-in simulation profile; never launch it."""
        if self.connected:
            raise BackendError("Already connected; disconnect explicitly before reconnecting")
        self._verify_profile_files()
        if self._api is None:
            try:
                self._api = importlib.import_module("linuxcnc")
            except ImportError as exc:
                raise BackendError("LinuxCNC Python module is unavailable; use the isolated Linux simulation runtime") from exc
        try:
            status = self._api.stat()
            status.poll()
            self._check_profile_identity(status)
            # Creating a command channel happens only after status/profile checks.
            command = self._api.command()
            errors = self._api.error_channel()
            self._status, self._command, self._errors = status, command, errors
            self.session = str(uuid.uuid4())
            self._pending.clear()
            self._issue_sequence = self._consumed_sequence = self._sample_sequence = 0
            self._loaded = None
            self._controller_error = None
            self.connected = True
            return self.poll()
        except Exception as exc:
            self.disconnect()
            if isinstance(exc, BackendError):
                raise
            raise BackendError("LinuxCNC attach failed; no commands sent") from exc

    def disconnect(self):
        """Drop service authority; does not claim to stop an independent controller."""
        self.connected = False
        self.session = None
        self.sample = None
        self._pending.clear()
        self._loaded = None
        self._command = self._status = self._errors = None

    def _check_profile_identity(self, status):
        if Path(status.ini_filename).resolve() != self.profile:
            raise BackendError("Refusing an unknown or physical-machine LinuxCNC profile")
        if getattr(status, "joints", 0) != 3 or getattr(status, "axis_mask", 0) != 7:
            raise BackendError("Simulation status is not initialized as the expected XYZ profile")

    def _require_connection(self):
        if not self.connected:
            raise BackendError("Backend is disconnected; explicit connection required")

    def poll(self):
        self._require_connection()
        try:
            self._status.poll()
            self._check_profile_identity(self._status)
            messages = []
            for _ in range(100):
                item = self._errors.poll()
                if item is None:
                    break
                messages.append((int(item[0]), str(item[1])))
            fatal = {self._api.NML_ERROR, self._api.OPERATOR_ERROR}
            for code, message in messages:
                if code in fatal:
                    self._controller_error = message
            s = self._status
            actual = tuple(float(x) for x in s.actual_position)
            commanded = tuple(float(x) for x in s.position)
            if not all(math.isfinite(x) for x in actual + commanded + (float(s.current_vel),)):
                raise BackendError("Non-finite controller position")
            self._sample_sequence += 1
            self.sample = StatusSample(
                self.session, self._sample_sequence, self._clock(),
                # Controller-reported identity (already checked above), not the
                # adapter's expected path, so evidence records an observation.
                str(s.ini_filename),
                s.task_state, s.task_mode, s.interp_state, bool(s.enabled), bool(s.estop),
                tuple(bool(x) for x in s.homed[:s.joints]), actual, commanded,
                bool(s.paused), bool(s.inpos), float(s.current_vel), int(s.motion_line),
                str(s.file), tuple(messages))
            return self.sample
        except Exception as exc:
            self.disconnect()
            raise BackendError("Status channel/profile lost; authority discarded") from exc

    def issue(self, action, **arguments):
        """Mint an expiring local service request, not a network auth credential."""
        self._require_connection()
        if action not in self.ACTIONS:
            raise BackendError("Unknown control action")
        now = self._clock()
        self._pending = {k: v for k, v in self._pending.items() if v.expires_at > now}
        if len(self._pending) >= 64:
            raise BackendError("Too many outstanding requests")
        self._issue_sequence += 1
        request = ControlRequest(self.session, self._issue_sequence, str(uuid.uuid4()),
                                 now + self.request_ttl, action,
                                 json.dumps(arguments, sort_keys=True, allow_nan=False))
        self._pending[request.token] = request
        return request

    def execute(self, request):
        self._require_connection()
        if not isinstance(request, ControlRequest) or request.session != self.session:
            raise BackendError("Request belongs to an expired connection")
        minted = self._pending.pop(request.token, None)
        if minted != request or request.sequence <= self._consumed_sequence:
            raise BackendError("Unknown, modified, replayed, or reordered request")
        # Consume even rejected state transitions: they cannot become valid later.
        self._consumed_sequence = request.sequence
        if self._clock() >= request.expires_at:
            raise BackendError("Control request expired")
        if request.action != "abort" and (self.sample is None or self._clock() - self.sample.sampled_at >= self.status_max_age):
            raise BackendError("Status is stale; poll and issue a new request")
        sample = self.poll()
        if self._clock() >= request.expires_at:
            raise BackendError("Control request expired during status refresh")
        def send(function, *arguments, wait=True):
            return self._send(function, *arguments, deadline=request.expires_at, wait=wait)
        args = json.loads(request.arguments_json)
        expected_args = {"mdi": {"line"}, "open_program": {"name", "sha256"}}.get(request.action, set())
        if set(args) != expected_args:
            raise BackendError("Unexpected control arguments")
        api, cmd, action = self._api, self._command, request.action
        if action == "abort":
            self._loaded = None
            return send(cmd.abort)
        if action == "reset_estop":
            if sample.task_state != api.STATE_ESTOP:
                raise BackendError("Controller is not in ESTOP")
            return send(cmd.state, api.STATE_ESTOP_RESET)
        if action == "power_off":
            self._loaded = None
            return send(cmd.state, api.STATE_OFF)
        if self._controller_error is not None:
            raise BackendError("Controller error latched; inspect the error and reconnect explicitly: " + self._controller_error)
        if action == "power_on":
            if sample.estop or sample.task_state not in (api.STATE_OFF, api.STATE_ESTOP_RESET):
                raise BackendError("Reset simulated ESTOP before enabling")
            return send(cmd.state, api.STATE_ON)
        if sample.task_state != api.STATE_ON or sample.estop or not sample.enabled:
            raise BackendError("Simulated machine is not enabled")
        if action in ("home_all", "mdi", "open_program", "run") and sample.interp_state != api.INTERP_IDLE:
            raise BackendError("Interpreter must be idle")
        if action == "home_all":
            send(cmd.mode, api.MODE_MANUAL)
            send(cmd.teleop_enable, 0)
            return send(cmd.home, -1, wait=False)
        if not all(sample.homed):
            raise BackendError("All simulated joints must be homed")
        if action == "mdi":
            line = args["line"]
            if not isinstance(line, str) or not line.strip() or len(line.encode("utf-8")) > 254 or "\n" in line or "\r" in line or "\x00" in line:
                raise BackendError("MDI requires one nonempty line of at most 254 UTF-8 bytes")
            send(cmd.mode, api.MODE_MDI)
            return send(cmd.mdi, line, wait=False)
        if action == "open_program":
            name = args["name"]
            if not isinstance(name, str) or Path(name).name != name or not name.endswith(".ngc"):
                raise BackendError("Only a named simulation program may be opened")
            path = (self.profile.parent / "programs" / name).resolve()
            if path.parent != (self.profile.parent / "programs").resolve() or not path.is_file():
                raise BackendError("Program is outside the simulation program directory")
            digest = hashlib.sha256(path.read_bytes()).hexdigest()
            if digest != args["sha256"]:
                raise BackendError("Program digest mismatch")
            send(cmd.mode, api.MODE_AUTO)
            result = send(cmd.program_open, str(path))
            self._loaded = (path, digest)
            return result
        if action in ("run", "resume"):
            if self._loaded is None:
                raise BackendError("Program must be explicitly reopened after reconnect/abort")
            path, digest = self._loaded
            if hashlib.sha256(path.read_bytes()).hexdigest() != digest or Path(sample.program).resolve() != path:
                self._loaded = None
                raise BackendError("Loaded program identity changed")
            if sample.task_mode != api.MODE_AUTO:
                raise BackendError("Controller is not in AUTO mode")
        if action == "run":
            return send(cmd.auto, api.AUTO_RUN, 0, wait=False)
        if action == "pause":
            if sample.task_mode != api.MODE_AUTO or sample.interp_state == api.INTERP_IDLE:
                raise BackendError("No automatic program is running")
            return send(cmd.auto, api.AUTO_PAUSE, wait=False)
        if action == "resume":
            if not sample.paused:
                raise BackendError("Controller has not reported paused")
            return send(cmd.auto, api.AUTO_RESUME, wait=False)
        raise BackendError("Action is not implemented")

    def _send(self, function, *args, deadline, wait=True):
        if self._clock() >= deadline:
            raise BackendError("Control request expired before sending command")
        try:
            function(*args)
            # Motion and hold commands stay asynchronous so abort remains usable.
            # Completion is a later status observation, never inferred from dispatch.
            result = self._command.wait_complete(self.completion_timeout) if wait else self._api.RCS_DONE
            if result != self._api.RCS_DONE:
                raise BackendError("Command failed or completion timed out; it will not be retried")
            sample = self.poll()
            fatal = {self._api.NML_ERROR, self._api.OPERATOR_ERROR}
            if any(code in fatal for code, _ in sample.errors):
                raise BackendError("LinuxCNC reported an error: " + repr(sample.errors))
            return sample
        except Exception as exc:
            self.disconnect()
            if isinstance(exc, BackendError):
                raise
            raise BackendError("Command channel failed; reconnect cannot replay the command") from exc
