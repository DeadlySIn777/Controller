"""Pure byte reconstruction of four additive r07 paths; no native API."""
import hashlib, json, shutil, sys, uuid
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(ROOT)); sys.path.insert(0, str(HERE.parent/'two-zero-via'))
import compose_additions as T
import compose_two as TWO
R07, R07_SHA = TWO.R07, TWO.R07_SHA
NAMESPACE = uuid.UUID('9e2c8c82-fd83-4152-8a7c-b0c3d5352faa')
NETS = {'/motherboard_io_control/DIC_NRST_N', '/motherboard_acc_control/AI_POWER_GOOD_HOST',
        '/BANK_B_BUFFER_ENABLE_QUALIFIED', '/motherboard_io_control/DI_SAFETY_SUPPLY_FAULT'}

def sha(raw): return hashlib.sha256(raw).hexdigest()
def norm(net): return net.replace('{slash}', '/')
def number(value): return format(value, '.6f').rstrip('0').rstrip('.')


def approved_paths(receipt):
    two = json.loads(Path(receipt['component_audits'][0]).read_bytes())
    ordinary = json.loads(Path(receipt['component_audits'][1]).read_bytes())
    safety = json.loads(Path(receipt['component_audits'][2]).read_bytes())
    if two['verdict'] != 'HOST_PASS_NATIVE_OPEN' or ordinary['verdict'] != 'HOST_PASS_NATIVE_OPEN' or safety['verdict'] != 'HOST_GEOMETRY_PASS_NATIVE_ELECTRICAL_OPEN':
        raise ValueError('Component audit not passed')
    paths = {norm(row['net']): {'segments': row['segments'], 'new_signal_vias': []} for row in two['rows']}
    row = ordinary['rows'][0]; paths[norm(row['net'])] = {'segments': [row['route']], 'new_signal_vias': []}
    paths[norm(safety['net'])] = {key: safety['route'][key] for key in ('segments', 'new_signal_vias')}
    if set(paths) != NETS: raise ValueError('Wrong approved net set')
    return paths


def reconstruct(receipt):
    if receipt['schema'] != 'r07-four-pure-add-construction-v1': raise ValueError('Wrong recipe')
    for path, expected in receipt['source_files_sha256'].items():
        if sha(Path(path).read_bytes()) != expected: raise ValueError('Construction input changed: '+path)
    source = Path(receipt['source_board']).read_bytes()
    if sha(source) != R07_SHA or receipt['source_board_sha256'] != R07_SHA: raise ValueError('Wrong r07 source')
    if sha(Path(receipt['live_board']).read_bytes()) != R07_SHA: raise ValueError('Actual live source changed')
    TWO.validate_construction(receipt['two_construction'], receipt['two_candidate'])
    intermediate = Path(receipt['two_candidate']).read_bytes()
    original, kept = T.inventory(source), T.inventory(intermediate)
    audit = json.loads(Path(receipt['audit_path']).read_bytes())
    if audit['verdict'] != 'HOST_PASS_NATIVE_ELECTRICAL_OPEN' or audit['source_board_sha256'] != R07_SHA or audit['failures']:
        raise ValueError('Combined audit not passed')
    if len(audit['rows']) != 4 or {norm(row['net']) for row in audit['rows']} != NETS: raise ValueError('Wrong combined net set')
    approved = approved_paths(receipt)
    for row in audit['rows']:
        if row['verdict'] != 'HOST_PASS_NATIVE_ELECTRICAL_OPEN' or row['failures']: raise ValueError('Unqualified path')
        if {key: row[key] for key in ('segments', 'new_signal_vias')} != approved[norm(row['net'])]: raise ValueError('Path differs from frozen component audit')
        if any(not all(check['source_connected_reference_both_planes'].values()) for check in row['reference_checks']): raise ValueError('Uncovered source reference')
        if any(not all(check['source_connected_after_all_new_antipads'].values()) for check in row['return_checks']): raise ValueError('Unanchored existing return')
    chunks, added = [], []
    two_receipt = json.loads(Path(receipt['two_construction']).read_bytes())
    added.extend(two_receipt['added_items'])
    for row in audit['rows']:
        if norm(row['net']) in TWO.NETS: continue
        for segment_index, segment in enumerate(row['segments']):
            if segment['layer'] not in ('F.Cu', 'In3.Cu') or segment['width_mm'] != .2: raise ValueError('Unexpected signal geometry')
            for index, (a, b) in enumerate(zip(segment['points_mm'], segment['points_mm'][1:])):
                if a == b: raise ValueError('Degenerate segment')
                key = json.dumps([R07_SHA, row['net'], 'segment', segment_index, index, a, b, .2, segment['layer']], separators=(',', ':'))
                uid = str(uuid.uuid5(NAMESPACE, key))
                if uid in kept[3] or any(item['uuid'] == uid for item in added): raise ValueError('UUID collision')
                chunk = ('\t(segment\n\t\t(start '+number(a[0])+' '+number(a[1])+')\n\t\t(end '+number(b[0])+' '+number(b[1])+')\n'
                         '\t\t(width 0.2)\n\t\t(layer '+json.dumps(segment['layer'])+')\n\t\t(net '+json.dumps(row['net'])+')\n\t\t(uuid "'+uid+'")\n\t)\n').encode()
                chunks.append(chunk); added.append({'uuid': uid, 'net': row['net'], 'kind': 'segment', 'layer': segment['layer'],
                                                    'width_mm': .2, 'start_mm': a, 'end_mm': b, 'sha256': sha(chunk)})
        for index, via in enumerate(row['new_signal_vias']):
            if norm(row['net']) != '/motherboard_io_control/DI_SAFETY_SUPPLY_FAULT' or via['size_mm'] != .5 or via['drill_mm'] != .2: raise ValueError('Unexpected via')
            x, y = via['point_mm']; key = json.dumps([R07_SHA, row['net'], 'via', index, x, y, .5, .2], separators=(',', ':'))
            uid = str(uuid.uuid5(NAMESPACE, key))
            if uid in kept[3] or any(item['uuid'] == uid for item in added): raise ValueError('UUID collision')
            chunk = ('\t(via\n\t\t(at '+number(x)+' '+number(y)+')\n\t\t(size 0.5)\n\t\t(drill 0.2)\n\t\t(layers "F.Cu" "B.Cu")\n'
                     '\t\t(net '+json.dumps(row['net'])+')\n\t\t(uuid "'+uid+'")\n\t)\n').encode()
            chunks.append(chunk); added.append({'uuid': uid, 'net': row['net'], 'kind': 'via', 'position_mm': [x, y],
                                               'size_mm': .5, 'drill_mm': .2, 'sha256': sha(chunk)})
    result = kept[0]+b''.join(kept[1])+b''.join(chunks)+kept[2]; after = T.inventory(result)
    if after[0] != original[0] or after[2] != original[2] or after[5] != original[5] or any(after[3].get(uid) != chunk for uid, chunk in original[3].items()): raise ValueError('Existing r07 item changed')
    if any(after[3].get(uid) != chunk for uid, chunk in kept[3].items()): raise ValueError('Frozen two-path item changed')
    if len(after[4])-len(original[4]) != len(added) or len(added) != 18: raise ValueError('Copper delta mismatch')
    return result, added


