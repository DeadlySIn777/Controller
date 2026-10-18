"""Appliance presentation only: no devices, machine store writes or shell launch.

Plans and hashes detect stale/conflicting local changes, not malicious authors.
Service mode is deliberately visible session state, never an authorization grant.
"""
from contextlib import contextmanager
from copy import deepcopy
import hashlib
import json
import os
from pathlib import Path
import re
import stat
import tempfile
import time
import uuid

from controller_config import package_archive

DEFAULTS = {"display_scale": 1, "reduced_motion": False, "startup_page": "home"}
PRESERVED = ["machine_configuration", "machine_backups", "calibration", "offline_entitlements",
             "ai_allowance", "diagnostics", "job_files"]
GUARDS = {"machine_commands": [], "physical_authority": False, "motion_authorized": False,
          "api_calls": 0, "terminal_available": False}
MAX_STATE = 64 * 1024
MAX_PACKAGE = 16 * 1024 * 1024
MAX_INVENTORY = 32 * 1024 * 1024
MAX_FILES = 32
MAX_SCAN = 128
PLAN_SECONDS = 300


class ApplianceError(ValueError):
    def __init__(self, code, message):
        self.code = code
        super().__init__(message)

    def as_dict(self):
        return {"code": self.code, "message": str(self)}


def require(condition, code, message):
    if not condition:
        raise ApplianceError(code, message)


def canonical(value):
    try:
        return json.dumps(value, sort_keys=True, separators=(",", ":"), allow_nan=False).encode("utf-8")
    except (ValueError, TypeError, RecursionError) as error:
        raise ApplianceError("APPLIANCE_FORMAT", "Expected bounded finite JSON") from error


def digest(value):
    return hashlib.sha256(canonical(value)).hexdigest()


def load_json(raw):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, "APPLIANCE_FORMAT", "Duplicate JSON field")
            result[key] = value
        return result
    try:
        return json.loads(raw, object_pairs_hook=pairs,
                          parse_constant=lambda _: (_ for _ in ()).throw(ValueError()))
    except (ValueError, UnicodeError, RecursionError) as error:
        if isinstance(error, ApplianceError):
            raise
        raise ApplianceError("APPLIANCE_FORMAT", "Invalid finite JSON") from error


def preferences(value):
    require(type(value) is dict and set(value) == set(DEFAULTS), "APPLIANCE_PREFERENCES", "Unknown or missing preference fields")
    require(type(value["display_scale"]) in (int, float) and value["display_scale"] in (1, 1.25, 1.5),
            "APPLIANCE_PREFERENCES", "Text size must be 1, 1.25 or 1.5")
    require(type(value["reduced_motion"]) is bool, "APPLIANCE_PREFERENCES", "Reduced motion must be boolean")
    require(type(value["startup_page"]) is str and value["startup_page"] in ("home", "files", "settings"),
            "APPLIANCE_PREFERENCES", "Unknown startup page")
    result = deepcopy(value)
    # One canonical representation survives a browser JSON round trip (1.0 -> 1).
    result["display_scale"] = 1 if result["display_scale"] == 1 else result["display_scale"]
    return result


def _linked(info):
    return stat.S_ISLNK(info.st_mode) or bool(getattr(info, "st_file_attributes", 0) & 0x400)


def _directory(path, missing_ok=False):
    path = Path(path).absolute()
    require(not path.drive.startswith("\\\\"), "APPLIANCE_PATH", "Network paths are outside the local appliance contract")
    for item in reversed([path, *path.parents]):
        try:
            info = item.lstat()
        except FileNotFoundError:
            if missing_ok and item == path:
                return None
            raise ApplianceError("APPLIANCE_PATH", "Expected an existing local directory")
        require(not _linked(info) and stat.S_ISDIR(info.st_mode), "APPLIANCE_PATH", "Linked or non-directory paths are forbidden")
    return info


def _identity(info):
    return info.st_dev, info.st_ino


