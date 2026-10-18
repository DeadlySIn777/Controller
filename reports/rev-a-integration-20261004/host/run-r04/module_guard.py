"""Preserve existing installed rootfs modules; only remove exact own binaries."""
import hashlib
import json
import re
import sys
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
    binaries = list((work / "build").glob("cnc3_refusal_*.so"))
    assert len(binaries) == 2
    for p in binaries:
        assert re.fullmatch(r"cnc3_refusal_IS[12]_[0-9a-f]{32}\.so", p.name)
        assert not (modules / p.name).exists(), "never overwrite an installed module"
    for p in binaries:
        (modules / p.name).write_bytes(p.read_bytes())
        (modules / p.name).chmod(0o755)
    print(json.dumps({"existing_modules": len(before), "temporary_modules": [p.name for p in binaries]}))
elif action == "restore":
    before = json.loads(before_path.read_text())
    for p in (work / "build").glob("cnc3_refusal_*.so"):
        assert re.fullmatch(r"cnc3_refusal_IS[12]_[0-9a-f]{32}\.so", p.name)
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
