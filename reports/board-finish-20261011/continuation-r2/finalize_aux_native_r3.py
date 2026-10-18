"""Recover the short source check with absolute paths; reuse intact native work.

The first runner received relative CLI paths. Its schematic-export command used
the source directory as cwd, so that short export failed to find the hierarchy.
Keep that failure and the native board measurement; never repeat the refill.
"""
import argparse, ast, datetime, hashlib, json, os, sys, time
from pathlib import Path
sys.dont_write_bytecode = True
import measure_aux_r1 as M
HERE = Path(__file__).resolve().parent
OUT = HERE / 'aux-native-r1/measure'

def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()

def write(p, v):
    tmp = p.with_suffix(p.suffix + '.part')
    tmp.write_text(json.dumps(v, indent=1) + '\n', encoding='utf-8')
    tmp.replace(p)

def main():
    inputs = json.loads((OUT / 'inputs.json').read_bytes())
    initial = M.helper_identities()
    for name, record in inputs['imported_helpers'].items():
        if sha(record['path']) != record['sha256']:
            raise ValueError('Launched helper changed ' + name)

    def verify(expected):
        if expected != inputs['imported_helpers']:
            raise ValueError('Unexpected launched helper contract')
        for name, record in expected.items():
            if sha(record['path']) != record['sha256']:
                raise ValueError('Launched helper changed ' + name)
        if M.helper_identities() != initial:
            raise ValueError('Finalizer helper closure changed')
    M.verify_helpers = verify
    tree = ast.parse(Path(M.__file__).read_text(encoding='utf-8'))
    fn = next((n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == 'evaluate'))
    changed = 0
    for node in ast.walk(fn):
        if isinstance(node, ast.Constant) and node.value == 'source-proof.json':
            node.value = 'source-proof-r3.json'
            changed += 1
    if changed != 1:
        raise ValueError('Evaluator source-proof selection changed')
    ns = dict(M.__dict__)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn], type_ignores=[])), 'aux-r2-evaluator', 'exec'), ns)
    evaluate = ns['evaluate']
    args = argparse.Namespace(out=OUT.resolve(), before_measure=Path('Z:/pcb-runs/claude-finish/integrate/measure/r07-ripup-signals-1').resolve(), before_board=Path(inputs['before_board']).resolve(), candidate=Path(inputs['after_board']).resolve(), r06_board=Path('Z:/pcb-runs/claude-finish/integrate/revs/r06-stitch-plane-pads-2.kicad_pcb').resolve(), r06_measure=Path('Z:/pcb-runs/claude-finish/integrate/measure/r06-stitch-plane-pads-2').resolve(), live_board=Path(inputs['live_board']).resolve(), construction=(HERE / 'aux-native-r1/construction.json').resolve())
    write(OUT / 'finalizer-inputs-r3.json', {'schema': 'aux-native-finalizer-r3', 'reason': 'Short source export used relative paths against source cwd; absolute-path retry reuses original exact native board measurement', 'original_inputs_sha256': sha(OUT / 'inputs.json'), 'original_runner_sha256': sha(M.__file__), 'original_helper_files_verified': inputs['imported_helpers'], 'finalizer_imported_helpers': initial, 'derived_evaluator_source': ast.unparse(fn), 'changes': ['CLI argument paths normalized to absolute', 'Explicit helper-name change from __main__ runner to imported runner is recorded; every original file hash remains mandatory', 'Read distinct source-proof-r3.json; preserve original failed source-proof.json'], 'native_refill_repeated': False, 'heavy_slots_added': 0, 'adopted': False})
    env = os.environ.copy()
    env['PATH'] = 'C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;' + env['PATH']
    env.update(OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    source_tree = ast.parse(Path(M.__file__).read_text(encoding='utf-8'))
    source_fn = next((n for n in source_tree.body if isinstance(n, ast.FunctionDef) and n.name == 'run_source_checks'))
    source_changed = []
    for node in ast.walk(source_fn):
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            replacements = {'native_entry.py': str((HERE / 'native_entry_width_r3.py').resolve()), 'source-export.log': 'source-export-r3.log', 'fresh.net': 'fresh-r3.net', 'native-parity.json': 'native-parity-r3.json', 'native-parity.log': 'native-parity-r3.log'}
            if node.value in replacements:
                source_changed.append([node.value, replacements[node.value]])
                node.value = replacements[node.value]
    source_namespace = dict(M.__dict__)
    exec(compile(ast.fix_missing_locations(ast.Module(body=[source_fn], type_ignores=[])), 'aux-r3-native-source-check', 'exec'), source_namespace)
    M.run_source_checks = source_namespace['run_source_checks']
    retry_contract = {'schema': 'aux-native-layer-width-retry-r3', 'original_runner_sha256': sha(M.__file__), 'native_helper_sha256': sha(HERE / 'native_entry_width_r3.py'), 'native_helper_derivation_sha256': sha(HERE / 'native-width-derivation-r3.json'), 'source_check_changes': source_changed, 'derived_source_check': ast.unparse(source_fn), 'original_assertion_stop_receipt': str((OUT / 'native-assert-stop-r2.json').resolve()), 'all_layer_annuli_identity_and_source_gates_retained': True, 'native_refill_repeated': False, 'adopted': False}
    write(OUT / 'source-check-derivation-r3.json', retry_contract)
    proof = M.run_source_checks(args, inputs, sha(OUT / 'inputs.json'), env)
    write(OUT / 'source-proof-r3.json', proof)
    print(json.dumps({'phase': 'SOURCE_RETRY_PASS', 'candidate': inputs['after_sha256']}), flush=True)
    while True:
        status = json.loads((OUT / 'status.json').read_bytes())
        if status['phase'] in ('FAILED', 'COMPLETE'):
            break
        time.sleep(2)
    if status['phase'] == 'FAILED' and (not status.get('reason', '').startswith('Source/API proof failed:')):
        raise ValueError('Original native measurement failed ' + status.get('reason', ''))
    result = evaluate(args, inputs, sha(OUT / 'inputs.json'))
    result['source_export_retry'] = {'original_source_failure': json.loads((OUT / 'source-proof.json').read_bytes()), 'retry_source_proof': str((OUT / 'source-proof-r3.json').resolve()), 'finalizer_contract': str((OUT / 'finalizer-inputs-r3.json').resolve()), 'native_refill_repeated': False}
    write(OUT / 'proof-r3.json', result)
    write(OUT / 'finalizer-status-r3.json', {'phase': 'COMPLETE', 'updated_utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'verdict': result['verdict'], 'live_completed': result['connectivity']['completed'], 'live_lost': result['connectivity']['lost'], 'r06_completed': result['connectivity_r06']['completed'], 'r06_lost': result['connectivity_r06']['lost'], 'ordinary_drc_errors': result['drc']['after']['errors'], 'adopted': False})
    print(json.dumps(json.loads((OUT / 'finalizer-status-r3.json').read_bytes())), flush=True)
if __name__ == '__main__':
    main()
