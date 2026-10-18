"""Independent failure controls of corrected guard using inert modules only."""
import hashlib
import json
import os
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
results = []
for mode in ["second_write_fails", "torn_second_pending_write", "lost_second_link_acknowledgment", "second_fsync_fails"]:
    with tempfile.TemporaryDirectory(prefix="atomic-install-", dir=HERE) as temporary:
        base = Path(temporary).resolve()
        assert base.parent == HERE.resolve()
        modules = base / "usr/lib/linuxcnc/modules"
        build = base / "work/test/build"
        out = base / "receipt"
        for item in (modules, build, out):
            item.mkdir(parents=True)
        existing = modules / "preexisting.so"
        existing_bytes = b"inert existing fixture"
        existing.write_bytes(existing_bytes)
        first = "c3rf_IS1_" + "1" * 20 + ".so"
        second = "c3rf_IS2_" + "1" * 20 + ".so"
        for name in (first, second):
            (build / name).write_bytes(b"inert candidate fixture " + name.encode())
        code = original.replace('root = Path("/root/.cache/controller-lab-linuxcnc/rootfs")', "root = Path(" + repr(str(base)) + ")")
        assert code != original
        write, link, fsync = Path.write_bytes, os.link, os.fsync
        fsync_calls = []
        def fail_write(path, data):
            if path.parent == modules and path.name.startswith("." + second + ".") and mode in ["second_write_fails", "torn_second_pending_write"]:
                if mode == "torn_second_pending_write":
                    write(path, data[:9])
                raise OSError(mode)
            return write(path, data)
        def fail_link(source, target):
            result = link(source, target)
            if Path(target).name == second and mode == "lost_second_link_acknowledgment":
                raise OSError(mode)
            return result
        def fail_fsync(fd):
            fsync_calls.append(fd)
            if len(fsync_calls) == 2 and mode == "second_fsync_fails":
                raise OSError(mode)
            return fsync(fd)
        error = None
        with patch.object(sys, "argv", [str(guard), "install", "/work/test", str(out)]), patch.object(Path, "write_bytes", fail_write), patch.object(os, "link", fail_link), patch.object(os, "fsync", fail_fsync):
            try:
                exec(compile(code, str(guard), "exec"), {"__name__": "__main__"})
            except OSError as fault:
                error = str(fault)
        assert error == mode, (mode, error)
        names = sorted(p.name for p in modules.iterdir())
        assert first in names and "preexisting.so" in names
        assert not any(p.name.startswith(".") for p in modules.iterdir()), "pending copy removed after failure"
        assert (second in names) == (mode == "lost_second_link_acknowledgment")
        for name in (first, second):
            if (modules / name).exists():
                assert sha(modules / name) == sha(build / name), "no torn module was published"
        assert existing.read_bytes() == existing_bytes
        with patch.object(sys, "argv", [str(guard), "restore", "/work/test", str(out)]):
            exec(compile(code, str(guard), "exec"), {"__name__": "__main__"})
        assert sorted(p.name for p in modules.iterdir()) == ["preexisting.so"]
        assert existing.read_bytes() == existing_bytes
        results.append({"case": mode, "status": "PASS", "owned_modules_published_before_failure": [n for n in names if n != "preexisting.so"], "no_torn_module_published": True, "no_pending_copy_retained": True, "original_inventory_restored": True})
result = {"status": "PASS", "cases": results, "scope": "Actual corrected module_guard logic with only root directory redirected to inert temporary fixtures; source code unchanged", "source_sha256": before, "source_unchanged": all(sha(Path(name)) == value for name, value in before.items()), "actual_rootfs_modules_accessed": False, "physical_evidence": False}
assert result["source_unchanged"]
out = HERE / "module-install-corrected-controls.json"
with out.open("x", encoding="utf8") as handle:
    json.dump(result, handle, indent=2)
    handle.write("\n")
print(json.dumps(result))
