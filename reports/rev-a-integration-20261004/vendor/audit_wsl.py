"""Read-only bounded Efinity/tool inventory; never reads license contents."""
import hashlib
import json
import os
from pathlib import Path
import shutil


def digest(path):
    h = hashlib.sha256()
    with open(path, "rb") as handle:
        for chunk in iter(lambda: handle.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


roots = ["/opt", "/usr/local", "/home", "/root"]
matches = []
errors = []
visited = 0
for root in roots:
    base = Path(root)
    def on_error(exc):
        errors.append({"path": exc.filename, "type": type(exc).__name__})
    for parent, directories, files in os.walk(base, topdown=True, onerror=on_error, followlinks=False):
        visited += 1
        depth = len(Path(parent).relative_to(base).parts)
        if depth >= 5:
            directories[:] = []
        else:
            directories[:] = [d for d in directories if d not in {".git", "node_modules", "proc", "sys", "dev"}]
        for name in directories + files:
            if any(term in name.lower() for term in ["efinity", "efinix", "efx_run"]):
                item = Path(parent) / name
                matches.append({"path": str(item), "is_directory": item.is_dir(), "is_symlink": item.is_symlink()})

tool_names = ["efx_run.py", "efx_run", "efinity", "yosys", "yosys-abc", "iverilog", "verilator", "python3", "chroot", "unshare"]
lab = Path("/root/.cache/controller-lab-linuxcnc/rootfs")
lab_paths = [lab / "usr/bin/yosys", lab / "usr/bin/yosys-abc", lab / "usr/share/yosys/efinix/cells_sim.v", lab / "usr/share/yosys/efinix/cells_map.v"]
lab_tools = []
for item in lab_paths:
    lab_tools.append({"path": str(item), "exists": item.is_file(), "sha256": digest(item) if item.is_file() else None})
os_info = {}
for line in Path("/etc/os-release").read_text().splitlines():
    if "=" in line:
        key, value = line.split("=", 1)
        if key in {"ID", "VERSION_ID", "PRETTY_NAME"}:
            os_info[key] = value.strip('"')
print(json.dumps({"surface": "GarciaMechBuilder", "os": os_info, "path_tools": {name: shutil.which(name) for name in tool_names}, "vendor_environment_names_only": sorted(k for k in os.environ if any(term in k.upper() for term in ["EFINITY", "EFINIX", "LM_LICENSE", "LICENSE_FILE"])), "search": {"roots": roots, "maximum_directory_depth": 5, "visited_directories": visited, "matched_names": matches, "errors": errors}, "existing_lab_tools": lab_tools, "license_contents_read": False}))
