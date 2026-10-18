"""Deterministic application overlay, not an approved bootable OS release.

No installer, partition writer, downloader, device backend or firmware flasher
exists here. Existing machine stores/credentials never enter the image payload.
"""
from copy import deepcopy
import hashlib
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import stat
import tarfile

from controller_config.service import canonical, digest
from controller_config.model import ConfigurationError

DEV_PROFILE = "dev-x86_64-posix-v1"
APP = "usr/lib/controller/app"
MANIFEST = "usr/share/controller/image-manifest.json"
MAX_FILE = 4 * 1024 * 1024
MAX_PAYLOAD = 32 * 1024 * 1024
PACKAGES = ("controller_config", "controller_shell", "controller_os", "controller_lab")
EXTENSIONS = {".py", ".html", ".css", ".js"}
GUARDS = {"simulation_only": True, "physical_authority": False,
          "physical_commissioning_complete": False, "motion_authorized": False,
          "outputs_inhibited": True, "homed": False, "signed_release": False,
          "bootable_image_qualified": False}


def reject(code, message):
    raise ConfigurationError(code, message)


def profiles():
    rows = [{"id": DEV_PROFILE, "architecture": "x86_64", "scope": "offline_development_overlay",
             "stage_allowed": True, "production_approved": False, "kernel": "POSIX development; no loaded real-time qualification"}]
    for name, storage in (("cm4-lite", "SD"), ("cm4-emmc", "eMMC"), ("cm5-lite", "SD"),
                          ("cm5-emmc", "eMMC"), ("cb1", "exact revision required"), ("cb2", "exact revision required")):
        rows.append({"id": name, "architecture": "aarch64", "scope": "unqualified_compute_candidate",
                     "stage_allowed": False, "production_approved": False, "storage_candidate": storage,
                     "blockers": ["Exact compute/carrier identity and cold-start selection",
                                  "Pinned matching base image, bootloader, kernel and device tree",
                                  "Qualified transport and loaded real-time/display behavior",
                                  "Physical media/power-loss/recovery measurements"]})
    return rows


def definition(profile=DEV_PROFILE, *, allow_development=False):
    if profile != DEV_PROFILE:
        reject("OS_PROFILE_UNQUALIFIED", "No physical compute/kernel image is approved; use the explicit disconnected development profile")
    if allow_development is not True:
        reject("OS_DEVELOPMENT_OPT_IN", "Explicit development opt-in is required")
    return {"schema_version": 1, "kind": "controller_appliance_overlay", "profile_id": profile,
            "architecture": "x86_64", "kernel_contract": "posix_development_only",
            "application_command": ["/usr/bin/python3", "-m", "controller_shell", "--directory", "/var/lib/controller/workspace", "--port", "8769"],
            "bind_address": "127.0.0.1", "workspace_path": "/var/lib/controller/workspace",
            "application_path": "/usr/lib/controller/app", "ai_provider_configured": False,
            "base_image_sha256": None, "bootloader_sha256": None, "kernel_sha256": None,
            "required_base_packages": ["python3 >= 3.11", "systemd", "a qualified browser/graphical session for optional kiosk"],
            "feature_dependencies": {"compressed_packages": "CPython3.14+ compression.zstd built with libzstd; runtime availability is checked; unavailable remains visibly disabled"},
            "settings_policy": "Existing settings stay outside replaceable application image; never initialize or restore on boot",
            "recovery_policy": "Read-only inspection; deliberate existing-service backup/restore; inhibited unhomed restart",
            "units_enabled_by_builder": False, "kiosk_graphics_qualified": False,
            "release_blockers": ["Exact pinned offline base image absent", "Compute/carrier/boot/kernel not target-qualified",
                                 "Signed release/update and physical boot/power-loss recovery unqualified",
                                 "Loaded motion, graphics, storage and display timing unqualified"], **deepcopy(GUARDS)}


