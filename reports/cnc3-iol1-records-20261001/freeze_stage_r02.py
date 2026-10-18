from pathlib import Path
import hashlib, json, shutil
P = Path(__file__).resolve().parent
S = P / 'stage-r02'
ROOT = P.parents[1]

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()

prior = P / 'record-config-replay-candidate-r01'
assert sha(prior / 'bundle-manifest.json') == '2bdad96bf51608fbb05dcd51a45990c64f09a23f0ddae41b38498df5c37013df'
originals = {}
for p in (S / 'originals').rglob('*'):
    if not p.is_file(): continue
    name = p.relative_to(S / 'originals').as_posix()
    live = ROOT / 'firmware/motherboard_iol1_readonly' / name
    assert live.is_file() and sha(live) == sha(p), name
    originals[name] = sha(p)
(S / 'original-source-retention.json').write_text(json.dumps({
    'evidence_type': 'byte-identical original shared firmware, no adoption',
    'original_root': str(ROOT / 'firmware/motherboard_iol1_readonly'),
    'files': originals, 'unchanged': True,
    'electrical_source_design_sha256': sha(ROOT / 'hardware/motherboard/design.json')
}, indent=2) + '\n')
proposal = json.loads((S / 'record-and-wire-proposal.json').read_text())
for item in proposal['record_layout']:
    if item[0] == 56:
        item[2] = 'source population12motors/4ABZ/24DI/16DO/2probe/2freq/2PWM/2AO/4AI plus0x0F actual four IOL1 lane mask; no qualification'
(S / 'record-and-wire-proposal.json').write_text(json.dumps(proposal, indent=2) + '\n')
primary = json.loads((S / 'primary-flash-observations.json').read_text())
primary['cold_flash_fault_boundary'] = (
    'Software IWDG starts before factory-page inspection after clocks/safe GPIO setup. '
    'NMI/HardFault currently use the default loop; ECC may therefore reset/repeat rather than recover a record. '
    'No bootloader, hardware-start option, readout protection, automatic repair, flash programming or '
    'NMI recovery is implemented. Actual ECC/brownout/IWDG/NRST behavior remains hardware qualification.')
(S / 'primary-flash-observations.json').write_text(json.dumps(primary, indent=2) + '\n')
readme = (S / 'README.md').read_text()
readme += '''
Successor r02 adds strict host slot/UID argument rejection, a real linker overflow
negative, software IWDG start before factory-page reads and actual C two-generation
selection/torn-successor retention controls. A flash ECC NMI may cause a reset loop;
recovery from physical corrupted flash is not implemented or qualified. The default
DIC diagnostic filter is100us while configuration is unqualified. Source population
ends in the four-lane mask0x0F, not an extra card count.

Run `replay_record_config.py --out <fresh-directory> [--wsl-distro GarciaMechBuilder]`
for all three fresh evidence stages, or `--inventory` for a nonexecuting inventory.
The exact bundle is checked before execution and after it. The source inspection
category is distinct from compiled tests, ARM compilation and SPI simulation.
'''
(S / 'README.md').write_text(readme, newline='\n')
delta = json.loads((S / 'stage-r02-delta.json').read_text())
delta['changes'] += [
    'host explicitly ValueError on invalid slot or UID length/type before indexing',
    'diagnostic comment describes accepted CONFIG/IDENT without authority',
    'actual compiler linker-overflow negative preserves60KiB application/two2KiB factory pages',
    'fresh immutable three-stage replay and original shared source hash retention',
    'clarify existing0x0F source-population lane-mask metadata, no record byte change',
]
(S / 'stage-r02-delta.json').write_text(json.dumps(delta, indent=2) + '\n')
O = P / 'record-config-replay-candidate-r02'
if O.exists(): raise RuntimeError('fresh frozen bundle required')
shutil.copytree(S, O, ignore=shutil.ignore_patterns('__pycache__'))
files = {p.relative_to(O).as_posix(): sha(p) for p in O.rglob('*') if p.is_file()}
(O / 'bundle-manifest.json').write_text(json.dumps({'files': files, 'frozen': True,
    'proposal_not_live_adoption': True}, indent=2) + '\n')
receipt = {'bundle': str(O), 'manifest_sha256': sha(O / 'bundle-manifest.json'),
           'file_count': len(files), 'original_shared_firmware_unchanged': True,
           'prior_r01_manifest_sha256': sha(prior / 'bundle-manifest.json'),
           'runtime_flash_programming_or_factory_trust': False}
(P / 'record-config-r02-freeze.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps(receipt))
