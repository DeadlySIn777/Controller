"""Freeze the exact partial MC revision and independently recheck native data.

Unconnected DRC is an expected failure, never a manufacturing pass. This runner
does not regenerate sources, reroute copper or export fabrication files.
"""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[2]
MC = ROOT / 'hardware/motion_card'
CAD = ROOT / 'hardware/board_review/revisions/20260930-14'
BOARD = CAD / 'motion-card-route-candidate.kicad_pcb'
CLI = Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe')
KIPY = CLI.parent / 'python.exe'


def sha(p):
    return hashlib.sha256(p.read_bytes()).hexdigest()


def write(name, value):
    (HERE / name).write_text(json.dumps(value, indent=2)+'\n', encoding='utf-8')


def run(name, command, expected):
    result = subprocess.run([str(x) for x in command], cwd=ROOT,
                            stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    path = HERE / (name+'.log')
    path.write_bytes(result.stdout)
    receipt = {'command':[str(x) for x in command], 'cwd':str(ROOT),
               'exit_code':result.returncode, 'log':path.name, 'log_sha256':sha(path)}
    if result.returncode not in expected:
        raise RuntimeError('Unexpected native exit '+str(receipt))
    return receipt


def main():
    if (HERE/'review.json').exists():
        raise RuntimeError('A prior immutable receipt exists')
    started = datetime.now(timezone.utc).isoformat()
    mapping = json.loads((MC/'assembly-map.json').read_text())
    paths = {ROOT/p for p in mapping['input_sha256']}
    paths.update(p for folder in (MC,CAD) for p in folder.rglob('*')
                 if p.is_file() and p.suffix != '.png')
    paths.update(ROOT/'tools'/name for name in (
        'hardware_build_motion_card.py','hardware_validate_motion_card.py',
        'hardware_mc_footprint_envelopes.py','motion_card_placement.py',
        'build_board_review.py','motion_card_retain_copper.py',
        'publish_routed_board_review.py','motion_card_routing_inventory.py'))
    paths.update(ROOT/'tests'/name for name in (
        'test_motion_card_integration.py','test_mc_footprint_envelopes.py'))
    before = {p.relative_to(ROOT).as_posix():sha(p) for p in sorted(paths)}
    for relative in before:
        destination = HERE/'source'/relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(ROOT/relative, destination)
    write('input-sha256.json', before)
    commands = []
    commands.append(run('native-sch-erc', [CLI,'sch','erc','--format','json',
        '--severity-all','--exit-code-violations','-o',HERE/'native-erc.json',
        MC/'motion_card.kicad_sch'], {0}))
    commands.append(run('native-sch-export', [CLI,'sch','export','netlist',
        '--format','kicadxml','-o',HERE/'fresh-netlist.xml',MC/'motion_card.kicad_sch'], {0}))
    sys.path.insert(0,str(ROOT/'tools'))
    from hardware_validate_motion_card import validate
    errors, contract = validate(ET.parse(HERE/'fresh-netlist.xml'),
        json.loads((MC/'design.json').read_text()), mapping)
    if errors:
        raise RuntimeError('Independent native contract mismatch '+str(errors))
    erc = json.loads((HERE/'native-erc.json').read_text())
    commands.append(run('native-pcb-drc', [CLI,'pcb','drc','--format','json',
        '--severity-all','--exit-code-violations','-o',HERE/'native-drc.json',BOARD], {5}))
    drc = json.loads((HERE/'native-drc.json').read_text())
    erc_violations = [v for sheet in erc.get('sheets',[]) for v in sheet.get('violations',[])]
    if erc_violations or drc['violations'] or erc.get('ignored_checks') or drc.get('ignored_checks'):
        raise RuntimeError('Unclosed or ignored native rule findings')
    commands.append(run('uncapped-routing-inventory', [KIPY,
        ROOT/'tools/motion_card_routing_inventory.py','--board',BOARD,
        '--netlist',HERE/'fresh-netlist.xml','--out',HERE/'fresh-native-routing-inventory'], {0}))
    routing = json.loads((HERE/'fresh-native-routing-inventory/review.json').read_text())
    after = {relative:sha(ROOT/relative) for relative in before}
    if before != after:
        raise RuntimeError('Source changed during native validation')
    receipt = {'started_utc':started, 'finished_utc':datetime.now(timezone.utc).isoformat(),
        'candidate_revision':'motion-card-r0.4-proposed-IS2','published_board_revision':'20260930-14',
        'scope':'Partial motion card, not a complete controller',
        'input_count':len(before),'input_hashes_unchanged':True,
        'native_kicad_cli_sha256':sha(CLI),'native_pcb_sha256':sha(BOARD),
        'erc_violations':len(erc_violations),'erc_ignored_checks':erc.get('ignored_checks',[]),
        'drc_regular_violations':len(drc['violations']),
        'drc_ignored_checks':drc.get('ignored_checks',[]),
        'drc_capped_unconnected_items':len(drc['unconnected_items']),
        'drc_pass':False,'drc_failure_reason':'Required physical connections remain unrouted',
        'source_contract':contract,
        'uncapped_unconnected_joins':routing['independent_physical_cluster_missing_joins'],
        'physical_connectivity_inventory_sha256':sha(HERE/'fresh-native-routing-inventory/review.json'),
        'commands':commands,'target_compilation_run':False,'hdl_simulation_run':False,
        'vendor_fit_run':False,'physical_measurement':False,
        'fabrication_files_generated':False,'manufacturing_ready':False}
    write('review.json',receipt)
    print(json.dumps({k:v for k,v in receipt.items() if k not in ('source_contract','commands')}))


if __name__ == '__main__':
    main()