def _relative(name):
    if type(name) is not str or not name or "\\" in name or ":" in name:
        reject("OS_PATH", "Payload path must be canonical relative POSIX text")
    path = PurePosixPath(name)
    if path.is_absolute() or ".." in path.parts or path.as_posix() != name:
        reject("OS_PATH", "Payload path leaves the image or is not canonical")
    return name


def _read(root, name, limit=MAX_FILE):
    root = Path(root).absolute(); target = root / _relative(name)
    for parent in [target, *target.parents]:
        if parent.exists() and parent.is_symlink():
            reject("OS_LINK", "Image/source paths cannot use symbolic links")
    descriptor = os.open(target, os.O_RDONLY | getattr(os, "O_NOFOLLOW", 0) | getattr(os, "O_BINARY", 0))
    try:
        info = os.fstat(descriptor)
        if not stat.S_ISREG(info.st_mode) or info.st_nlink != 1 or info.st_size > limit:
            reject("OS_FILE", "Payload must be a bounded exclusively owned regular file")
        with os.fdopen(descriptor, "rb", closefd=False) as stream:
            body = stream.read(limit + 1)
        after = os.fstat(descriptor)
        if len(body) > limit or len(body) != info.st_size or (info.st_size, info.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            reject("OS_SOURCE_CHANGED", "File changed or exceeded its bound during inspection")
        return body
    finally:
        os.close(descriptor)


def application_sources(root):
    root = Path(root).absolute(); result = {}
    for package in PACKAGES:
        directory = root / package
        if not directory.is_dir() or directory.is_symlink():
            reject("OS_SOURCE", "Required application package is missing or linked: " + package)
        for path in sorted(directory.rglob("*")):
            if "__pycache__" in path.parts:
                continue
            if path.is_symlink():
                reject("OS_LINK", "Application source tree contains a symbolic link")
            if path.is_file() and path.suffix in EXTENSIONS:
                name = path.relative_to(root).as_posix()
                if package == "controller_lab" and name not in ("controller_lab/__init__.py", "controller_lab/cnc3_configuration.py"):
                    continue
                result[name] = _read(root, name)
    required = {f"{package}/__init__.py" for package in PACKAGES} | {"controller_os/__main__.py", "controller_shell/__main__.py",
        "controller_shell/web/index.html", "controller_shell/web/shell.js", "controller_config/web/setup.html", "controller_config/web/setup.js"}
    if not required <= set(result) or len(result) > 512 or sum(map(len, result.values())) > MAX_PAYLOAD:
        reject("OS_SOURCE", "Application closure is incomplete or exceeds image bounds")
    return result


def unit_files():
    common = "User=controller\nWorkingDirectory=/usr/lib/controller/app\nEnvironment=PYTHONPATH=/usr/lib/controller/app\nEnvironment=PYTHONDONTWRITEBYTECODE=1\nNoNewPrivileges=yes\nPrivateDevices=yes\nPrivateTmp=yes\nProtectSystem=strict\nProtectHome=yes\nProtectKernelTunables=yes\nProtectKernelModules=yes\nProtectControlGroups=yes\nRestrictSUIDSGID=yes\nLockPersonality=yes\n"
    verify = "/usr/bin/python3 -m controller_os preflight --root / --manifest /usr/share/controller/image-manifest.json --workspace /var/lib/controller/workspace --profile " + DEV_PROFILE + " --allow-development"
    files = {
        "etc/systemd/system/controller-preflight.service": "[Unit]\nDescription=Verify disconnected Controller development image\nAfter=systemd-sysusers.service systemd-tmpfiles-setup.service\nOnFailure=controller-recovery.target\n\n[Service]\nType=oneshot\nRemainAfterExit=yes\n" + common + "ExecStart=" + verify + "\n",
        "etc/systemd/system/controller-shell.service": "[Unit]\nDescription=Controller development desktop service\nRequires=controller-preflight.service\nAfter=controller-preflight.service\nOnFailure=controller-recovery.target\n\n[Service]\n" + common + "StateDirectory=controller\nReadWritePaths=/var/lib/controller\nIPAddressDeny=any\nIPAddressAllow=localhost\nUnsetEnvironment=OPENAI_API_KEY CNC3_ALLOW_DISCONNECTED_RTL_SIMULATION\nExecStart=/usr/bin/python3 -m controller_shell --directory /var/lib/controller/workspace --port 8769\nRestart=on-failure\nRestartSec=3\n",
        "etc/systemd/system/controller-recovery.service": "[Unit]\nDescription=Read-only Controller recovery inspection\n\n[Service]\nType=oneshot\n" + common + "ExecStart=/usr/bin/python3 -m controller_os recovery --root / --manifest /usr/share/controller/image-manifest.json --workspace /var/lib/controller/workspace --profile " + DEV_PROFILE + " --allow-development\n",
        "etc/systemd/system/controller-recovery.target": "[Unit]\nDescription=Controller read-only recovery; shell stopped\nRequires=controller-recovery.service\nAfter=controller-recovery.service\nConflicts=controller-shell.service\n",
        "etc/systemd/system/controller.target": "[Unit]\nDescription=Disconnected Controller development appliance\nRequires=controller-shell.service\nAfter=controller-shell.service\n",
        "etc/systemd/user/controller-kiosk.service": "[Unit]\nDescription=Optional Controller kiosk on a qualified graphical user session\nAfter=graphical-session.target\n\n[Service]\nExecStart=/usr/bin/chromium --kiosk --no-first-run --user-data-dir=%h/.local/share/controller/browser http://127.0.0.1:8769/\nRestart=on-failure\nRestartSec=3\nNoNewPrivileges=yes\n\n[Install]\nWantedBy=graphical-session.target\n",
        "etc/tmpfiles.d/controller.conf": "d /var/lib/controller 0700 controller controller -\nd /var/lib/controller/workspace 0700 controller controller -\n",
        "usr/lib/sysusers.d/controller.conf": "u controller - \"Controller development service\" /var/lib/controller\n"}
    return {name: body.encode("utf8") for name, body in files.items()}


def stage(source_root, output, *, profile=DEV_PROFILE, allow_development=False, release_id="development-r1"):
    contract = definition(profile, allow_development=allow_development)
    if type(release_id) is not str or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}", release_id):
        reject("OS_RELEASE", "Supply a bounded explicit release identifier")
    output = Path(output).absolute()
    if output.exists() or output.is_symlink():
        reject("OS_OUTPUT_EXISTS", "Image staging requires a new directory; existing files are preserved")
    for parent in output.parents:
        if parent.is_symlink():
            reject("OS_LINK", "Output parents cannot be symbolic links")
    sources = application_sources(source_root)
    payload = {f"{APP}/{name}": body for name, body in sources.items()}
    payload.update(unit_files())
    entries = {name: {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body), "mode": 0o644} for name, body in sorted(payload.items())}
    manifest = {"schema_version": 1, "kind": "controller_offline_image_manifest", "release_id": release_id,
                "definition": contract, "source_sha256": {name: hashlib.sha256(body).hexdigest() for name, body in sorted(sources.items())},
                "entries": entries, "payload_bytes": sum(len(body) for body in payload.values()),
                "checksum_is_release_authentication": False, **deepcopy(GUARDS)}
    manifest["manifest_sha256"] = digest(manifest)
    payload[MANIFEST] = canonical(manifest) + b"\n"
    output.mkdir(parents=True, exist_ok=False)
    for name, body in sorted(payload.items()):
        target = output / "rootfs" / name; target.parent.mkdir(parents=True, exist_ok=True)
        with target.open("xb") as handle:
            handle.write(body)
        target.chmod(0o644)
    # Deterministic regular-file-only archive. No secret stores, base OS,
    # kernel, device nodes, links or guessed firmware enter this overlay.
    with (output / "controller-overlay.tar").open("xb") as file:
        with tarfile.open(fileobj=file, mode="w", format=tarfile.USTAR_FORMAT) as archive:
            for name, body in sorted(payload.items()):
                info = tarfile.TarInfo(name); info.size = len(body); info.mode = 0o644
                info.mtime = 0; info.uid = info.gid = 0; info.uname = info.gname = "root"
                archive.addfile(info, io.BytesIO(body))
    receipt = {"status": "STAGED_DEVELOPMENT_OVERLAY", "manifest_sha256": manifest["manifest_sha256"],
               "overlay_sha256": hashlib.sha256((output / "controller-overlay.tar").read_bytes()).hexdigest(),
               "source_files": len(sources), "payload_files": len(entries), "payload_bytes": manifest["payload_bytes"],
               "existing_settings_included": False, "services_installed_or_enabled": False, "network_modified": False,
               "paid_api_calls": 0, "device_writes": 0, **deepcopy(GUARDS)}
    with (output / "receipt.json").open("x", encoding="utf8") as file:
        json.dump(receipt, file, indent=2); file.write("\n")
    return receipt


