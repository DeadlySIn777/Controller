"""Distinct four-net E1 extension of the frozen c03 reconstruction recipe."""
import argparse
from collections import Counter
import importlib.util
import json
from pathlib import Path
import re
import shutil
import sys

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = BASE.parent
E1 = ROOT / 'router-repair'
BASE_RECEIPT = BASE / 'construction-r1.json'
BASE_CANDIDATE = BASE / 'c03-recovery-in3-fag-dfm.kicad_pcb'
BASE_CHECKER = BASE / 'compose_recovery.py'
spec = importlib.util.spec_from_file_location('c04_frozen_c03', BASE_CHECKER)
base = importlib.util.module_from_spec(spec)
spec.loader.exec_module(base)
R06_SHA = '0e90568af6efa53e8bb15b3de60dbc5d167c1ed84b013b07fa902762582cfe53'
FULL_E1_SHA = '0d491c548285427466cd1c270b54beef13dfc8c2e632edcb1e28a19832e69548'
APPROVED = {'/motherboard_status/OBS27_K', '/motherboard_status/OBS34_K',
            '/motherboard_status/OUT5_R_MID', '/motherboard_status/RGB_DRIVER_19'}
ROLES = {'manifest', 'donor_receipt', 'jobs', 'checkpoint', 'routes', 'full_donor', 'subset_donor', 'subset_receipt'}

def normalized(value):
    return json.loads(json.dumps(value))

def canonical_job(job):
    return json.dumps(job, sort_keys=True, separators=(',', ':'))

def item_net(chunk):
    match = re.search(rb'\(net ("(?:\\.|[^"\\])*")\)', chunk)
    if not match:
        raise ValueError('ordinary native donor item lacks one explicit net name')
    return json.loads(match.group(1))

