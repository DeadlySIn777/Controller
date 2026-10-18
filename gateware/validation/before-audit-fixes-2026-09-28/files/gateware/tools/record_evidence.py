#!/usr/bin/env python3
"""Preserve a successful reference test run and hash its source inputs."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
log = (root / "build/simulation.log").read_bytes()
required = (
    b"ALL 180 CHECKS PASSED; pulse timing monitors passed on six channels",
    b"Python independently decoded RTL status",
    b"V e r i l a t i o n   R e p o r t: Verilator 5.048",
)
if any(marker not in log for marker in required):
    raise SystemExit("Log does not contain the expected successful reference run; do not publish evidence")
out = root / "validation"
out.mkdir(exist_ok=True)
(out / "simulation.log").write_bytes(log)
(out / "status_encoder.hex").write_bytes((root / "build/status_encoder.hex").read_bytes())
paths = sorted(path for pattern in ("rtl/*.v", "tests/*", "tools/*.py", "tools/*.sh", "PROTOCOL.md")
               for path in root.glob(pattern) if path.is_file())
manifest = {
    "recorded_utc": datetime.now(timezone.utc).isoformat(),
    "scope": "RTL functional simulation, default-top elaboration, independent codec check, lint only",
    "tools": {"iverilog": "13.0", "verilator": "5.048", "python": "3.14.7",
              "environment": "WSL GarciaMechBuilder / Alpine Linux 3.24.2"},
    "rtl_checks": 180,
    "source_sha256": {str(path.relative_to(root)).replace("\\", "/"): hashlib.sha256(path.read_bytes()).hexdigest()
                      for path in paths},
    "evidence_sha256": {name: hashlib.sha256((out / name).read_bytes()).hexdigest()
                        for name in ("simulation.log", "status_encoder.hex")},
    "not_proven": ["T20 synthesis/resource fit", "place and route/timing closure", "board pin/bank assignment",
                   "physical SPI/encoder/STEP integrity", "physical LinuxCNC realtime SPI transport/target deadlines", "machine safety"],
}
(out / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
print(f"Recorded {len(paths)} source hashes and two evidence hashes in {out / 'manifest.json'}")
