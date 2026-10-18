"""Independent inert negative control; never accesses actual rootfs modules."""
import hashlib
import json
from pathlib import Path
import sys
import tempfile
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
guard = HERE.parent / "host/module_guard.py"
runner = HERE.parent / "host/run_hal.py"
original = guard.read_text(encoding="utf8")
sha = lambda path: hashlib.sha256(path.read_bytes()).hexdigest()
before = {str(path): sha(path) for path in (guard, runner)}
with tempfile.TemporaryDirectory(prefix="inert-install-", dir=HERE) as temporary:
    base = Path(temporary).resolve()
    assert base.parent == HERE.resolve()
    modules = base / "usr/lib/linuxcnc/modules"
    build = base / "work/test/build"
    out = base / "receipt"
    for item in (modules, build, out):
        item.mkdir(parents=True)
    existing = modules / "preexisting.so"
    existing.write_bytes(b"inert existing fixture")
    first = "c3rf_IS1_" + "1" * 20 + ".so"
    second = "c3rf_IS2_" + "1" * 20 + ".so"
    for name in (first, second):
        (build / name).write_bytes(b"inert candidate fixture " + name.encode())
    code = original.replace('root = Path("/root/.cache/controller-lab-linuxcnc/rootfs")', "root = Path(" + repr(str(base)) + ")")
    assert code != original
    write = Path.write_bytes
    writes = []
    def fail_second(path, data):
        if path.parent == modules and path.name == second:
            raise OSError("inert second-install failure")
        writes.append(str(path))
        return write(path, data)
    fault = None
    with patch.object(sys, "argv", [str(guard), "install", "/work/test", str(out)]), patch.object(Path, "write_bytes", fail_second):
        try:
            exec(compile(code, str(guard), "exec"), {"__name__": "__main__"})
        except OSError as error:
            fault = str(error)
    remaining_after_failure = sorted(p.name for p in modules.iterdir())
    assert fault == "inert second-install failure"
    assert first in remaining_after_failure and second not in remaining_after_failure
    assert existing.read_bytes() == b"inert existing fixture"
    with patch.object(sys, "argv", [str(guard), "restore", "/work/test", str(out)]):
        exec(compile(code, str(guard), "exec"), {"__name__": "__main__"})
    restored = sorted(p.name for p in modules.iterdir()) == ["preexisting.so"]
    assert restored
    result = {
        "status": "REPRODUCED",
        "scope": "Independent inert temporary-directory execution of actual module_guard logic; only root path redirected, second write forced to fail",
        "failure": fault,
        "remaining_modules_after_install_failure": remaining_after_failure,
        "manual_restore_reclaims_first_owned_module_and_preserves_existing": restored,
        "rootfs_modules_accessed": False,
        "product_or_runner_sources_modified": False,
        "source_sha256": before,
        "source_unchanged": all(sha(Path(name)) == value for name, value in before.items()),
        "runner_cleanup_observation": "Caller only sets installed=True after install stage success; partial install failure skips finally restore in reviewed source",
    }
    (HERE / "module-install-negative-control.json").write_text(json.dumps(result, indent=2) + "\n", encoding="utf8")
    print(json.dumps(result))
