"""Preserve existing installed rootfs modules; only remove exact own binaries."""
import hashlib
import json
import os
import re
import sys
import tempfile
from pathlib import Path
root = Path("/root/.cache/controller-lab-linuxcnc/rootfs")
modules = root / "usr/lib/linuxcnc/modules"
work = root / sys.argv[2].lstrip("/")
out = Path(sys.argv[3])
action = sys.argv[1]
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
inventory = lambda: {p.name: sha(p) for p in sorted(modules.glob("*.so"))}
before_path = out / "installed-modules-before.json"
if action == "install":
    before = inventory()
    before_path.write_text(json.dumps(before, indent=2) + "\n")
    binaries = list((work / "build").glob("c3rf_*.so"))
    assert len(binaries) == 2
    for p in binaries:
        assert re.fullmatch(r"c3rf_IS[12]_[0-9a-f]{20}\.so", p.name)
        assert not (modules / p.name).exists(), "never overwrite an installed module"
    for p in binaries:
        # Publish only a completed copy. A failed/torn write never creates a
        # module with a bad digest that the hash-sensitive restore cannot remove.
        fd, temporary = tempfile.mkstemp(prefix="." + p.name + ".", dir=modules)
        os.close(fd)
        pending = Path(temporary)
        try:
            pending.write_bytes(p.read_bytes())
            pending.chmod(0o755)
            with pending.open("rb") as ready:
                os.fsync(ready.fileno())
            os.link(pending, modules / p.name)  # atomic and never overwrites
        finally:
            pending.unlink(missing_ok=True)
    print(json.dumps({"existing_modules": len(before), "temporary_modules": [p.name for p in binaries]}))
elif action == "restore":
    before = json.loads(before_path.read_text())
    for p in (work / "build").glob("c3rf_*.so"):
        assert re.fullmatch(r"c3rf_IS[12]_[0-9a-f]{20}\.so", p.name)
        target = modules / p.name
        assert target.resolve().parent == modules.resolve() and p.name not in before
        if target.exists():
            assert sha(target) == sha(p), "refuse removal if own temporary module changed"
            target.unlink()
    after = inventory()
    (out / "installed-modules-after.json").write_text(json.dumps(after, indent=2) + "\n")
    assert before == after, "installed modules changed"
    print(json.dumps({"existing_module_inventory_preserved": True, "modules": len(after)}))
else:
    raise ValueError(action)
