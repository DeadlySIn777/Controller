"""Pinned source-only target inventory for additive recovery on frozen c05."""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys
from collections import Counter

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
EXT = Path('Z:/pcb-runs/claude-finish')
C05 = HERE.parent / 'c05'
SPEC = importlib.util.spec_from_file_location('c06_c05', C05 / 'compose_c05.py')
c05 = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(c05)
base = c05.base
SOURCES = {
 'c05_board': C05 / 'c05-fag-e1-rollback-dfm.kicad_pcb',
 'c05_construction': C05 / 'construction.json',
 'r06_board': EXT / 'integrate/revs/r06-stitch-plane-pads-2.kicad_pcb',
 'r07_board': EXT / 'integrate/revs/r07-ripup-signals-1.kicad_pcb',
 'r07_partitions': EXT / 'integrate/measure/r07-ripup-signals-1/partitions.json',
 'c05_partitions': ROOT / 'measure/c05-shared/partitions.json',
 'transition': ROOT / 'measure/c05-shared/live-transition-diagnostic.json',
 'r06_geometry': EXT / 'agent-work/field-pdn/testA3/w/geom.json',
 'router_reserved_geometry_a': EXT / 'integrate/work/r07-ripup-signals-1/rd/ripup-work/res-geom-r1-a/geom.json',
 'router_reserved_geometry_c': EXT / 'integrate/work/r07-ripup-signals-1/rd/ripup-work/res-geom-r1-c/geom.json',
 'router_reserved_rules_a': EXT / 'integrate/work/r07-ripup-signals-1/rd/ripup-work/res-geom-r1-a/board.kicad_dru',
 'router_reserved_rules_c': EXT / 'integrate/work/r07-ripup-signals-1/rd/ripup-work/res-geom-r1-c/board.kicad_dru',
 'project': C05 / 'inputs/project/board.kicad_pro.good',
 'rules': C05 / 'inputs/project/board.kicad_dru',
 'barriers': Path('Z:/pcb-runs/domains/barriers.json'),
}


def sha(data): return hashlib.sha256(data).hexdigest()


def main():
    data = {role: path.read_bytes() for role, path in SOURCES.items()}
    if sha(data['c05_board']) != '95874c4275f10851f03c2f7953fdf4cf4e7e8a0c39bbe399f8aaec642bd7c77d':
        raise ValueError('c05 source differs')
    old, new, diagnostic, geometry = [json.loads(data[role]) for role in
                                    ['r07_partitions', 'c05_partitions', 'transition', 'r06_geometry']]
    if old['sha256'] != sha(data['r07_board']) or new['sha256'] != sha(data['c05_board']):
        raise ValueError('saved native partition source mismatch')
    if geometry['sha256'] != sha(data['r06_board']) or not geometry['refilled'] or geometry['api_errors']:
        raise ValueError('conservative r06 geometry source differs')
    pad_counts = Counter()
    pads = {}
    for pad in geometry['pads']:
        key = pad['ref'] + '.' + pad['num']
        number = pad_counts[key]
        pad_counts[key] += 1
        pads[key + '#' + str(number)] = pad
    targets = []
    for net, record in diagnostic['per_net'].items():
        if not record['lost']: continue
        splits = []
        for before in old['nets'][net]:
            touched = [group for group in new['nets'][net] if set(group) & set(before)]
            if len(touched) > 1:
                splits.append({'r07_connected_pad_ids': before, 'c05_split_groups': touched})
        targets.append({'net': net, 'domain': geometry['nets'].get(net), 'lost': record['lost'],
                        'lost_relationships': splits, 'r07_groups': old['nets'][net],
                        'c05_groups': new['nets'][net],
                        'pads': [{key: pads[pid][key] for key in ['ref','num','uuid','net','x','y','smd']}
                                 | {'pad_id': pid, 'layers': list(pads[pid]['layers'])}
                                 for group in new['nets'][net] for pid in group]})
    if len(targets) != 13 or sum(item['lost'] for item in targets) != 13 or any(len(item['lost_relationships']) != 1 for item in targets):
        raise ValueError('expected thirteen single native relationships differs')
    report = {'schema': 'c06-source-target-inventory-v1', 'evidence_class': 'Source/native saved-receipt target selection only',
              'source_files': {role: {'path':str(SOURCES[role]), 'sha256':sha(raw), 'bytes':len(raw)} for role,raw in data.items()},
              'targets': targets, 'policy': {'existing_c05_items': 'retain every item byte exact',
                  'native_jobs': 0, 'gpu_jobs': 0, 'new_routes': 'host strict geometry only; at most one dive/return',
                  'ordinary_signal_width_mm':0.2, 'new_via_size_drill_mm':[0.6,0.3],
                  'same_domain_clearance_mm':0.15, 'foreign_domain_clearance_mm':0.6,
                  'hole_clearance_mm':0.25, 'export_geometry_margin_mm':0.025},
              'adopted':False, 'fresh_native_required':True}
    (HERE/'target-inventory.json').write_text(json.dumps(report,indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'source_sha':sha(data['c05_board']), 'targets':targets},indent=1))


if __name__ == '__main__': main()
