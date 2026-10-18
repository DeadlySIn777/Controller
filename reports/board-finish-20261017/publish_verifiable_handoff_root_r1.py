from pathlib import Path
import datetime
import hashlib
import json
import re
import shutil
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]
PUB = ROOT / 'tmp/github-controller-public-20261018'
REPORT = Path('reports/board-finish-20261017')
JAVA = REPORT / 'release-review/java-electrical-contacts-source-r1/actual-c7d8-native-ordinary-query-r1'
HANDOFF = Path('reports/handoff-20261018')

def sha(p):
    with p.open('rb') as f:
        return hashlib.file_digest(f, 'sha256').hexdigest()

def git(*args):
    return subprocess.check_output(['git', '-C', str(PUB), *args]).decode().strip()

def write(p, obj):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2) + '\n', encoding='utf8')

def prepare():
    selected = [Path('docs/proposals/IS3.md')]
    notes = Path('research/user-notes/2026-10-18-is3-proposal')
    selected.extend(p.relative_to(ROOT) for p in (ROOT / notes).rglob('*') if p.is_file())
    selected.append(Path('reports/documentation-refresh-20261018/is3-proposal-intake/intake.json'))
    selected.extend(Path('reports/documentation-refresh-20261018/independent-audit-followup') / n
                    for n in ('README.md', 'focused-checks.json', 'cnc1-record-check.json', 'source-supplement.json'))
    selected.extend(JAVA / n for n in ('qualification.json', 'ACTUAL_ORIGINAL_JAVA_LOAD_ONLY.log',
                                      'ACTUAL_ORIGINAL_JAVA_LOAD_ONLY-process.json', 'provenance.json'))
    selected.extend(JAVA.parent / n for n in ('NativeOrdinaryPartitionGate.java',
        'one-method-opt-in-electrical-all-contacts.patch', 'compiled-bytecode-review.json',
        'construction-receipt.json', 'run_actual_partition_gate_guarded.py'))
    selected.append(REPORT / 'publish_verifiable_handoff_root_r1.py')
    selected.extend(REPORT / 'release-review' / n for n in ('stopped-transaction-cached-source-preservation-root-r4.json',
                                                          'native-annulus-batch-stopped-transaction-root-r4.json'))
    pattern = re.compile(rb'-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|\b(?:ghp_[A-Za-z0-9]{30,}|github_pat_[A-Za-z0-9_]{40,}|hf_[A-Za-z0-9]{30,})\b')
    for rel in selected:
        src = ROOT / rel
        assert src.stat().st_size < 25_000_000, rel
        assert not pattern.search(src.read_bytes()), 'Potential credential in ' + str(rel)
        dst = PUB / rel
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, dst)
        assert sha(src) == sha(dst)
    classification = json.loads((ROOT / notes / 'sources/final_classification.json').read_text())
    examples = [x for x in classification['missing_reclassification']['true_gap_examples'] if x.get('recorded_path') == 'F.Cu']
    details = []
    def find_keys(obj, pointer=''):
        found = []
        if isinstance(obj, dict):
            for k, v in obj.items():
                child = pointer + '/' + k.replace('~', '~0').replace('/', '~1')
                if k == 'F.Cu':
                    found.append({'json_pointer':child, 'value_type':type(v).__name__, 'value':v if isinstance(v,(str,int,float)) else None})
                found.extend(find_keys(v, child))
        elif isinstance(obj, list):
            for i, v in enumerate(obj):
                found.extend(find_keys(v, pointer + '/' + str(i)))
        return found
    for item in examples:
        p = ROOT / item['manifest']
        details.append({**item, 'manifest_exists_locally':p.is_file(),
                        'manifest_sha256':sha(p) if p.is_file() else None,
                        'layer_key_occurrences':find_keys(json.loads(p.read_text(encoding='utf-8-sig'))) if p.is_file() else [],
                        'literal_workspace_root_F_Cu_exists':(ROOT / 'F.Cu').exists()})
    out = {'claimed_count':81, 'supplied_examples':len(examples), 'all81_individually_supplied':False,
           'scope':'These examples label F.Cu, a layer key. Literal filename absence is not proof of missing CAD. No synthetic F.Cu file was created.',
           'examples':details}
    write(PUB / HANDOFF / 'fcup-details.json', out)
    changed = [rel.as_posix() for rel in selected] + [(HANDOFF / 'fcup-details.json').as_posix()]
    write(ROOT / REPORT / 'handoff-publication-selection-root-r1.json', {'paths':changed})
    print(json.dumps({'copied':len(selected), 'fcup_supplied_examples':len(examples), 'credentials_scan':'no matched token/private-key patterns', 'paths':changed}))

