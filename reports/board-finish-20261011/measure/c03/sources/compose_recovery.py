"""Compose frozen genuine copper additions onto a measured recovered board.

Read-only validation reconstructs the exact native bytes, including the reviewed
DFM recipe, without pcbnew. Construction alone never authorizes adoption.
"""
import argparse
import hashlib
import json
from pathlib import Path
import re
import shutil
import sys

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent
RECOVERY = Path('Z:/pcb-runs/claude-finish/agent-work/codex-recovery-20261011')
RUN = Path('Z:/pcb-runs/claude-finish')
sys.path.insert(0, str(ROOT))
sys.dont_write_bytecode = True
from compose_additions import inventory, definition, pcbtext
import reconcile_dfm
import dfm_contract_v2

SOURCES = {
    'recovery': (RECOVERY / 'candidate.kicad_pcb', '53838149db4378929875b9862681b790a3a7ed975ee5530c4af975abbeb7df64'),
    'r06': (RECOVERY / 'inputs/baseline-r06.kicad_pcb', '0e90568af6efa53e8bb15b3de60dbc5d167c1ed84b013b07fa902762582cfe53'),
    'in3_baseline': (RUN / 'integrate/revs/r05-stitch-plane-pads-1.kicad_pcb', '594a1091d3a0eade7bff5d4fb83418f10640004afd36119faab92a3886f9e6c2'),
    'in3_donor': (RUN / 'agent-work/test-bridges3/applied.kicad_pcb', 'c28f6c9410cbf0b9bee8f7f1931ad78cffe30a03b401aeb102dc91c35650724e'),
    'fag_donor': (ROOT / 'power-audit/fag-r06/candidate/board.kicad_pcb', 'a10803bbfa3aa5b7e1a859ca4c5a7b6481969c97dc038a66cef21f92e5f61789'),
    'dfm_donor': (ROOT / 'revisions/c02a-r06-dfm.kicad_pcb', '785b1ec5f679aabfab11b319ef50006769fafc099849cd59ca76893ba33743cd'),
}
CORE_PROJECT = ('board.kicad_dru', 'fp-lib-table', 'sch.net')

def sha(data):
    return hashlib.sha256(data).hexdigest()

def file_record(path):
    return {'path': str(path.resolve()), 'sha256': sha(path.read_bytes())}

def verify_file(record):
    path = Path(record['path'])
    data = path.read_bytes()
    if sha(data) != record['sha256']:
        raise ValueError('source hash mismatch: ' + str(path))
    return data

def ordinary_copper(chunk):
    token = pcbtext.chunk_kind(chunk)
    if token == 'segment':
        return True
    if token != 'via':
        return False
    return (re.match(rb'^\s*\(via\s*\r?\n', chunk) is not None
            and re.search(rb'\(layers "F\.Cu" "B\.Cu"\)', chunk) is not None)

def pure_add(target, donor_baseline, donor):
    """Retain every target chunk while requiring the donor's own baseline.

    Target may legitimately omit or replace old baseline copper. Those exact
    differences are recorded; fresh native no-loss/DRC remains compulsory.
    """
    t, b, d = [inventory(data) for data in (target, donor_baseline, donor)]
    if b[0] != d[0] or b[2] != d[2] or b[5] != d[5]:
        raise ValueError('donor modifies non-copper definitions')
    if t[0] != b[0] or t[2] != b[2] or t[5] != b[5]:
        raise ValueError('target and donor baseline physical/setup definitions differ')
    for uid, chunk in b[3].items():
        actual = d[3].get(uid)
        if actual is None or (actual != chunk if uid in b[4] else definition(actual) != definition(chunk)):
            raise ValueError('donor removes or changes its own baseline item: ' + uid)
    additions = [(uid, chunk) for uid, chunk in d[4].items() if uid not in b[4]]
    if set(d[3]) - set(b[3]) != {uid for uid, _ in additions}:
        raise ValueError('donor adds a non-copper item')
    for uid, chunk in additions:
        if not ordinary_copper(chunk):
            raise ValueError('unsupported donor copper; ordinary segments/through vias required')
        if uid in t[3]:
            raise ValueError('donor UUID collides with target: ' + uid)
    result = t[0] + b''.join(t[1]) + b''.join(chunk for _, chunk in additions) + t[2]
    r = inventory(result)
    if r[0] != t[0] or r[2] != t[2] or r[5] != t[5] or r[1][:len(t[1])] != t[1]:
        raise ValueError('pure-add composition altered target chunks')
    if any(r[3].get(uid) != chunk for uid, chunk in t[3].items()):
        raise ValueError('pure-add composition altered target items')
    missing, changed = [], []
    for uid, chunk in b[4].items():
        actual = t[4].get(uid)
        if actual is None:
            missing.append({'uuid': uid, 'baseline_sha256': sha(chunk)})
        elif actual != chunk:
            changed.append({'uuid': uid, 'baseline_sha256': sha(chunk), 'target_sha256': sha(actual)})
    return result, {
        'target_sha256': sha(target), 'donor_baseline_sha256': sha(donor_baseline),
        'donor_sha256': sha(donor), 'result_sha256': sha(result),
        'all_target_chunks_retained_exact': True, 'donor_own_baseline_retained': True,
        'diverged_old_copper': {'missing': missing, 'changed': changed},
        'additions': [{'uuid': uid, 'kind': pcbtext.chunk_kind(chunk), 'sha256': sha(chunk),
                       'layer': pcbtext.chunk_layer(chunk)} for uid, chunk in additions],
        'requires_fresh_native_measurement': True,
    }

