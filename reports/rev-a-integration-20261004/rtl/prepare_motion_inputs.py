"""Pin unchanged current bounded motion candidate for disconnected replay."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent / 'motion-inputs'
OUT.mkdir(exist_ok=False)
STAGE = ROOT / 'reports/cnc3-stateful-implementation-20261001/stage-r02'
names = ('cnc3_alarm_filter.v', 'cnc3_encoder_runtime.v', 'cnc3_motion_spi.v',
         'cnc3_motion_state.v', 'cnc3_spi_transport_stateful.v', 'cnc3_stepgen_runtime.v',
         'cnc3_rate_admission_serial.v')
sources = [STAGE / name for name in names] + [ROOT / 'gateware/v3/rtl/cnc3_command_validate.v']
inventory = []
for source in sources:
    raw = source.read_bytes()
    (OUT / source.name).write_bytes(raw)
    inventory.append({'source': source.relative_to(ROOT).as_posix(), 'copy': source.name,
                      'sha256': hashlib.sha256(raw).hexdigest()})
receipt = {'created_utc': datetime.now(timezone.utc).isoformat(), 'inputs': inventory,
           'scope': 'unchanged bounded report-local stateful 12-motor/4-encoder candidate plus current frozen-protocol validator',
           'complete_IS2_top': False, 'qualification_providers': 'explicit ideal simulation fixtures',
           'DI_DO_probe_integrated': False, 'physical_qualification': False}
(OUT / 'provenance.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(receipt, indent=2))