def _read(path, limit):
    parent = _directory(path.parent)
    before = path.lstat()
    require(not _linked(before) and stat.S_ISREG(before.st_mode) and before.st_nlink == 1 and before.st_size <= limit,
            "APPLIANCE_FILE", "Expected a bounded, unlinked regular file")
    fd = os.open(path, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0))
    try:
        opened = os.fstat(fd)
        require(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1 and _identity(before) == _identity(opened),
                "APPLIANCE_FILE_CHANGED", "File changed while opening")
        with os.fdopen(fd, "rb", closefd=False) as stream:
            data = stream.read(limit + 1)
        after = os.fstat(fd)
        now = path.lstat()
        require(len(data) <= limit and len(data) == opened.st_size and
                (opened.st_size, opened.st_mtime_ns, opened.st_ctime_ns) == (after.st_size, after.st_mtime_ns, after.st_ctime_ns) and
                not _linked(now) and _identity(now) == _identity(opened) and _identity(parent) == _identity(_directory(path.parent)),
                "APPLIANCE_FILE_CHANGED", "File or directory changed during inspection")
        return data
    finally:
        os.close(fd)


def _uuid(value):
    require(type(value) is str, "APPLIANCE_REQUEST", "Expected a canonical request UUID")
    try:
        require(str(uuid.UUID(value)) == value, "APPLIANCE_REQUEST", "Expected a canonical request UUID")
    except ValueError as error:
        raise ApplianceError("APPLIANCE_REQUEST", "Expected a canonical request UUID") from error