def verify_image(root, *, manifest_path=MANIFEST, profile=DEV_PROFILE, allow_development=False, exact_overlay=False):
    contract = definition(profile, allow_development=allow_development)
    def pairs(values):
        data = {}
        for key, value in values:
            if key in data:
                reject("OS_MANIFEST", "Duplicate manifest field")
            data[key] = value
        return data
    try:
        manifest = json.loads(_read(root, manifest_path).decode("utf8"), object_pairs_hook=pairs,
                              parse_constant=lambda value: reject("OS_MANIFEST", "Nonfinite manifest value"))
        fields = {"schema_version", "kind", "release_id", "definition", "source_sha256", "entries", "payload_bytes", "checksum_is_release_authentication", "manifest_sha256", *GUARDS}
        if type(manifest) is not dict or set(manifest) != fields or type(manifest["schema_version"]) is not int or manifest["schema_version"] != 1:
            reject("OS_MANIFEST", "Unsupported image manifest schema")
        payload = {key: value for key, value in manifest.items() if key != "manifest_sha256"}
        if digest(payload) != manifest["manifest_sha256"] or canonical(manifest["definition"]) != canonical(contract):
            reject("OS_MANIFEST", "Manifest or declared profile changed")
        if manifest["kind"] != "controller_offline_image_manifest" or manifest["checksum_is_release_authentication"] is not False or any(manifest[key] is not expected for key, expected in GUARDS.items()):
            reject("OS_AUTHORITY", "Image must retain every disconnected guard")
        if type(manifest["release_id"]) is not str or not re.fullmatch(r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,63}", manifest["release_id"]):
            reject("OS_RELEASE", "Image release identifier is invalid")
        installed = application_sources(Path(root) / APP)
        source_hashes = {name: hashlib.sha256(body).hexdigest() for name, body in sorted(installed.items())}
        if manifest["source_sha256"] != source_hashes:
            reject("OS_SOURCE_CLOSURE", "Installed application closure differs from image manifest")
        expected = {f"{APP}/{name}": body for name, body in installed.items()}; expected.update(unit_files())
        if type(manifest["entries"]) is not dict or set(manifest["entries"]) != set(expected):
            reject("OS_SOURCE_CLOSURE", "Image omits or adds application/service files")
        for name, expected_body in expected.items():
            body = _read(root, name)
            if body != expected_body or manifest["entries"][name] != {"sha256": hashlib.sha256(body).hexdigest(), "bytes": len(body), "mode": 0o644}:
                reject("OS_INTEGRITY", "Image file differs from verified payload: " + name)
        if type(manifest["payload_bytes"]) is not int or manifest["payload_bytes"] != sum(len(body) for body in expected.values()):
            reject("OS_MANIFEST", "Payload byte count differs")
        if exact_overlay:
            files = {p.relative_to(root).as_posix() for p in Path(root).rglob("*") if p.is_file() or p.is_symlink()}
            if files != set(expected) | {manifest_path}:
                reject("OS_SOURCE_CLOSURE", "Overlay includes unlisted files")
        return manifest
    except ConfigurationError:
        raise
    except (OSError, ValueError, TypeError, KeyError, RecursionError, UnicodeError) as error:
        reject("OS_MANIFEST", "Unable to verify bounded image manifest: " + type(error).__name__)
