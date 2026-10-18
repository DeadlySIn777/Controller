"""Exact c04 replay followed by complete rollback of conflicting FAG and E1 groups."""
import argparse
import importlib.util
import json
from pathlib import Path
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
C04 = HERE.parent / 'e1'
SPEC = importlib.util.spec_from_file_location('c05_frozen_c04', C04 / 'compose_c04.py')
c04 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c04)
base = c04.base
SOURCE = C04 / 'c04-four-net-e1-dfm.kicad_pcb'
SOURCE_RECEIPT = C04 / 'construction.json'
SOURCE_SHA = 'abed2445e14ce438464a5e2f8d073eb71dc329a66fc5b882a97b6b5be6b12af7'
NET = '/motherboard_motors{slash}FIELD_GND'


def tool_records():
    return {'compose_c05.py': base.file_record(Path(__file__)),
            'compose_c04.py': base.file_record(C04 / 'compose_c04.py')}


def rollback(source, previous):
    """Remove complete pure-add FAG/E1 groups; retain every other byte chunk."""
    if base.sha(source) != SOURCE_SHA:
        raise ValueError('c04 source identity differs')
    original = previous['base_bindings']
    additions = original['stages']['fag']['additions'] + previous['stages']['e1']['additions']
    owned = {item['uuid']: item for item in additions}
    fag_ids = {item['uuid'] for item in original['stages']['fag']['additions']}
    e1_nets = {item['uuid']: item['net'] for item in previous['stages']['e1_native_subset_items']}
    if len(owned) != 462 or len(fag_ids) != 261 or len(e1_nets) != 201 or len(additions) != 462:
        raise ValueError('Complete FAG/E1 ownership groups differ')
    if set(e1_nets.values()) != c04.APPROVED or set(owned) != fag_ids | set(e1_nets):
        raise ValueError('Complete four-net E1 ownership differs')
    inventory = base.inventory(source)
    head, chunks, tail, native = inventory[0], inventory[1], inventory[2], inventory[4]
    r06 = base.inventory(base.verify_file(original['native_sources']['r06']))[4]
    recovery = base.inventory(base.verify_file(original['native_sources']['recovery']))[4]
    removed = []
    kept = []
    for chunk in chunks:
        uid = base.pcbtext.chunk_uuid(chunk)
        if uid not in owned:
            kept.append(chunk)
            continue
        item = owned[uid]
        if (uid in r06 or uid in recovery or base.sha(chunk) != item['sha256']
                or base.pcbtext.chunk_kind(chunk) not in {'segment', 'via'}
                or c04.item_net(chunk) != (NET if uid in fag_ids else e1_nets[uid])):
            raise ValueError('Rollback touches protected or changed copper: ' + uid)
        removed.append(item)
    if {item['uuid'] for item in removed} != set(owned):
        raise ValueError('Incomplete whole FAG/E1 group rollback')
    result = head + b''.join(kept) + tail
    expected = {uid: chunk for uid, chunk in native.items() if uid not in owned}
    after = base.inventory(result)[4]
    if after != expected:
        raise ValueError('Non-FAG/E1 c04 source chunk changed')
    return result, {'source_sha256': base.sha(source), 'candidate_sha256': base.sha(result),
                    'removed_complete_new_groups': removed,
                    'removed_fag_items': len(fag_ids), 'removed_e1_items': len(e1_nets),
                    'removed_e1_whole_nets': sorted(c04.APPROVED),
                    'removed_native_items': len(removed), 'all_other_c04_chunks_retained_exact': True,
                    'protected_r06_and_recovery_items_removed_or_changed': 0,
                    'reason': 'c04 native471errors:14FAG and457across all4E1 nets; each conflicting whole new group withdrawn',
                    'electrical_effect': 'Partial96mA FAG branch and unqualified four E1 routes withdrawn; original power and signal copper unchanged; FIELD_A distribution remains open'}


def validate_construction(receipt_path, candidate_path):
    receipt = json.loads(Path(receipt_path).read_bytes())
    if receipt.get('schema') != 'c05-whole-fag-e1-rollback-construction-v1' or receipt['tools'] != tool_records():
        raise ValueError('c05 constructor identities differ')
    if receipt['source_construction'] != base.file_record(SOURCE_RECEIPT) or receipt['source_candidate'] != base.file_record(SOURCE):
        raise ValueError('Frozen c04 source bindings differ')
    c04.validate_construction(SOURCE_RECEIPT, SOURCE)
    previous = json.loads(SOURCE_RECEIPT.read_bytes())
    if receipt['base_bindings'] != previous:
        raise ValueError('Complete c04 source/project/proof bindings differ')
    context = base.project_context(HERE / 'inputs/project')
    if receipt['project'] != context or {key: value['sha256'] for key, value in context.items()} != {
            key: value['sha256'] for key, value in previous['project'].items()}:
        raise ValueError('c05 native project/rules/library/netlist source differs')
    expected, changes = rollback(SOURCE.read_bytes(), previous)
    if receipt['changes'] != changes or receipt['candidate_sha256'] != base.sha(expected):
        raise ValueError('c05 rollback recipe differs')
    if Path(candidate_path).read_bytes() != expected:
        raise ValueError('c05 candidate bytes differ from exact reconstruction')
    return {'ok': True, 'schema': receipt['schema'], 'candidate_sha256': base.sha(expected),
            'whole_new_fag_items_removed': 261, 'whole_new_e1_items_removed': 201,
            'all_other_c04_chunks_retained_exact': True,
            'protected_copper_removed_or_changed': 0, 'fresh_native_required': True, 'adopted': False}


def build():
    out, receipt_path = HERE / 'c05-fag-e1-rollback-dfm.kicad_pcb', HERE / 'construction.json'
    if out.exists() or receipt_path.exists() or (HERE / 'inputs').exists():
        raise ValueError('c05 destinations must be fresh')
    c04.validate_construction(SOURCE_RECEIPT, SOURCE)
    previous = json.loads(SOURCE_RECEIPT.read_bytes())
    candidate, changes = rollback(SOURCE.read_bytes(), previous)
    shutil.copytree(C04 / 'inputs/project', HERE / 'inputs/project')
    receipt = {'schema': 'c05-whole-fag-e1-rollback-construction-v1', 'evidence_class': 'Source rollback reconstruction only',
               'source_construction': base.file_record(SOURCE_RECEIPT), 'source_candidate': base.file_record(SOURCE),
               'base_bindings': previous, 'tools': tool_records(), 'project': base.project_context(HERE / 'inputs/project'),
               'changes': changes, 'candidate_sha256': base.sha(candidate), 'adopted': False, 'manufacturing_ready': False,
               'requires_fresh_native_measurement': True,
               'limits': ['Provisional20joins only; no fresh native c05 result yet',
                          'All r06/recovery/In3/DFM source retained; complete new FAG and four new E1 groups withdrawn',
                          'No native DRC or electrical/physical qualification from this source receipt']}
    out.write_bytes(candidate)
    receipt_path.write_text(json.dumps(receipt, indent=1) + '\n', encoding='utf-8')
    result = validate_construction(receipt_path, out)
    (HERE / 'construction-check.json').write_text(json.dumps(result, indent=1)+'\n', encoding='utf-8')
    print(json.dumps(result))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--candidate', type=Path)
    args = parser.parse_args()
    if args.build: build()
    elif args.receipt and args.candidate: print(json.dumps(validate_construction(args.receipt, args.candidate)))
    else: parser.error('build, or validate exact receipt and candidate')
