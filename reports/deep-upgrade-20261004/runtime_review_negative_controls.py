"""Reproduce second-review host guard defects using inert adapters only."""
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from test_runtime_configuration import Adapter
from controller_config.runtime import RuntimeConfigurationService

result = {'scope': 'temporary inert host adapters; no LinuxCNC/device connection', 'source_sha256': {}}
for name in ['controller_config/runtime.py', 'tests/test_runtime_configuration.py']:
    raw = (ROOT / name).read_bytes()
    result['source_sha256'][name] = hashlib.sha256(raw).hexdigest()
    target = OUT / 'before-runtime-review' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as handle:
        handle.write(raw)
adapter = Adapter()
adapter.value['capabilities']['max_steps_per_second'] = 10**1000
try:
    RuntimeConfigurationService(adapter).preview([250, 200, 200, 200, 200, 200])
except Exception as error:
    result['oversized_dds_exception_type'] = type(error).__name__
adapter = Adapter()
service = RuntimeConfigurationService(adapter)
plan = service.preview([250, 200, 200, 200, 200, 200])
adapter.unhome_mutation = {'homed': []}
result['empty_homed_apply_released'] = service.apply(plan)['applied'] and not adapter.value['config_locked']
adapter = Adapter()
adapter.value['config_locked'] = True
adapter.unhome_mutation = {'homed': []}
result['empty_homed_recover_released'] = RuntimeConfigurationService(adapter).recover_inhibit()['inhibit_released']
with (OUT / 'runtime-review-negative-controls.json').open('x', encoding='utf-8') as handle:
    json.dump(result, handle, indent=2)
    handle.write('\n')
print(json.dumps(result, indent=2))
