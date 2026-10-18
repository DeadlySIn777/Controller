"""Record finished controls/final source identities; never launch native jobs."""
import copy, hashlib, json, sys
from pathlib import Path
sys.dont_write_bytecode = True
import compose_four as C
import measure_four as M
HERE = Path(__file__).resolve().parent
def sha(path): return hashlib.sha256(path.read_bytes()).hexdigest()
def write(path, value): path.write_text(json.dumps(value, indent=1)+'\n', encoding='utf-8')


def main():
    names = ['compose_four.py', 'measure_four.py', 'audit_four.py', 'audit.json', 'construction.json',
             'r07-four-path.kicad_pcb', 'test_four.py', 'test-four-final.log', 'capture_ready.py']
    pins = {str(HERE/name): sha(HERE/name) for name in names}
    log = (HERE/'test-four-final.log').read_text()
    if log.count(' ... ok') != 12 or not log.endswith('\nOK\n'): raise ValueError('Controls log mismatch')
    check = C.validate_construction(HERE/'construction.json', HERE/'r07-four-path.kicad_pcb')
    receipt = json.loads((HERE/'construction.json').read_bytes()); audit = json.loads((HERE/'audit.json').read_bytes())
    before = json.loads(Path('Z:/pcb-runs/claude-finish/integrate/measure/r07-ripup-signals-1/partitions.json').read_bytes())
    r06 = json.loads(Path('Z:/pcb-runs/claude-finish/integrate/measure/r06-stitch-plane-pads-2/partitions.json').read_bytes())
    after = copy.deepcopy(before)
    for row in audit['rows']:
        groups = after['nets'][row['net']]; selected = [set(group) for group in row['physical_pad_groups']]
        indices = [i for i, group in enumerate(groups) if set(group) in selected]
        if len(indices) != 2: raise ValueError('Synthetic selected native groups mismatch')
        after['nets'][row['net']] = [group for i, group in enumerate(groups) if i not in indices] + [sorted(set(groups[indices[0]]) | set(groups[indices[1]]))]
    after['pad_island_joins'] -= 4; after['api_unconnected_count'] -= 4
    synthetic = {'evidence_class': 'HOST_GUARD_CONTROL_ONLY_NOT_NATIVE_CANDIDATE', 'r07_live': M.compare(before, after), 'r06': M.compare(r06, after)}
    synthetic['combined_verdict'] = M.combined_verdict(synthetic['r07_live'], synthetic['r06'], 0)
    if synthetic['r07_live']['lost'] != 0 or synthetic['r07_live']['completed'] != 4 or synthetic['r06']['lost'] != 14 or synthetic['combined_verdict'] != 'FAIL': raise ValueError('No-loss guard regression')
    write(HERE/'synthetic-guard-control.json', synthetic)
    original = HERE.parent/'two-zero-via/measure_two.py'; derived = HERE/'measure_four.py'
    expected = original.read_text().replace('Measure two pure-add r07 signals', 'Measure four pure-add r07 signals').replace('from compose_two import', 'from compose_four import').replace('compose_two.py', 'compose_four.py').replace('audit_two.py', 'audit_four.py')
    if derived.read_text() != expected: raise ValueError('Unexpected native runner derivation')
    derivation = {'schema': 'four-path-native-runner-derivation-v1', 'source': str(original), 'source_sha256': sha(original),
                  'derived': str(derived), 'derived_sha256': sha(derived),
                  'changes': ['Documentation names four paths', 'Use distinct compose_four validator', 'Snapshot distinct compose_four/audit_four sources'],
                  'preserved': ['Both r07/live and r06 strict guards; any lost connections remain fatal',
                                'All-severity raw native DRC and exact r06/r07 baseline evidence bindings',
                                'Project/rules/libraries/footprints/source bindings before and after',
                                'Exact inputs.json bytes plus all four native binary identities before and after',
                                'One existing shared heavy.sh slot; no native jobs started here',
                                'CLI/API parity remains explicitly unexecuted/separately required']}
    write(HERE/'runner-derivation.json', derivation)
    native = M.binary_identities(M.ReadSet())
    ready = {'schema': 'r07-four-path-ready-host-v1', 'verdict': 'SOURCE_HOST_PASS_NATIVE_ELECTRICAL_OPEN',
             'source_files_sha256': pins, 'construction_check': check, 'controls_passed': 12,
             'controls_log': {'path': str(HERE/'test-four-final.log'), 'sha256': sha(HERE/'test-four-final.log'),
                              'capture': 'Exact combined terminal tool output from completed host session74381; no tests rerun'},
             'runner_derivation_sha256': sha(HERE/'runner-derivation.json'), 'native_binaries_at_ready': native,
             'synthetic_guard_control_path': str(HERE/'synthetic-guard-control.json'),
             'synthetic_guard_control_sha256': sha(HERE/'synthetic-guard-control.json'),
             'native_launched': False, 'native_gate': 'OPEN; must pass BOTH actual live/r07 and original r06 plus DRC',
             'full_return_zone_island_neck_critical_safety_current_si_gates': 'OPEN',
             'adopted': False, 'manufacturing_ready': False}
    for path, expected_sha in pins.items():
        if sha(Path(path)) != expected_sha: raise ValueError('Source changed while freezing: '+path)
    write(HERE/'ready.json', ready)
    print(json.dumps({'ready': str(HERE/'ready.json'), 'ready_sha256': sha(HERE/'ready.json'), 'pins': pins,
                      'native_launched': False, 'controls_passed': 12, 'synthetic_live_completed': synthetic['r07_live']['completed'],
                      'synthetic_r06_completed': synthetic['r06']['completed'], 'synthetic_r06_lost': synthetic['r06']['lost']}, indent=1))


if __name__ == '__main__': main()