def verify_accounting(data):
    manifest, receipt, jobs, checkpoint, routes = [json.loads(data[role]) for role in
                                                  ('manifest', 'donor_receipt', 'jobs', 'checkpoint', 'routes')]
    if (not isinstance(jobs, list) or len(jobs) != 2147 or checkpoint.get('done') != len(jobs)
            or checkpoint.get('jobs_sha') != base.sha(data['jobs'])
            or manifest.get('checkpoint_is_complete') is not True
            or manifest.get('source_total_jobs') != len(jobs) or manifest.get('checkpoint_done') != len(jobs)
            or receipt.get('complete_checkpoint') is not True or receipt.get('source_total_jobs') != len(jobs)
            or receipt.get('checkpoint_done') != len(jobs)
            or receipt.get('baseline_sha256') != R06_SHA or manifest.get('base_board_sha256') != R06_SHA
            or receipt.get('donor_sha256') != FULL_E1_SHA or base.sha(data['full_donor']) != FULL_E1_SHA
            or manifest.get('source_hashes', {}).get('jobs') != base.sha(data['jobs'])
            or manifest.get('source_hashes', {}).get('checkpoint') != base.sha(data['checkpoint'])
            or checkpoint.get('tracks') != routes.get('tracks') or checkpoint.get('failures') != routes.get('failures')):
        raise ValueError('E1 final source/checkpoint identities or completeness differ')
    successes = set()
    indexed_aux = set()
    for item in checkpoint['tracks']:
        index = item.get('job_index')
        if index is None:
            continue
        # E1 producer uses one-based job_index; manifest retains that convention.
        if type(index) is not int or not 1 <= index <= len(jobs) or item.get('net') != jobs[index - 1].get('net'):
            raise ValueError('E1 indexed route provenance differs from source job')
        points = item.get('points', [])
        if item.get('kind') == 'power' and len(points) >= 2 and any(point != points[0] for point in points[1:]):
            successes.add(index)
        else:
            indexed_aux.add(index)
    if indexed_aux - successes:
        raise ValueError('E1 auxiliary item does not prove a successful main route')
    expected_failures = Counter(canonical_job(job) for index, job in enumerate(jobs, 1) if index not in successes)
    failures = Counter(canonical_job(item['job']) for item in checkpoint['failures'])
    if failures - expected_failures:
        raise ValueError('E1 failure records cannot be attributed to unsuccessful original jobs')
    remaining_failures = failures.copy()
    unrepresented = []
    for index, job in enumerate(jobs, 1):
        if index in successes:
            continue
        key = canonical_job(job)
        if remaining_failures[key]:
            remaining_failures[key] -= 1
        else:
            unrepresented.append({'index': index, 'job': job})
    groups = {group['net']: group for group in manifest['groups']}
    selected = {}
    for net in sorted(APPROVED):
        group = groups[net]
        indices = [index for index, job in enumerate(jobs, 1) if job.get('net') == net]
        routed, failed = sorted(set(indices) & successes), sorted(set(indices) - successes)
        if set(indices) & {item['index'] for item in unrepresented}:
            raise ValueError('Selected E1 group has an unrepresented original job: ' + net)
        if (group['decision'].get('eligible') is not True or group['decision'].get('disposition') != 'ordinary_indicator'
                or group['source_job_indices'] != indices or group['successful_job_indices'] != routed
                or group['failed_job_indices'] != failed or group['source_jobs'] != [jobs[index - 1] for index in indices]):
            raise ValueError('E1 selected whole-net accounting differs: ' + net)
        per_net = receipt['per_net'][net]
        if per_net['source_jobs'] != indices or per_net['successes'] != routed or per_net['failures'] != failed:
            raise ValueError('E1 native extraction ledger differs: ' + net)
        if per_net.get('router_claimed_cross_ground_pour_records') != 0 or any(
                item.get('crosses_ground_pour') is True for item in checkpoint['tracks'] if item.get('net') == net):
            raise ValueError('E1 selected group contains an unreviewed router ground-pour crossing')
        selected[net] = {'source_jobs': indices, 'successes': routed, 'failures': failed,
                         'native_uuids': per_net['new_native_uuids'],
                         'potential_joins_if_clear_and_connected': per_net['potential_pad_island_joins'],
                         'router_claimed_cross_ground_pour_records': 0}
    if 1679 not in selected['/motherboard_status/OBS34_K']['failures']:
        raise ValueError('Failed OBS34_K source job1679 disappeared')
    return {'checkpoint_processed_original_jobs': len(jobs),
            'explicit_original_outcomes': len(successes) + sum(failures.values()),
            'unrepresented_original_jobs_withheld': unrepresented,
            'selected_original_jobs_fully_accounted': True, 'selected_whole_nets': selected,
            'excluded_whole_nets': ['/motherboard_status/OBS24_K', '/motherboard_status/RGB_DRIVER_3', '/motherboard_status/RGB_NETWORK_B_K'],
            'potential_new_joins': sum(group['potential_joins_if_clear_and_connected'] for group in selected.values()),
            'scope': 'Selected ordinary jobs fully accounted; other unrepresented jobs withheld; obstacle geometry and actual connectivity unqualified'}

def exact_subset(r06, data, accounting):
    _, full = base.pure_add(r06, r06, data['full_donor'])
    b, d = base.inventory(r06), base.inventory(data['full_donor'])
    chunks = [(uid, chunk) for uid, chunk in d[4].items() if uid not in b[4] and item_net(chunk) in APPROVED]
    expected = b[0] + b''.join(b[1]) + b''.join(chunk for _, chunk in chunks) + b[2]
    if expected != data['subset_donor']:
        raise ValueError('Reviewed four-net donor differs from exact original donor subset')
    declared = {uid for group in accounting['selected_whole_nets'].values() for uid in group['native_uuids']}
    if declared != {uid for uid, _ in chunks}:
        raise ValueError('Selected native item UUIDs differ from source-accounting receipt')
    if {item_net(chunk) for _, chunk in chunks} != APPROVED:
        raise ValueError('Four-net donor group inventory differs')
    reviewed = json.loads(data['subset_receipt'])
    if (base.sha(expected) != 'ebdf6b1da6d19ea46d25b31b29429a1ffca2df8d1b7c97fce752ba6377f853dc'
            or reviewed.get('baseline_sha256') != R06_SHA or reviewed.get('donor_sha256') != base.sha(expected)
            or reviewed.get('seven_net_donor_sha256') != FULL_E1_SHA
            or reviewed.get('all_r06_original_items_retained_exact') is not True
            or reviewed.get('added_native_items') != len(chunks) or len(chunks) != 201):
        raise ValueError('Independent four-net subset source receipt differs')
    return expected, [{'uuid': uid, 'net': item_net(chunk), 'sha256': base.sha(chunk)} for uid, chunk in chunks]