def validate_construction(receipt_path, candidate_path):
    receipt = json.loads(Path(receipt_path).read_bytes()); candidate, added = reconstruct(receipt)
    if Path(candidate_path).read_bytes() != candidate or sha(candidate) != receipt['candidate_sha256'] or added != receipt['added_items']: raise ValueError('Exact source/ownership reconstruction failed')
    return {'schema': receipt['schema'], 'verdict': 'SOURCE_HOST_PASS_NATIVE_ELECTRICAL_OPEN', 'candidate_sha256': sha(candidate),
            'retained_live_r07_items_byte_exact': True, 'retained_frozen_two_path_items_byte_exact': True,
            'new_segments': 16, 'new_vias': 2, 'new_nets': 4, 'netclasses_rules_components_planes_changed': False,
            'native_partition_guards': ['r07/live', 'r06'], 'remaining_original_r06_losses_are_fatal': True,
            'native_return_zone_island_neck_electrical_proof': 'OPEN', 'adopted': False, 'manufacturing_ready': False}


def main():
    audit_path = HERE/'audit.json'; audit = json.loads(audit_path.read_bytes())
    if audit['verdict'] != 'HOST_PASS_NATIVE_ELECTRICAL_OPEN': raise ValueError('Combined audit not passed')
    project = HERE/'inputs/project'; project.mkdir(parents=True, exist_ok=False)
    for source in (TWO.HERE/'inputs/project').iterdir():
        if source.is_dir(): shutil.copytree(source, project/source.name)
        else: (project/source.name).write_bytes(source.read_bytes())
    two_construction, two_candidate = TWO.HERE/'construction.json', TWO.HERE/'r07-two-zero-via.kicad_pcb'
    hashes = dict(audit['source_files_sha256']); two_receipt = json.loads(two_construction.read_bytes())
    for path, expected in two_receipt['source_files_sha256'].items():
        if path in hashes and hashes[path] != expected: raise ValueError('Source binding conflict')
        hashes[path] = expected
    live = Path('Z:/pcb-runs/claude-finish/integrate/board.kicad_pcb')
    for path in [Path(__file__), audit_path, Path(T.__file__), Path(T.pcbtext.__file__), Path(TWO.__file__),
                 two_construction, two_candidate, live] + list(project.rglob('*')):
        if path.is_file(): hashes[str(path.resolve())] = sha(path.read_bytes())
    receipt = {'schema': 'r07-four-pure-add-construction-v1', 'source_board': str(R07), 'source_board_sha256': R07_SHA,
               'live_board': str(live), 'two_construction': str(two_construction), 'two_candidate': str(two_candidate),
               'component_audits': [str(HERE.parent/'two-zero-via/audit.json'), str(HERE.parent/'ordinary-batch/audit.json'), str(HERE.parent/'alternate-r07-small/safety-path-audit-r1.json')],
               'audit_path': str(audit_path), 'source_files_sha256': hashes,
               'evidence_class': 'Exact pure addition and host geometry only; full native/electrical gates open',
               'adopted': False, 'manufacturing_ready': False}
    candidate, added = reconstruct(receipt); receipt.update(candidate_sha256=sha(candidate), added_items=added)
    output, construction = HERE/'r07-four-path.kicad_pcb', HERE/'construction.json'
    if output.exists() or construction.exists(): raise ValueError('Fresh outputs only')
    output.write_bytes(candidate); construction.write_text(json.dumps(receipt, indent=1)+'\n', encoding='utf-8')
    checked = validate_construction(construction, output)
    (HERE/'construction-check.json').write_text(json.dumps(checked, indent=1)+'\n', encoding='utf-8')
    print(json.dumps({'candidate': str(output), 'construction': str(construction), 'check': checked}, indent=1))


if __name__ == '__main__': main()
