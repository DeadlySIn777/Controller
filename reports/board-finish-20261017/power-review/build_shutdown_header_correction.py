"""Create an isolated BOM-only shutdown-header correction; never rewrite a PCB.

All input files remain immutable. Exact native footprint chunks form a guarded
three-object packet for later source/board reconciliation by the parent task.
"""
from pathlib import Path
import csv
import hashlib
import importlib.util
import json
import re
import shutil
from datetime import datetime, timezone

ROOT = Path(__file__).resolve().parents[3]
OUT = Path(__file__).resolve().parent
OLD = ROOT / 'reports/board-finish-20261011'
CONT = OLD / 'continuation-r2'
SOURCE = CONT / 'field-power/combined-power-source-r3-hierarchy/source'
BOARD = CONT / 'combined-R753-one-full-native-fill-cached-DRC-r299/copy/board.kicad_pcb'
HELPER = OLD / 'parity-repair/root106/tools/pcbtext.py'
FOOTPRINT = ROOT / 'reports/routing-resume-20261011/bridge-native/copy/Connector_Phoenix_MC.pretty/PhoenixContact_MC_1,5_2-G-3.81_1x02_P3.81mm_Horizontal.kicad_mod'
REFS = ('J11002', 'J11004', 'J11006')
FPID = 'Connector_Phoenix_MC:PhoenixContact_MC_1,5_2-G-3.81_1x02_P3.81mm_Horizontal'

def digest(data):
    return hashlib.sha256(data).hexdigest()

def sha(path):
    return digest(path.read_bytes())

def replace_properties(chunk, ref):
    assert len(re.findall(rb'\(property "Reference" "' + ref.encode() + rb'"', chunk)) == 1
    assert FPID.encode() in chunk
    new = chunk
    for name in ('Value', 'MPN'):
        old = f'(property "{name}" "1803578"'.encode()
        newprop = f'(property "{name}" "1803277"'.encode()
        assert new.count(old) == 1, (ref, name)
        new = new.replace(old, newprop)
    assert new.replace(b'"1803277"', b'"1803578"') == chunk
    return new

