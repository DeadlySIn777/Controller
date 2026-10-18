"""Read-only startup and recovery; successful boot never grants motion."""
from copy import deepcopy
import hashlib
import platform
from pathlib import Path
import sys

from controller_config.model import ConfigurationError
from controller_config.setup_readiness import ReadinessService
from controller_config.setup_service import SetupService, GUARDS as SETUP_GUARDS
from controller_config.package_archive import capabilities as package_capabilities
from controller_lab.cnc3_configuration import configuration_binding
from .image import DEV_PROFILE, GUARDS, MANIFEST, verify_image, reject, _read


def observed_host():
    return {"os": platform.system(), "architecture": platform.machine().lower(),
            "python": list(sys.version_info[:3]), "kernel_release": platform.release()}


def settings_status(workspace):
    workspace = Path(workspace).absolute(); path = workspace / "setup.json"
    if workspace.is_symlink() or path.is_symlink():
        reject("OS_SETTINGS", "Preserved settings may not be a symbolic link")
    checksum = lambda: hashlib.sha256(_read(workspace, "setup.json", 2_000_000)).hexdigest() if path.exists() else None
    before = checksum()
    try:
        snapshot = SetupService(path).status()
        if any(snapshot.get(key) != expected or type(snapshot.get(key)) is not type(expected) for key, expected in SETUP_GUARDS.items()):
            reject("OS_SETTINGS_AUTHORITY", "Saved setup must retain disconnected guards")
        readiness = ReadinessService(workspace).status()
    except ConfigurationError:
        raise
    except (OSError, ValueError, TypeError) as error:
        reject("OS_SETTINGS", "Settings inspection failed; preserve files for recovery: " + type(error).__name__)
    after = checksum()
    if before != after:
        reject("OS_SETTINGS_CHANGED", "Settings changed during startup inspection; retry in a stopped service state")
    binding = None
    if snapshot["initialized"]:
        binding = configuration_binding(snapshot)
    if readiness["configuration_binding"] != binding:
        reject("OS_SETTINGS_CHANGED", "Readiness and captured settings identify different reviewed generations")
    return {"initialized": snapshot["initialized"], "settings_sha256": before,
            "configuration_binding": binding, "readiness": readiness, "settings_written": False}


def preflight(root, workspace, *, manifest_path=MANIFEST, profile=DEV_PROFILE, allow_development=False):
    manifest = verify_image(root, manifest_path=manifest_path, profile=profile, allow_development=allow_development)
    host = observed_host()
    if host["os"] != "Linux" or host["architecture"] not in ("x86_64", "amd64") or tuple(host["python"]) < (3, 11, 0):
        reject("OS_HOST_PROFILE", "This overlay runs only on the explicit Linux x86_64 Python3.11+ development host")
    return {"status": "DEVELOPMENT_SHELL_START_ALLOWED", "manifest_sha256": manifest["manifest_sha256"],
            "observed_host": host, "settings": settings_status(workspace),
            "compressed_packages": package_capabilities(),
            "kernel_realtime_qualified": False, "physical_machine_start_allowed": False,
            "paid_api_calls": 0, "device_connections": 0, **deepcopy(GUARDS)}


def recovery(root, workspace, *, manifest_path=MANIFEST, profile=DEV_PROFILE, allow_development=False):
    checks = {}
    for name, callback in (("image", lambda: verify_image(root, manifest_path=manifest_path, profile=profile, allow_development=allow_development)),
                           ("settings", lambda: settings_status(workspace))):
        try:
            result = callback()
            checks[name] = {"status": "PASS", "manifest_sha256": result.get("manifest_sha256")} if name == "image" else {"status": "PASS", **result}
        except (ConfigurationError, OSError, ValueError) as error:
            checks[name] = {"status": "BLOCKED", "code": getattr(error, "code", "OS_IO"), "message": str(error)}
    return {"status": "READ_ONLY_RECOVERY", "checks": checks, "automatic_restore": False,
            "next_action": "Preserve settings and inspect/export through the existing setup CLI; review any restore deliberately",
            "settings_written": False, "physical_machine_start_allowed": False, "paid_api_calls": 0, **deepcopy(GUARDS)}