def apply_dfm(target, baseline, donor):
    """Replay ROOT's reviewed recipe and hardened independent source contract."""
    reviewed = dfm_contract_v2.validate(baseline, donor)
    t, b, d = [inventory(data) for data in (target, baseline, donor)]
    if t[0] != b[0] or t[2] != b[2] or t[5] != b[5]:
        raise ValueError('DFM target physical definitions differ from reviewed baseline')
    replacements = {item['uuid']: d[3][item['uuid']] for item in reviewed['changed_footprints']}
    if any(t[3].get(uid) != b[3][uid] for uid in replacements):
        raise ValueError('DFM target footprint differs from reviewed baseline')
    added = [item['uuid'] for item in reviewed['additions']]
    if any(uid in t[3] for uid in added):
        raise ValueError('DFM addition UUID collides with target')
    result = t[0] + b''.join(replacements.get(pcbtext.chunk_uuid(chunk), chunk) for chunk in t[1]) + b''.join(d[3][uid] for uid in added) + t[2]
    actual = dfm_contract_v2.validate(target, result)
    return result, {'before_sha256': sha(target), 'candidate_sha256': sha(result), **actual}

def recovery_gate(records, source_data):
    if set(records) != {'guard', 'summary', 'partitions', 'drc'}:
        raise ValueError('native recovery proof records incomplete')
    guard = json.loads(verify_file(records['guard']))
    summary = json.loads(verify_file(records['summary']))
    partitions = json.loads(verify_file(records['partitions']))
    drc = json.loads(verify_file(records['drc']))
    if (guard.get('verdict') != 'PASS' or guard.get('lost') != 0 or guard.get('completed') != 16
            or guard.get('before_sha256') != sha(source_data['r06'])
            or guard.get('after_sha256') != sha(source_data['recovery'])
            or summary.get('board_sha256') != sha(source_data['recovery']) or summary.get('drc_errors') != 0
            or partitions.get('sha256') != sha(source_data['recovery']) or partitions.get('refilled') is not True
            or not isinstance(drc.get('violations'), list)
            or any(item.get('severity') == 'error' for item in drc['violations'])):
        raise ValueError('recovery base lacks its exact native DRC0/lost0/16-gain gate')
    return {'verdict': 'PASS', 'completed': 16, 'lost': 0, 'drc_errors': 0,
            'before_sha256': guard['before_sha256'], 'after_sha256': guard['after_sha256'],
            'scope': 'Recovery base only; composite requires a fresh native gate'}

def reconstruct(source_data):
    stage1, in3 = pure_add(source_data['recovery'], source_data['in3_baseline'], source_data['in3_donor'])
    stage2, fag = pure_add(stage1, source_data['r06'], source_data['fag_donor'])
    final, dfm = apply_dfm(stage2, source_data['r06'], source_data['dfm_donor'])
    if len(in3['additions']) != 32 or len(fag['additions']) != 261:
        raise ValueError('unexpected genuine donor addition count')
    # Hardened DFM exposes tuple world coordinates; JSON receipts use arrays.
    # Canonicalize only receipt metadata. Native bytes are never normalized.
    stages = json.loads(json.dumps({'in3': in3, 'fag': fag, 'dfm': dfm}))
    return stage2, final, stages