class ApplianceService:
    def __init__(self, workspace_directory, packages_directory=None, *, clock=time.time):
        self.workspace = Path(workspace_directory).absolute()
        self.directory = self.workspace / "appliance"
        self.path = self.directory / "preferences.json"
        self.packages = Path(packages_directory).absolute() if packages_directory is not None else self.workspace / "packages"
        self.clock = clock
        self._service_mode = False

    def _empty(self):
        return {"schema_version": 1, "kind": "appliance_preferences", "store_id": None, "revision": 0,
                "preferences": deepcopy(DEFAULTS), "undo": None, "requests": []}

    def _state(self):
        if _directory(self.workspace, missing_ok=True) is None:
            return self._empty()
        if _directory(self.directory, missing_ok=True) is None:
            return self._empty()
        try:
            value = load_json(_read(self.path, MAX_STATE))
        except FileNotFoundError:
            return self._empty()
        require(type(value) is dict and set(value) == set(self._empty()) | {"integrity_sha256"},
                "APPLIANCE_STORE", "Invalid preference envelope")
        expected = value.pop("integrity_sha256")
        require(type(expected) is str and digest(value) == expected, "APPLIANCE_INTEGRITY", "Preference integrity mismatch; preserve the file for inspection")
        require(type(value["schema_version"]) is int and value["schema_version"] == 1 and value["kind"] == "appliance_preferences",
                "APPLIANCE_STORE", "Unsupported preference schema")
        _uuid(value["store_id"])
        require(type(value["revision"]) is int and 1 <= value["revision"] <= 0x7fffffff,
                "APPLIANCE_STORE", "Invalid preference revision")
        preferences(value["preferences"])
        undo = value["undo"]
        if undo is not None:
            require(type(undo) is dict and set(undo) == {"reset_id", "revision", "preferences"} and
                    type(undo["revision"]) is int and undo["revision"] == value["revision"], "APPLIANCE_STORE", "Invalid undo binding")
            _uuid(undo["reset_id"])
            preferences(undo["preferences"])
        require(type(value["requests"]) is list and len(value["requests"]) <= 32, "APPLIANCE_STORE", "Invalid request history")
        seen = set()
        for row in value["requests"]:
            require(type(row) is dict and set(row) == {"request_id", "plan_sha256", "result"}, "APPLIANCE_STORE", "Invalid request receipt")
            _uuid(row["request_id"])
            require(row["request_id"] not in seen and type(row["plan_sha256"]) is str and
                    re.fullmatch(r"[0-9a-f]{64}", row["plan_sha256"]), "APPLIANCE_STORE", "Conflicting request receipts")
            seen.add(row["request_id"])
            result = row["result"]
            require(type(result) is dict and set(result) == {"operation", "scope", "revision", "preferences", "preserved", "request_id"} and
                    result["operation"] in ("preferences", "reset", "undo") and result["scope"] == "appliance_preferences" and
                    type(result["revision"]) is int and 1 <= result["revision"] <= value["revision"] and
                    result["request_id"] == row["request_id"] and result["preserved"] == PRESERVED,
                    "APPLIANCE_STORE", "Invalid preference receipt")
            preferences(result["preferences"])
        return value

    def _binding(self, state):
        # Empty stores still belong to the explicitly selected workspace. Without
        # this field, a first-use preview from A could be confirmed into empty B.
        local_identity = os.path.normcase(os.path.normpath(str(self.workspace)))
        return {"workspace_id": hashlib.sha256(local_identity.encode("utf-8")).hexdigest(),
                "store_id": state["store_id"], "revision": state["revision"], "integrity_sha256": digest(state)}

    def status(self):
        state = self._state()
        return {"schema_version": 1, "preferences": deepcopy(state["preferences"]), "revision": state["revision"],
                "binding": self._binding(state), "initialized": state["store_id"] is not None,
                "undo_available": state["undo"] is not None, "service_mode": self._service_mode,
                "service_mode_scope": "presentation_only; not authentication or machine permission",
                "factory_reset_scope": "appliance_preferences", "full_machine_reset": {"available": False,
                "code": "MACHINE_RESET_BLOCKED", "reason": "Machine storage, protected backups, entitlement and calibration reset contract is not qualified"},
                "preserved": deepcopy(PRESERVED), **deepcopy(GUARDS)}

    def service_mode(self, enabled, confirmation):
        require(type(enabled) is bool and confirmation == ("ENTER SERVICE VIEW" if enabled else "LEAVE SERVICE VIEW"),
                "APPLIANCE_CONFIRMATION", "Deliberate service-view confirmation is required")
        self._service_mode = enabled
        return self.status()

    def _plan(self, state, operation, target, created=None):
        created = int(self.clock()) if created is None else created
        words = {"preferences": "SAVE INTERFACE PREFERENCES", "reset": "RESET INTERFACE PREFERENCES", "undo": "RESTORE INTERFACE PREFERENCES"}
        plan = {"schema_version": 1, "operation": operation, "scope": "appliance_preferences", "binding": self._binding(state),
                "preferences": deepcopy(target), "diff": [{"field": k, "before": state["preferences"][k], "after": target[k]}
                                                          for k in sorted(DEFAULTS) if state["preferences"][k] != target[k]],
                "preserved": deepcopy(PRESERVED), "confirmation": words[operation], "created_at": created,
                "expires_at": created + PLAN_SECONDS, "undo_reset_id": state["undo"]["reset_id"] if operation == "undo" else None,
                **deepcopy(GUARDS)}
        return {**plan, "plan_sha256": digest(plan)}

    def preview_preferences(self, patch, expected_revision):
        state = self._state()
        require(type(expected_revision) is int and state["revision"] == expected_revision, "APPLIANCE_STALE", "Preferences changed; review a fresh preview")
        require(type(patch) is dict and patch and set(patch) <= set(DEFAULTS), "APPLIANCE_PREFERENCES", "Expected known preference fields")
        return self._plan(state, "preferences", preferences({**state["preferences"], **patch}))

    def preview_reset(self, scope="appliance_preferences"):
        require(scope == "appliance_preferences", "MACHINE_RESET_BLOCKED", "Full machine reset is not qualified; machine data is preserved")
        return self._plan(self._state(), "reset", DEFAULTS)

    def preview_undo(self):
        state = self._state()
        require(state["undo"] is not None, "APPLIANCE_UNDO", "No current interface reset is available to undo")
        return self._plan(state, "undo", state["undo"]["preferences"])

    @contextmanager
    def _lock(self):
        if _directory(self.workspace, missing_ok=True) is None:
            try:
                self.workspace.mkdir(mode=0o700)
            except FileExistsError:
                pass
        _directory(self.workspace)
        if _directory(self.directory, missing_ok=True) is None:
            try:
                self.directory.mkdir(mode=0o700)
            except FileExistsError:
                pass
        parent = _directory(self.directory)
        path = self.directory / "preferences.lock"
        try:
            before = path.lstat()
        except FileNotFoundError:
            before = None
        require(before is None or not _linked(before) and stat.S_ISREG(before.st_mode) and before.st_nlink == 1,
                "APPLIANCE_LOCK", "Preference lock must be an unlinked regular file")
        fd = os.open(path, os.O_CREAT | os.O_RDWR | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_NONBLOCK", 0) | getattr(os, "O_BINARY", 0), 0o600)
        locked = False
        try:
            opened = os.fstat(fd)
            require(stat.S_ISREG(opened.st_mode) and opened.st_nlink == 1 and
                    (before is None or _identity(before) == _identity(opened)) and
                    _identity(path.lstat()) == _identity(opened) and _identity(_directory(self.directory)) == _identity(parent),
                    "APPLIANCE_LOCK", "Preference lock changed")
            try:
                if os.name == "nt":
                    import msvcrt
                    msvcrt.locking(fd, msvcrt.LK_NBLCK, 1)
                else:
                    import fcntl
                    fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
            except OSError as error:
                raise ApplianceError("APPLIANCE_BUSY", "Another local interface writer owns the preference lock") from error
            locked = True
            if opened.st_size == 0:
                os.write(fd, b"\0")
            yield
        finally:
            if locked:
                if os.name == "nt":
                    os.lseek(fd, 0, os.SEEK_SET)
                    msvcrt.locking(fd, msvcrt.LK_UNLCK, 1)
                else:
                    fcntl.flock(fd, fcntl.LOCK_UN)
            os.close(fd)

    def _write(self, state):
        data = canonical({**state, "integrity_sha256": digest(state)}) + b"\n"
        require(len(data) <= MAX_STATE, "APPLIANCE_SIZE", "Preference state exceeds its bound")
        parent = _directory(self.directory)
        pending = None
        published = False
        try:
            fd, name = tempfile.mkstemp(prefix=".preferences-", suffix=".pending", dir=self.directory)
            pending = Path(name)
            with os.fdopen(fd, "wb") as handle:
                handle.write(data)
                handle.flush()
                os.fsync(handle.fileno())
            require(_identity(_directory(self.directory)) == _identity(parent), "APPLIANCE_PATH", "Preference directory changed before publication")
            os.replace(pending, self.path)
            published = True
            pending = None
            if os.name != "nt":
                descriptor = os.open(self.directory, os.O_RDONLY | getattr(os, "O_DIRECTORY", 0))
                try:
                    os.fsync(descriptor)
                finally:
                    os.close(descriptor)
        except OSError as error:
            if not published:
                try:
                    published = _read(self.path, MAX_STATE) == data
                except (OSError, ApplianceError):
                    pass
            raise ApplianceError("APPLIANCE_PUBLICATION_UNCERTAIN" if published else "APPLIANCE_IO",
                                 "Preference save acknowledgement failed; inspect status before retrying") from error
        finally:
            if pending is not None:
                pending.unlink(missing_ok=True)

    def confirm(self, plan, request_id, confirmation):
        _uuid(request_id)
        require(type(plan) is dict and len(canonical(plan)) <= MAX_STATE and type(plan.get("plan_sha256")) is str,
                "APPLIANCE_PLAN", "Expected a bounded reviewed plan")
        payload = {k: v for k, v in plan.items() if k != "plan_sha256"}
        require(digest(payload) == plan["plan_sha256"], "APPLIANCE_PLAN", "Plan integrity mismatch")
        require(type(confirmation) is str and confirmation == plan.get("confirmation"), "APPLIANCE_CONFIRMATION", "Exact review confirmation is required")
        with self._lock():
            state = self._state()
            for old in state["requests"]:
                if old["request_id"] == request_id:
                    require(old["plan_sha256"] == plan["plan_sha256"], "APPLIANCE_REQUEST_CONFLICT", "Request UUID was already used for another plan")
                    return {**deepcopy(old["result"]), "idempotent": True, **deepcopy(GUARDS)}
            require(type(plan.get("created_at")) is int and plan["created_at"] <= self.clock() < plan["created_at"] + PLAN_SECONDS,
                    "APPLIANCE_EXPIRED", "Preview expired; review preferences again")
            require(plan.get("binding") == self._binding(state), "APPLIANCE_STALE", "Preferences changed; review a fresh preview")
            operation = plan.get("operation")
            require(operation in ("preferences", "reset", "undo"), "APPLIANCE_PLAN", "Unsupported preference operation")
            if operation == "reset":
                target = deepcopy(DEFAULTS)
            elif operation == "undo":
                require(state["undo"] is not None, "APPLIANCE_UNDO", "Reset is no longer available to undo")
                target = state["undo"]["preferences"]
            else:
                target = preferences(plan.get("preferences"))
            require(plan == self._plan(state, operation, target, plan["created_at"]), "APPLIANCE_PLAN", "Plan fields differ from the reviewed operation")
            require(state["revision"] < 0x7fffffff, "APPLIANCE_REVISION", "Preference revision exhausted")
            previous = deepcopy(state["preferences"])
            state["revision"] += 1
            state["store_id"] = state["store_id"] or str(uuid.uuid4())
            state["preferences"] = deepcopy(target)
            state["undo"] = {"reset_id": request_id, "revision": state["revision"], "preferences": previous} if operation == "reset" else None
            result = {"operation": operation, "scope": "appliance_preferences", "revision": state["revision"],
                      "preferences": deepcopy(target), "preserved": deepcopy(PRESERVED), "request_id": request_id}
            state["requests"] = (state["requests"] + [{"request_id": request_id, "plan_sha256": plan["plan_sha256"], "result": result}])[-32:]
            self._write(state)
            return {**deepcopy(result), "idempotent": False, **deepcopy(GUARDS)}

    def _names(self):
        if _directory(self.workspace, missing_ok=True) is None:
            return []
        if _directory(self.packages, missing_ok=True) is None:
            return []
        names, seen = [], set()
        with os.scandir(self.packages) as entries:
            for index, entry in enumerate(entries):
                require(index < MAX_SCAN, "APPLIANCE_INVENTORY_LIMIT", "Package directory exceeds the bounded scan; no partial inventory is presented")
                if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,79}\.tar\.zst", entry.name):
                    continue
                require(entry.name.casefold() not in seen, "APPLIANCE_FILE_COLLISION", "Case-colliding package names are ambiguous")
                seen.add(entry.name.casefold())
                names.append(entry.name)
                require(len(names) <= MAX_FILES, "APPLIANCE_INVENTORY_LIMIT", "Too many packages; no partial inventory is presented")
        return sorted(names)

    def _package(self, name):
        path = self.packages / name
        raw = _read(path, MAX_PACKAGE)
        checked = package_archive.read_archive(path)
        require(checked["manifest"]["kind"] in ("config", "support"), "APPLIANCE_PACKAGE_KIND", "Files exposes configuration and support packages only")
        require(hashlib.sha256(raw).hexdigest() == checked["sha256"], "APPLIANCE_FILE_CHANGED", "Package changed between validation and download")
        row = {"package_id": hashlib.sha256(name.encode("ascii")).hexdigest(), "filename": name,
               "kind": checked["manifest"]["kind"], "size": len(raw), "sha256": checked["sha256"],
               "integrity_verified": True, "authenticates_sender": False}
        return row, raw

    def files(self):
        rows, unavailable, total = [], [], 0
        for name in self._names():
            try:
                info = (self.packages / name).lstat()
                total += info.st_size
                require(total <= MAX_INVENTORY, "APPLIANCE_INVENTORY_LIMIT", "Package inventory exceeds its total byte bound")
                row, _ = self._package(name)
                rows.append(row)
            except (ApplianceError, package_archive.ArchiveError, OSError) as error:
                if getattr(error, "code", None) == "APPLIANCE_INVENTORY_LIMIT":
                    raise
                unavailable.append({"filename": name, "downloadable": False,
                                    "error": {"code": getattr(error, "code", "APPLIANCE_FILE"),
                                              "message": "Unable to inspect this local package" if isinstance(error, OSError) else str(error)}})
        return {"schema_version": 1, "files": rows, "unavailable": unavailable, "read_only": True,
                "archive_capabilities": package_archive.capabilities(), "max_files": MAX_FILES,
                "max_scan_entries": MAX_SCAN, "max_package_bytes": MAX_PACKAGE, "max_inventory_bytes": MAX_INVENTORY,
                "arbitrary_paths_accepted": False, **deepcopy(GUARDS)}

    def download(self, package_id, expected_sha256):
        require(type(package_id) is str and re.fullmatch(r"[0-9a-f]{64}", package_id) and
                type(expected_sha256) is str and re.fullmatch(r"[0-9a-f]{64}", expected_sha256),
                "APPLIANCE_DOWNLOAD", "Opaque package identity and expected SHA-256 are required")
        matches = [name for name in self._names() if hashlib.sha256(name.encode("ascii")).hexdigest() == package_id]
        require(len(matches) == 1, "APPLIANCE_DOWNLOAD", "Package is unavailable; refresh Files")
        row, raw = self._package(matches[0])
        require(row["sha256"] == expected_sha256, "APPLIANCE_STALE", "Package changed; review a fresh inventory")
        return {"metadata": row, "data": raw, "content_type": "application/zstd", **deepcopy(GUARDS)}
