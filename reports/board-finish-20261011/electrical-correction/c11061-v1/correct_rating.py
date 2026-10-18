"""Isolated C11061 voltage-rating correction; preserve source and copper.

This does not qualify power timing/current, adopt a board or emit fabrication.
"""
import copy
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPORT = HERE.parent.parent
sys.path.insert(0, str(REPORT))
import compose_additions as C
sys.path.insert(0, str(REPORT / 'parity-repair'))
from host_parity import load_parser, read_board_text, compare
from fresh_export import canonical

BASE = REPORT / 'final-bundle/ROOT106-c05-experimental-v2/native'
BASE_SHA = '95874c4275f10851f03c2f7953fdf4cf4e7e8a0c39bbe399f8aaec642bd7c77d'
OLD_VALUE, NEW_VALUE = '4.7uF 16V X7R', '4.7uF 25V X7R'
OLD_MPN, NEW_MPN = 'C2012X7R1C475K125AB', 'C2012X7R1E475K125AB'
FOOTPRINT_UUID = '73b53c88-a7dc-4167-881c-5246eb125d8a'
SYMBOL_UUID = '01e50a71-28fe-5d2d-9998-baccf3ad16b0'


def sha(raw):
    return hashlib.sha256(raw).hexdigest()


def hashes(folder):
    return {p.relative_to(folder).as_posix(): sha(p.read_bytes())
            for p in sorted(folder.rglob('*')) if p.is_file()}


def replace_properties(raw):
    changed = raw
    for field, old, new in (('Value', OLD_VALUE, NEW_VALUE), ('MPN', OLD_MPN, NEW_MPN)):
        needle = ('(property "' + field + '" "' + old + '"').encode()
        replacement = ('(property "' + field + '" "' + new + '"').encode()
        if changed.count(needle) != 1:
            raise ValueError('Expected exactly one owned property: ' + field)
        changed = changed.replace(needle, replacement)
    return changed