def validate_construction(receipt_path, candidate_path):
    """Read-only: rehash sources, replay all recipes, require exact final bytes."""
    receipt = json.loads(Path(receipt_path).read_text(encoding='utf-8'))
    if receipt.get('schema') != 'recovery-composite-construction-v1':
        raise ValueError('unsupported construction receipt')
    expected_tools = {path.name: path.resolve() for path in [Path(__file__), ROOT / 'compose_additions.py',
                      ROOT / 'reconcile_dfm.py', ROOT / 'dfm_contract_v2.py', RUN / 'tools/integrate/pcbtext.py']}
    if set(receipt['tools']) != set(expected_tools):
        raise ValueError('construction tool hashes incomplete')
    if any(Path(receipt['tools'][name]['path']).resolve() != path for name, path in expected_tools.items()):
        raise ValueError('construction tool paths differ from executed checker')
    for record in receipt['tools'].values():
        verify_file(record)
    if set(receipt['origins']) != set(SOURCES):
        raise ValueError('original source role bindings incomplete')
    for role, (path, expected) in SOURCES.items():
        if Path(receipt['origins'][role]['path']).resolve() != path.resolve() or receipt['origins'][role]['sha256'] != expected:
            raise ValueError('original source binding differs from approved chain: ' + role)
    for record in receipt['origins'].values():
        verify_file(record)
    for evidence in receipt['individual_native_evidence'].values():
        for record in evidence['frozen_reports'].values():
            verify_file(record)
    sources = {role: verify_file(record) for role, record in receipt['native_sources'].items()}
    if set(sources) != set(SOURCES):
        raise ValueError('native source roles incomplete')
    for role, (_, expected) in SOURCES.items():
        if sha(sources[role]) != expected:
            raise ValueError('native source identity differs from approved chain: ' + role)
    contexts = receipt['project_bindings']
    if set(contexts) != {'recovery', 'in3', 'fag', 'frozen_composite'}:
        raise ValueError('project role bindings incomplete')
    ids = []
    context_roots = {'recovery': RECOVERY / 'project', 'in3': RUN / 'agent-work/test-bridges3/w/copy',
                     'fag': ROOT / 'power-audit/fag-r06/input', 'frozen_composite': HERE / 'inputs/project'}
    for role, context in contexts.items():
        if not {'project', *CORE_PROJECT} <= set(context):
            raise ValueError('project core identities incomplete: ' + role)
        for record in context.values():
            verify_file(record)
        if context != project_context(context_roots[role]):
            raise ValueError('project context paths or full local-library inventory differs: ' + role)
        ids.append({key: value['sha256'] for key, value in context.items()})
    if any(context != ids[0] for context in ids[1:]):
        raise ValueError('project/rules/netlist/library identities disagree')
    gate = recovery_gate(receipt['recovery_proof'], sources)
    before_dfm, expected, stages = reconstruct(sources)
    if stages != receipt['stages'] or gate != receipt['recovery_base_gate']:
        raise ValueError('construction recipe/receipt differs from reconstruction')
    if sha(before_dfm) != receipt['pre_dfm_sha256'] or sha(expected) != receipt['candidate_sha256']:
        raise ValueError('constructed intermediate/final hash differs')
    if Path(candidate_path).read_bytes() != expected:
        raise ValueError('candidate bytes differ from exact reconstructed source')
    return {'ok': True, 'schema': receipt['schema'], 'candidate_sha256': sha(expected),
            'pre_dfm_sha256': sha(before_dfm), 'in3_additions': 32, 'fag_additions': 261,
            'dfm_guard_version': stages['dfm']['guard_version'],
            'all_pre_dfm_target_items_retained_exact': True,
            'requires_fresh_native_measurement': True, 'adopted': False}

def project_context(root):
    project = root / ('board.kicad_pro.good' if (root / 'board.kicad_pro.good').exists() else 'board.kicad_pro')
    records = {'project': file_record(project)}
    records.update({name: file_record(root / name) for name in CORE_PROJECT})
    records.update({str(path.relative_to(root)): file_record(path) for path in sorted(root.glob('*.pretty/*')) if path.is_file()})
    return records