def finalize():
    head = git('rev-parse', 'HEAD')
    remote = git('ls-remote', 'origin', 'refs/heads/codex/board-review-20261018').split()[0]
    assert remote == head
    tracked = git('ls-files', '-z').split('\0')
    count = len([x for x in tracked if x])
    delta = git('diff', '--name-only', '3e5b329e35c90eead04f72a692c61f51f71791ad', head).splitlines()
    changes = [{'path':p, 'sha256':sha(PUB / p)} for p in delta if (PUB / p).is_file()]
    q = json.loads((PUB / JAVA / 'qualification.json').read_text())
    dsn = Path('review/current-routing-setup-20261018/signal-route-first.dsn')
    assert sha(PUB / dsn) == q['DSN_SHA256']
    assert q['router_runs'] == 0 and q['resource']['exit_code'] == 0
    fcu = json.loads((PUB / HANDOFF / 'fcup-details.json').read_text())
    handoff = {
        'repo_head':{'sha':head, 'file_count':count, 'pushed_at':datetime.datetime.now(datetime.timezone.utc).isoformat()},
        'new_or_changed_files':changes,
        'freerouting_local_result':{
            'dsn_path':dsn.as_posix(), 'dsn_sha256':sha(PUB / dsn),
            'freerouting_version':'2.4.1 with opt-in electrical-contact query overlay',
            'loaded':True, 'runtime_seconds':q['load_seconds'], 'routes_added':0,
            'joins_before':837, 'joins_after':837,
            'join_counter_name':'Ordinary native-baseline pad-partition joins, matched by Java electrical query; LOAD ONLY. runtime_seconds is DSN load time, not total query time. Separate routed candidate: 1694 to 1688 cached native required joins, six closed, zero old pad pairs lost.',
            'log_path':(JAVA / 'ACTUAL_ORIGINAL_JAVA_LOAD_ONLY.log').as_posix()},
        'fcup_verification':{
            'note':'The supplied final_classification.json groups 81 F.Cu findings but supplies only 25 example manifest references. Results below are literal workspace-root F.Cu filename checks for those supplied examples, not 81 proven missing CAD files. See reports/handoff-20261018/fcup-details.json for manifest identities, hashes and actual layer-key JSON pointers. Remaining 56 not individually supplied; full existence verdict unresolved.',
            'results':[{'recorded_path':x['recorded_path'], 'exists_locally':x['literal_workspace_root_F_Cu_exists'], 'sha256':None, 'size_bytes':None} for x in fcu['examples']]},
        'adoption_status':{
            'adopted_this_session':[],
            'native_receipts_present':[{
                'path':(REPORT / 'release-review/stopped-transaction-cached-source-preservation-root-r4.json').as_posix(),
                'covers':'Existing cached-native candidate source preservation, six joins closed and zero old pad pairs lost; no full filled AFTER/DRC or adoption.'}],
            'proposals_still_open':['IS-3 remains a proposal; twelve-motor requirements unchanged',
                'Global routing, power/current/return/thermal/assembly, full native refill/DRC, FPGA physical fit/timing and physical commissioning remain open.']}}
    write(PUB / HANDOFF / 'handoff.json', handoff)
    for item in changes:
        assert sha(PUB / item['path']) == item['sha256']
    print(json.dumps({'pre_handoff_pushed_HEAD':head, 'tracked_files':count, 'changed_file_hashes':len(changes), 'handoff':str(HANDOFF / 'handoff.json')}))

if __name__ == '__main__':
    {'prepare':prepare, 'finalize':finalize}[sys.argv[1]]()
