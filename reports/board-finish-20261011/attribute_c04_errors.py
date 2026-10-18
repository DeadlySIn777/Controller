"""Read-only DRC attribution to exact frozen additive donor UUIDs."""
import hashlib
import json
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent


def sha(data):
    return hashlib.sha256(data).hexdigest()


def main():
    construction_path = HERE / 'recovery-composite/e1/construction.json'
    board_path = HERE / 'recovery-composite/e1/c04-four-net-e1-dfm.kicad_pcb'
    drc_path = HERE / 'measure/c04-main/drc.json'
    construction_bytes, board_bytes, drc_bytes = [p.read_bytes() for p in (construction_path, board_path, drc_path)]
    construction = json.loads(construction_bytes)
    if sha(board_bytes) != construction['candidate_sha256']:
        raise ValueError('c04 board differs from frozen construction')
    owners = {}
    for item in construction['stages']['e1_native_subset_items']:
        owners[item['uuid']] = item['net']
    for item in construction['stages']['fag']['additions']:
        if item['uuid'] in owners:
            raise ValueError('donor UUID ownership collision')
        owners[item['uuid']] = 'FAG'
    if len(owners) != 462:
        raise ValueError('expected 201 E1 plus 261 FAG additions')
    drc = json.loads(drc_bytes)
    counts = Counter()
    records = []
    for error in drc['violations']:
        if error['severity'] != 'error':
            continue
        matched = sorted({owners[item['uuid']] for item in error['items'] if item['uuid'] in owners})
        if len(matched) != 1:
            raise ValueError('error has missing or ambiguous additive ownership')
        counts[matched[0]] += 1
        records.append({'owner': matched[0], 'type': error['type'], 'description': error['description'],
                        'item_uuids': [item['uuid'] for item in error['items']]})
    expected = {'FAG': 14, '/motherboard_status/OBS27_K': 138, '/motherboard_status/OBS34_K': 74,
                '/motherboard_status/OUT5_R_MID': 124, '/motherboard_status/RGB_DRIVER_19': 121}
    if dict(counts) != expected or len(records) != 471:
        raise ValueError('raw native attribution differs from reviewed count')
    for path, original in zip((construction_path, board_path, drc_path), (construction_bytes, board_bytes, drc_bytes)):
        if path.read_bytes() != original:
            raise ValueError('input changed during attribution')
    receipt = {'verdict': 'PASS_EXACT_ERROR_ATTRIBUTION', 'evidence_class': 'host analysis of completed raw native DRC',
               'candidate_sha256': sha(board_bytes), 'construction_sha256': sha(construction_bytes),
               'drc_sha256': sha(drc_bytes), 'errors': len(records), 'counts_by_new_donor_group': dict(counts),
               'all_errors_have_exact_single_donor_owner': True, 'records': records,
               'required_action': 'Remove complete 261-item FAG and all four 201-item E1 groups; remeasure repaired source',
               'native_work_started': False, 'adopted': False, 'manufacturing_ready': False}
    (HERE / 'c04-error-attribution.json').write_text(json.dumps(receipt, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({key: receipt[key] for key in ('verdict', 'errors', 'counts_by_new_donor_group')}))


if __name__ == '__main__':
    main()
