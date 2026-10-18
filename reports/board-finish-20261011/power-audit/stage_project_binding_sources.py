"""Save official KiCad tag sources for a bounded read-only API binding audit."""
import hashlib
import json
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
OUT = HERE / "project-binding-source"
FILES = {
    "pcbnew_scripting_helpers.cpp": "pcbnew/python/scripting/pcbnew_scripting_helpers.cpp",
    "board.cpp": "pcbnew/board.cpp",
    "pcbnew_jobs_handler.cpp": "pcbnew/pcbnew_jobs_handler.cpp",
    "zone_filler.cpp": "pcbnew/zone_filler.cpp",
    "board_design_settings.cpp": "pcbnew/board_design_settings.cpp",
}


def main():
    OUT.mkdir(exist_ok=True)
    rows = []
    for name, relative in FILES.items():
        url = "https://gitlab.com/kicad/code/kicad/-/raw/10.0.4/" + relative
        target = OUT / name
        data = target.read_bytes() if target.exists() else urllib.request.urlopen(url, timeout=45).read()
        if b"#include" not in data or b"<html" in data[:1000].lower():
            raise ValueError("Official response is not C++ source: " + url)
        if target.exists() and target.read_bytes() != data:
            raise ValueError("Previously staged source differs: " + str(target))
        target.write_bytes(data)
        rows.append({"path": str(target), "url": url, "tag": "10.0.4",
                     "sha256": hashlib.sha256(data).hexdigest(), "bytes": len(data)})
    (OUT / "sources.json").write_text(json.dumps(rows, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(rows, indent=2))


if __name__ == "__main__":
    main()