def main():
    native = HERE / 'native'
    if native.exists() or (HERE / 'receipt.json').exists():
        raise ValueError('Fresh isolated outputs required')
    source_hashes = hashes(BASE)
    board_raw = (BASE / 'motherboard.kicad_pcb').read_bytes()
    if sha(board_raw) != BASE_SHA:
        raise ValueError('Wrong c05 carrier')
    old = C.inventory(board_raw)
    matches = [(i, ch) for i, ch in enumerate(old[1])
               if C.pcbtext.chunk_kind(ch) == 'footprint'
               and C.pcbtext.chunk_uuid(ch) == FOOTPRINT_UUID]
    if len(matches) != 1 or b'(property "Reference" "C11061"' not in matches[0][1]:
        raise ValueError('Wrong owned footprint')
    index, old_chunk = matches[0]
    new_chunk = replace_properties(old_chunk)
    chunks = list(old[1]); chunks[index] = new_chunk
    corrected_board = old[0] + b''.join(chunks) + old[2]
    new = C.inventory(corrected_board)
    if old[0] != new[0] or old[2] != new[2] or old[4] != new[4]:
        raise ValueError('Copper or setup changed')
    if any(ch != new[1][i] for i, ch in enumerate(old[1]) if i != index):
        raise ValueError('Unowned native item changed')
    if new_chunk.replace(NEW_VALUE.encode(), OLD_VALUE.encode()).replace(NEW_MPN.encode(), OLD_MPN.encode()) != old_chunk:
        raise ValueError('Owned geometry, pads or UUIDs changed')
    sch = BASE / 'motherboard_power_entry.kicad_sch'
    original_sch = sch.read_bytes()
    lines = original_sch.splitlines(keepends=True)
    owned = [(i, line) for i, line in enumerate(lines)
             if b'(property "Reference" "C11061"' in line and SYMBOL_UUID.encode() in line]
    if len(owned) != 1:
        raise ValueError('Expected exact owned single-line source symbol')
    si, original_line = owned[0]
    lines[si] = replace_properties(original_line)
    corrected_sch = b''.join(lines)
    if corrected_sch.replace(NEW_VALUE.encode(), OLD_VALUE.encode()).replace(NEW_MPN.encode(), OLD_MPN.encode()) != original_sch:
        raise ValueError('Unowned schematic field changed')
    shutil.copytree(BASE, native)
    (native / 'motherboard.kicad_pcb').write_bytes(corrected_board)
    (native / 'motherboard_power_entry.kicad_sch').write_bytes(corrected_sch)
    copied = hashes(native)
    if set(copied) != set(source_hashes):
        raise ValueError('Clone file inventory changed')
    changes = [n for n in copied if copied[n] != source_hashes[n]]
    if set(changes) != {'motherboard.kicad_pcb', 'motherboard_power_entry.kicad_sch'}:
        raise ValueError('Unexpected cloned file changes')
    # Keep the old netlist in the clone labelled by its initial manifest.
    # Export the corrected source to a separate output, then compare all semantics.
    wrapper = Path('Z:/pcb-runs/claude-finish/tools/heavyt.sh')
    parser_source = REPORT / 'parity-repair/c05/tools/netlist_parity.py'
    command = ['C:/Program Files/Git/usr/bin/sh.exe', wrapper.as_posix(), 'kicad',
               'C:/Program Files/KiCad/10.0/bin/kicad-cli.exe', 'sch', 'export', 'netlist',
               '--format', 'kicadsexpr', '--output', (HERE / 'corrected.net').as_posix(),
               (native / 'motherboard.kicad_sch').as_posix()]
    frozen_tools = {str(p.resolve()): sha(p.read_bytes()) for p in
                    (Path(__file__), Path(C.__file__), Path(C.pcbtext.__file__), wrapper, parser_source)}
    env = os.environ.copy()
    env['PATH'] = 'C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;' + env['PATH']
    env.update(OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    started = time.time()
    with (HERE / 'export.log').open('w', encoding='utf-8') as log:
        run = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT, check=False)
    if run.returncode or not (HERE / 'corrected.net').is_file():
        raise ValueError('Corrected native schematic export failed')
    parser = load_parser(parser_source)
    previous = parser['read_netlist'](BASE / 'sch.net')
    fresh = parser['read_netlist'](HERE / 'corrected.net')
    expected = canonical(previous)
    expected['components']['C11061']['value'] = NEW_VALUE
    expected['components']['C11061']['properties']['MPN'] = NEW_MPN
    if canonical(fresh) != expected:
        raise ValueError('Fresh export has unapproved semantic changes')
    table = read_board_text(native / 'motherboard.kicad_pcb', parser, Path(C.pcbtext.__file__))
    parity = compare(fresh, table, parser)
    (HERE / 'host-parity.json').write_text(json.dumps(parity, indent=2) + '\n', encoding='utf-8')
    if parity['verdict'] != 'PASS':
        raise ValueError('Corrected source/native host parity failed')
    if hashes(BASE) != source_hashes or hashes(native) != copied:
        raise ValueError('Inputs changed during export')
    for path, expected_hash in frozen_tools.items():
        if sha(Path(path).read_bytes()) != expected_hash:
            raise ValueError('Tool changed during correction: ' + path)
    result = {'verdict': 'SOURCE_CORRECTION_AND_NATIVE_EXPORT_PASS', 'ref': 'C11061',
              'base_board_sha256': BASE_SHA, 'corrected_board_sha256': sha(corrected_board),
              'footprint_uuid': FOOTPRINT_UUID, 'symbol_uuid': SYMBOL_UUID,
              'old_value': OLD_VALUE, 'new_value': NEW_VALUE, 'old_mpn': OLD_MPN, 'new_mpn': NEW_MPN,
              'retained_footprint': 'Capacitor_SMD:C_0805_2012Metric',
              'nominal_capacitance_uF': 4.7, 'tolerance_percent': 10, 'dielectric': 'X7R',
              'all_copper_pads_poses_rules_and_other_components_exact': True,
              'motor_feed_CT_pins': 'U11010/U11011 intentional unconnected pins unchanged',
              'native_export': {'returncode': run.returncode, 'seconds': round(time.time()-started, 3),
                                'sha256': sha((HERE / 'corrected.net').read_bytes()),
                                'semantic_changes': ['C11061 value and MPN only']},
              'source_inputs': source_hashes, 'corrected_native_inputs': copied, 'tools': frozen_tools,
              'references': [
                  {'url': 'https://www.ti.com/lit/ds/symlink/tps22990.pdf', 'scope': 'Rev C section 9.3.2: CT up to 15 V; capacitor minimum 25 V'},
                  {'url': 'https://product.tdk.com/system/files/dam/doc/product/capacitor/ceramic/mlcc/charasheet/c2012x7r1e475k125ab.pdf',
                   'scope': '4.7 uF, 25 V, X7R, 10%, 0805; nominal body 2.00 x 1.25 x 1.25 mm'}],
              'native_DRC_refill_connectivity_run': False, 'native_API_parity': 'OPEN',
              'adopted': False, 'manufacturing_ready': False,
              'limits': ['Old sch.net in native clone is historical; corrected.net is the corrected native export',
                         'Effective CT versus bias/temperature, historical 0.47–1.32 uF envelope, ramp and inrush must be requalified',
                         '3.6 A / 100 mV delivery, 1000 uF charge envelope and inhibited restart/fault sequence remain open',
                         'No supplier stock, price, board DRC, fabrication or physical qualification']}
    (HERE / 'receipt.json').write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({k: result[k] for k in ('verdict', 'corrected_board_sha256', 'new_value', 'new_mpn')}), flush=True)


if __name__ == '__main__':
    main()