def replay(data, base_receipt):
    native = {role: base.verify_file(record) for role, record in base_receipt['native_sources'].items()}
    accounting = verify_accounting(data)
    subset, items = exact_subset(native['r06'], data, accounting)
    stage1, in3 = base.pure_add(native['recovery'], native['in3_baseline'], native['in3_donor'])
    stage2, fag = base.pure_add(stage1, native['r06'], native['fag_donor'])
    if base.sha(stage2) != base_receipt['pre_dfm_sha256']:
        raise ValueError('c03 pre-DFM replay differs from frozen construction')
    stage3, e1 = base.pure_add(stage2, native['r06'], subset)
    candidate, dfm = base.apply_dfm(stage3, native['r06'], native['dfm_donor'])
    return candidate, normalized({'in3': in3, 'fag': fag, 'e1': e1, 'dfm': dfm,
                                 'source_accounting': accounting, 'e1_native_subset_items': items})

def tools():
    paths = [Path(__file__), BASE_CHECKER, ROOT / 'compose_additions.py', ROOT / 'reconcile_dfm.py',
             ROOT / 'dfm_contract_v2.py', base.RUN / 'tools/integrate/pcbtext.py']
    return {path.name: base.file_record(path) for path in paths}

def provenance_bindings(data):
    """Retain every original source identity named by the reviewed extraction receipts."""
    manifest, full, subset = [json.loads(data[role]) for role in ('manifest', 'donor_receipt', 'subset_receipt')]
    records = {}
    named = [(manifest['sources'][role], expected) for role, expected in manifest['source_hashes'].items()]
    named += list(full['original_input_hashes'].items()) + list(subset['input_hashes'].items())
    for path, expected in named:
        record = {'path': str(Path(path).resolve()), 'sha256': expected}
        base.verify_file(record)
        if record['path'] in records and records[record['path']]['sha256'] != expected:
            raise ValueError('Conflicting original E1 source identities')
        records[record['path']] = record
    return records

def validate_construction(receipt_path, candidate_path):
    receipt = json.loads(Path(receipt_path).read_text())
    if receipt.get('schema') != 'c04-four-net-e1-construction-v1' or set(receipt['e1_sources']) != ROLES:
        raise ValueError('c04 construction bindings incomplete')
    if receipt['tools'] != tools():
        raise ValueError('c04 executed source differs from frozen tool identities')
    for role, path in {'receipt': BASE_RECEIPT, 'candidate': BASE_CANDIDATE, 'checker': BASE_CHECKER}.items():
        record = receipt['base_construction'][role]
        if Path(record['path']).resolve() != path.resolve():
            raise ValueError('c03 base path differs from frozen construction')
        base.verify_file(record)
    if base.sha(BASE_CANDIDATE.read_bytes()) != '8f1e03225429422199edc52c3c1ceb476818948c7a5f920e7d71b7cc8d7640c9':
        raise ValueError('c03 candidate identity differs')
    base.validate_construction(BASE_RECEIPT, BASE_CANDIDATE)
    original_base = json.loads(BASE_RECEIPT.read_text())
    if original_base != receipt['base_bindings']:
        raise ValueError('Complete c03 source/project/proof bindings differ')
    for record in receipt['e1_origins'].values():
        base.verify_file(record)
    if set(receipt['e1_origins']) != ROLES:
        raise ValueError('Original E1 source bindings incomplete')
    data = {role: base.verify_file(record) for role, record in receipt['e1_sources'].items()}
    if receipt['original_source_bindings'] != provenance_bindings(data):
        raise ValueError('Original E1 extraction identities differ')
    context = base.project_context(HERE / 'inputs/project')
    if receipt['project'] != context or {key: rec['sha256'] for key, rec in context.items()} != {
            key: rec['sha256'] for key, rec in original_base['project_bindings']['frozen_composite'].items()}:
        raise ValueError('c04 native project/rules/netlist/library identities differ')
    expected, stages = replay(data, original_base)
    if stages != receipt['stages'] or base.sha(expected) != receipt['candidate_sha256']:
        raise ValueError('c04 construction recipe differs from exact replay')
    if Path(candidate_path).read_bytes() != expected:
        raise ValueError('c04 candidate bytes differ from exact reconstruction')
    return {'ok': True, 'schema': receipt['schema'], 'candidate_sha256': base.sha(expected),
            'e1_items': len(stages['e1']['additions']), 'e1_groups': len(APPROVED),
            'e1_potential_new_joins': stages['source_accounting']['potential_new_joins'],
            'all_pre_dfm_target_items_retained_exact': True, 'dfm_guard_version': 2,
            'requires_fresh_native_measurement': True, 'adopted': False}