def main():
    work = OUT / 'shutdown-header-correction-r1'
    assert not work.exists(), 'Refuse stale/overwritten evidence directory'
    work.mkdir()
    inventory = {str(p): sha(p) for p in SOURCE.iterdir() if p.is_file()}
    inventory.update({str(p): sha(p) for p in (BOARD, HELPER, FOOTPRINT, Path(__file__))})
    assert inventory[str(BOARD)] == '7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2'
    spec = importlib.util.spec_from_file_location('frozen_pcbtext', HELPER)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    source_out = work / 'source'
    source_out.mkdir()
    # Retain complete 27-sheet hierarchy and project tables; do not carry a stale netlist.
    for p in SOURCE.iterdir():
        if p.is_file():
            shutil.copyfile(p, source_out / p.name)
    source_path = source_out / 'motherboard_power_entry.kicad_sch'
    original_source = source_path.read_bytes()
    lines = original_source.splitlines(keepends=True)
    source_changes = []
    for ref in REFS:
        indices = [i for i, line in enumerate(lines) if f'(property "Reference" "{ref}"'.encode() in line]
        assert len(indices) == 1
        i = indices[0]
        before = lines[i]
        lines[i] = replace_properties(before, ref)
        source_changes.append({'ref': ref, 'old_symbol_sha256': digest(before), 'new_symbol_sha256': digest(lines[i])})
    corrected_source = b''.join(lines)
    assert corrected_source.replace(b'"1803277"', b'"1803578"') == original_source
    source_path.write_bytes(corrected_source)
    for name in inventory:
        if str(SOURCE) in name and Path(name).name != source_path.name:
            assert sha(source_out / Path(name).name) == inventory[name]

    head, chunks, tail = helper.split(BOARD.read_bytes())
    packet = work / 'native-bom-packet'
    packet.mkdir()
    operations = []
    for ref in REFS:
        selected = [c for c in chunks if helper.chunk_kind(c) == 'footprint' and f'(property "Reference" "{ref}"'.encode() in c]
        assert len(selected) == 1
        before = selected[0]
        after = replace_properties(before, ref)
        (packet / f'{ref}.before.footprint-chunk').write_bytes(before)
        (packet / f'{ref}.BOM-only.footprint-chunk').write_bytes(after)
        operations.append({'ref': ref, 'uuid': helper.chunk_uuid(before), 'expected_before_chunk_sha256': digest(before), 'replacement_chunk_sha256': digest(after), 'changed_properties': ['Value', 'MPN'], 'all_other_bytes_preserved': True})

    fp = FOOTPRINT.read_bytes()
    assert b'order number: 1803277' in fp
    assert fp.count(b'(drill 1.2)') == 2
    assert b'(at 3.81 0)' in fp
    shutil.copyfile(FOOTPRINT, work / FOOTPRINT.name)
    vendor = {
        'checked_utc': datetime.now(timezone.utc).isoformat(),
        'local_resource_checked_before_web': str(FOOTPRINT),
        'header': {'mpn': '1803277', 'name': 'MC 1,5/ 2-G-3,81', 'role': '2-position PCB header', 'pitch_mm': 3.81, 'vendor_recommended_hole_mm': 1.2, 'header_nominal_current_A': 8, 'nominal_rating_is_not_application_qualification': True, 'url': 'https://www.phoenixcontact.com/en-us/products/pcb-header-mc-15-2-g-381-1803277'},
        'mate': {'mpn': '1803578', 'name': 'MC 1,5/ 2-ST-3,81', 'role': 'removable screw socket connector', 'listed_by_header_vendor_as_mating_part': True, 'url': 'https://www.phoenixcontact.com/en-us/products/pcb-plug-mc-15-2-st-381-1803578'},
        'remaining': ['orientation and pin-1/harness drawing visual review', 'keying/coding and wire/strain-relief qualification', 'mechanical insertion/service clearance and assembly verification'],
    }
    (work / 'primary-evidence.json').write_text(json.dumps(vendor, indent=2) + '\n')
    with (work / 'connector-bom-delta.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['reference', 'assembly_role', 'old_mpn', 'corrected_mpn', 'qty_each', 'scope'])
        for ref in REFS:
            writer.writerow([ref, 'PCB header fitted on motherboard', '1803578', '1803277', 1, 'Value/MPN only; pins/footprint/pose/copper unchanged'])
        writer.writerow(['J11002/J11004/J11006 mates', 'retained pluggable harness connector', '', '1803578', 3, 'Separate harness BOM line; not fitted PCB component'])
    for name, expected in inventory.items():
        assert sha(Path(name)) == expected, ('input changed', name)
    receipt = {
        'verdict': 'PASS_ISOLATED_BOM_ONLY_CONSTRUCTION_NATIVE_EXPORT_PENDING',
        'utc': datetime.now(timezone.utc).isoformat(),
        'input_sha256': inventory,
        'source_changes': source_changes,
        'source_sheet_count': len(list(source_out.glob('*.kicad_sch'))),
        'native_packet_operations': operations,
        'all_other_source_files_unchanged': True,
        'source_reversal_exact': True,
        'native_chunk_reversal_exact': True,
        'source_or_live_board_written': False,
        'source_derivative_written': True,
        'full_PCB_emitted': False,
        'electrical_or_current_limits_changed': False,
        'shutdown_contacts_remain_control_only': True,
        'ERC': False, 'DRC': False, 'physical_measurement': False,
        'adopted': False, 'manufacturing_ready': False,
    }
    (work / 'construction-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({'verdict': receipt['verdict'], 'refs': REFS, 'sheets': receipt['source_sheet_count'], 'out': str(work)}))

if __name__ == '__main__':
    main()
