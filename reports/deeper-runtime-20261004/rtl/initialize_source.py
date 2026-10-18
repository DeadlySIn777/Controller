"""Create a versioned SIM-only derivative without touching frozen source."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = ROOT / "gateware/v3/runtime"
STAGE = ROOT / "reports/cnc3-is2-profile-20261002/profile-candidate-r02/rtl"
inventory = []
for name in ("cnc3_stepgen_runtime.v", "cnc3_encoder_runtime.v", "cnc3_alarm_filter.v",
             "cnc3_spi_transport_stateful.v", "cnc3_rate_admission_serial.v"):
    source = STAGE / name
    data = source.read_bytes()
    with (OUT / name).open("xb") as file:
        file.write(data)
    inventory.append({"source": source.relative_to(ROOT).as_posix(), "copy": name,
                      "sha256": hashlib.sha256(data).hexdigest(), "modified": False})
for old, new in (("cnc3_motion_state.v", "cnc3_runtime_state.v"),
                 ("cnc3_command_validate.v", "cnc3_runtime_validate.v"),
                 ("cnc3_motion_spi.v", "cnc3_runtime_sim.v")):
    source = STAGE / old
    data = source.read_bytes()
    with (OUT / new).open("xb") as file:
        file.write(data)
    inventory.append({"source": source.relative_to(ROOT).as_posix(), "copy": new,
                      "before_sha256": hashlib.sha256(data).hexdigest(), "modified": True})
with (OUT / "source-provenance.json").open("x", encoding="utf-8") as file:
    json.dump({"schema_version": 1, "scope": "SIM2 disconnected runtime derivative",
               "production_adopted": False, "inputs": inventory}, file, indent=2)
    file.write("\n")
