"""Preserve exact authorized sources and reproduce two host policy defects."""
import hashlib
import json
import os
from pathlib import Path
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
sys.path[:0] = [str(ROOT), str(ROOT / 'tests')]
from test_runtime_configuration import Adapter
from controller_config.runtime import RuntimeConfigurationService
from controller_config import ConfigurationService, RuntimeState
from controller_config.recovery import Cartridge

sources = ['controller_config/runtime.py', 'controller_config/persistent_runtime.py', 'controller_config/recovery.py',
           'tests/test_runtime_configuration.py', 'tests/test_persistent_runtime.py', 'tests/test_configuration_recovery.py',
           'tests/test_motherboard_iol1_readonly.py', 'firmware/motherboard_iol1_readonly/iol1.c',
           'firmware/motherboard_iol1_readonly/iol1.h', 'firmware/motherboard_iol1_readonly/target.c',
           'firmware/motherboard_iol1_readonly/test_protocol.c']
hashes = {}
for name in sources:
    raw = (ROOT / name).read_bytes()
    target = OUT / 'before' / name
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as handle:
        handle.write(raw)
    hashes[name] = hashlib.sha256(raw).hexdigest()
results = {}
for label, velocity in [('nan', float('nan')), ('negative', -10), ('boolean', True)]:
    adapter = Adapter()
    adapter.value['capabilities']['joint_max_velocity'][0] = velocity
    result = RuntimeConfigurationService(adapter).preview([250, 200, 200, 200, 200, 200])
    results['unsafe_velocity_' + label + '_preview_accepted'] = bool(result)
with tempfile.TemporaryDirectory() as directory:
    folder = Path(directory)
    service = ConfigurationService(folder / 'config.json', lambda: RuntimeState())
    service.initialize('test-only')
    config = service.select_profile('sim-mill-3axis')
    cartridge = Cartridge(folder / 'cartridge')
    machine = '29ec6d59-6e25-4986-95a2-92cc10cfdc1d'
    cartridge.save(machine, config, 0)
    cartridge.save(machine, config, 1)
    victim = folder / 'unrelated-source.json'
    os.link(cartridge.slot_path(0), victim)
    before = victim.read_bytes()
    cartridge.save(machine, config, 2, interrupt_after_bytes=10)
    results['hardlinked_user_file_truncated'] = victim.read_bytes() == before[:10]
receipt = {'source_sha256': hashes, 'negative_controls': results,
           'scope': 'Temporary disconnected host doubles only; no runtime/device opened.'}
(OUT / 'firmware-runtime-before.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
print(json.dumps(results))
