"""Change permissions only inside the new isolated UUID-keyed image fixture."""
from pathlib import Path
import re
import sys

work=Path(sys.argv[1])
assert re.fullmatch(r"/work/controller-os-[0-9a-f]{32}",str(work)) and work.is_dir() and not work.is_symlink()
for path in (work/"rootfs").rglob("*"):
    assert not path.is_symlink() and path.resolve().is_relative_to(work)
    path.chmod(0o755 if path.is_dir() else 0o644)
workspace=work/"workspace"
assert workspace.is_dir() and not workspace.is_symlink()
for path in workspace.iterdir():
    assert path.is_file() and not path.is_symlink()
    path.chmod(0o444)
workspace.chmod(0o555)