def snapshot_individual_evidence(frozen):
    """Freeze completed JSON reports only; mutable progress is not a source gate."""
    roles = {'in3_on_r06': ROOT / 'measure/c01', 'fag': ROOT / 'power-audit/fag-r06/measure',
             'dfm': ROOT / 'measure/c02a'}
    result = {}
    for role, root in roles.items():
        records = {}
        for name in ('partitions.json', 'summary.json', 'drc.json'):
            source = root / name
            if not source.exists():
                continue
            data = source.read_bytes()
            try:
                json.loads(data)
            except json.JSONDecodeError:
                continue
            target = frozen / 'individual-evidence' / role / name
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)
            records[name] = {**file_record(target), 'origin_at_snapshot': str(source.resolve())}
        result[role] = {'frozen_reports': records,
                        'full_native_reports_available_at_construction': set(records) == {'partitions.json', 'summary.json', 'drc.json'},
                        'qualification_required_by_constructor': False,
                        'status': 'Individual full native DRC/partition results pending at construction' if set(records) != {'partitions.json', 'summary.json', 'drc.json'} else 'Reports frozen as context; not used to qualify composite',
                        'scope': 'Source additions are checked; final composite needs fresh native DRC and uncapped no-loss proof'}
    return result

def build():
    output, receipt_path = HERE / 'c03-recovery-in3-fag-dfm.kicad_pcb', HERE / 'construction.json'
    if output.exists() or receipt_path.exists() or (HERE / 'inputs').exists():
        raise ValueError('construction destinations must be fresh')
    origins = {role: file_record(path) for role, (path, _) in SOURCES.items()}
    for role, (_, expected) in SOURCES.items():
        if origins[role]['sha256'] != expected:
            raise ValueError('approved original source hash changed: ' + role)
    proof = {key: file_record(RECOVERY / path) for key, path in {
        'guard': 'strict-guard.json', 'summary': 'measure/summary.json',
        'partitions': 'measure/partitions.json', 'drc': 'measure/drc.json'}.items()}
    data = {role: verify_file(record) for role, record in origins.items()}
    gate = recovery_gate(proof, data)
    before_dfm, candidate, stages = reconstruct(data)
    contexts = {'recovery': project_context(RECOVERY / 'project'),
                'in3': project_context(RUN / 'agent-work/test-bridges3/w/copy'),
                'fag': project_context(ROOT / 'power-audit/fag-r06/input')}
    if any({key: rec['sha256'] for key, rec in context.items()} != {key: rec['sha256'] for key, rec in contexts['recovery'].items()}
           for context in contexts.values()):
        raise ValueError('native donor project contexts differ')
    frozen = HERE / 'inputs'
    frozen.mkdir()
    sources = {}
    for role, content in data.items():
        path = frozen / (role + '.kicad_pcb')
        path.write_bytes(content)
        sources[role] = file_record(path)
    project = frozen / 'project'
    shutil.copytree(RECOVERY / 'project', project)
    contexts['frozen_composite'] = project_context(project)
    tools = {path.name: file_record(path) for path in [Path(__file__), ROOT / 'compose_additions.py',
             ROOT / 'reconcile_dfm.py', ROOT / 'dfm_contract_v2.py', RUN / 'tools/integrate/pcbtext.py']}
    receipt = {'schema': 'recovery-composite-construction-v1', 'evidence_class': 'Exact native source construction and hardened DFM contract only',
               'native_sources': sources, 'origins': origins, 'tools': tools, 'project_bindings': contexts,
               'recovery_proof': proof, 'recovery_base_gate': gate, 'stages': stages,
               'individual_native_evidence': snapshot_individual_evidence(frozen),
               'pre_dfm_sha256': sha(before_dfm), 'candidate_sha256': sha(candidate),
               'requires_fresh_native_measurement': True, 'adopted': False, 'manufacturing_ready': False,
               'limits': ['Composite has no native measurement yet; refill DRC and uncapped no-loss comparison versus r06 are mandatory',
                          'Schematic parity, return/domain/current/SI, FPGA/firmware and manufacturing qualification remain separate open gates']}
    output.write_bytes(candidate)
    receipt_path.write_text(json.dumps(receipt, indent=1) + '\n', encoding='utf-8')
    validated = validate_construction(receipt_path, output)
    (HERE / 'construction-check.json').write_text(json.dumps(validated, indent=1) + '\n', encoding='utf-8')
    print(json.dumps(validated))

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--build', action='store_true')
    parser.add_argument('--receipt', type=Path)
    parser.add_argument('--candidate', type=Path)
    args = parser.parse_args()
    if args.build:
        build()
    elif args.receipt and args.candidate:
        print(json.dumps(validate_construction(args.receipt, args.candidate)))
    else:
        parser.error('--build or --receipt and --candidate required')

if __name__ == '__main__':
    main()