def build(args):
    output, receipt_path = HERE / 'c04-four-net-e1-dfm.kicad_pcb', HERE / 'construction.json'
    if output.exists() or receipt_path.exists() or (HERE / 'inputs').exists():
        raise ValueError('c04 construction destinations must be fresh')
    base.validate_construction(BASE_RECEIPT, BASE_CANDIDATE)
    previous = json.loads(BASE_RECEIPT.read_text())
    origins = {'manifest': E1 / 'e1-final-r06-manifest.json', 'donor_receipt': E1 / 'e1-final-donor/receipt.json',
               'jobs': E1 / 'e1-final-frozen/jobs.json', 'checkpoint': E1 / 'e1-final-frozen/checkpoint.json',
               'routes': E1 / 'e1-final-frozen/routes.json', 'full_donor': E1 / 'e1-final-donor/r06-e1-ordinary-donor.kicad_pcb',
               'subset_donor': args.subset_donor, 'subset_receipt': args.subset_receipt}
    originals = {role: base.file_record(path) for role, path in origins.items()}
    data = {role: base.verify_file(record) for role, record in originals.items()}
    candidate, stages = replay(data, previous)
    original_bindings = provenance_bindings(data)
    frozen = HERE / 'inputs'
    frozen.mkdir()
    sources = {}
    for role, content in data.items():
        suffix = '.kicad_pcb' if 'donor' in role and 'receipt' not in role else '.json'
        path = frozen / (role + suffix)
        path.write_bytes(content)
        sources[role] = base.file_record(path)
    shutil.copytree(BASE / 'inputs/project', frozen / 'project')
    receipt = {'schema': 'c04-four-net-e1-construction-v1', 'evidence_class': 'Source reconstruction and complete job accounting only',
               'base_construction': {'receipt': base.file_record(BASE_RECEIPT), 'candidate': base.file_record(BASE_CANDIDATE),
                                     'checker': base.file_record(BASE_CHECKER)}, 'base_bindings': previous,
               'e1_origins': originals, 'e1_sources': sources, 'tools': tools(),
               'original_source_bindings': original_bindings,
               'project': base.project_context(frozen / 'project'), 'stages': stages,
               'candidate_sha256': base.sha(candidate), 'requires_fresh_native_measurement': True,
               'adopted': False, 'manufacturing_ready': False,
               'limits': ['No new native proof yet; actual E1 joins may be obstructed by retained copper',
                          'Reject whole new E1 net groups on conflict; never remove pre-DFM target copper',
                          'Fresh whole-board refilled lost0/DRC0, explicit same-hash parity and electrical/return/domain gates remain open']}
    output.write_bytes(candidate)
    receipt_path.write_text(json.dumps(receipt, indent=1) + '\n')
    result = validate_construction(receipt_path, output)
    (HERE / 'construction-check.json').write_text(json.dumps(result, indent=1) + '\n')
    print(json.dumps(result))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--subset-donor', type=Path)
    parser.add_argument('--subset-receipt', type=Path)
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--candidate', type=Path)
    args = parser.parse_args()
    if args.build and args.subset_donor and args.subset_receipt:
        build(args)
    elif args.receipt and args.candidate:
        print(json.dumps(validate_construction(args.receipt, args.candidate)))
    else:
        parser.error('build with subset donor/receipt, or validate with receipt/candidate')

if __name__ == '__main__':
    main()
