"""Derive separate v2; never mutate v1 or corrected design inputs."""
import hashlib, json
from pathlib import Path
HERE = Path(__file__).resolve().parent
V1 = HERE.parent/'v1'
def sha(raw): return hashlib.sha256(raw).hexdigest()

source = (V1/'restore_libraries.py').read_bytes()
text = source.decode()
text = text.replace('import sys\n', 'import sys\nimport sysconfig\n')
anchor = '\ndef main():\n'
helpers = '''
def helper_identities():
    """All loaded nonstdlib file-backed modules, including project transitives."""
    stdlib = Path(sysconfig.get_path('stdlib')).resolve()
    sites = {Path(sysconfig.get_path(role)).resolve() for role in ('purelib', 'platlib')}
    result = {}
    for name, module in sorted(sys.modules.items()):
        filename = getattr(module, '__file__', None)
        if not filename:
            continue
        path = Path(filename).resolve()
        if path.is_relative_to(stdlib) and not any(path.is_relative_to(site) for site in sites):
            continue
        if path.suffix == '.pyc':
            import importlib.util
            original = Path(importlib.util.source_from_cache(str(path)))
            if not original.is_file():
                raise ValueError('Nonstdlib helper has no bound source: ' + name)
            path = original.resolve()
        if not path.is_file():
            raise ValueError('Nonstdlib helper unavailable: ' + name)
        result[name] = {'path': str(path), 'sha256': sha(path)}
    required = {'symbol_resources', 'host_parity', 'fresh_export', 'prepare_parity',
                'run_native_parity', 'project_clone', 'finish_bridge_proof', 'partition_guard', '__main__'}
    if not required <= set(result):
        raise ValueError('Expected imported helper closure incomplete: ' + str(sorted(required-set(result))))
    return result


def verify_helpers(expected):
    current = helper_identities()
    if current != expected:
        raise ValueError('At-run imported helper identities changed')
    return current

'''
if text.count(anchor) != 1: raise ValueError('Unknown v1 structure')
text = text.replace(anchor, helpers+anchor)
text = text.replace("    native = HERE / 'native'\n", "    native = HERE / 'native'\n    helper_start = helper_identities()\n    v1_initial = tree(HERE.parent / 'v1')\n")
text = text.replace("    parser = load_parser(parser_path)\n", "    parser_initial_sha256 = sha(parser_path)\n    parser = load_parser(parser_path)\n    if sha(parser_path) != parser_initial_sha256:\n        raise ValueError('AST parser changed while loading')\n")
text = text.replace("    tools = [Path(__file__), Path(symbol_resources.__file__), parser_path, wrapper, *binaries]\n", "    verify_helpers(helper_start)\n    if sha(parser_path) != parser_initial_sha256:\n        raise ValueError('AST parser changed before native export')\n    tools = [Path(__file__), HERE / 'derivation.json', HERE / 'build_derivation.py', Path(symbol_resources.__file__), parser_path, wrapper, *binaries, Path(sys.executable),\n             *[Path(identity['path']) for identity in helper_start.values()]]\n")
text = text.replace("'native_files': initial, 'tools': frozen, 'corrected_netlist_sha256': netlist_digest, 'command': command}", "'native_files': initial, 'tools': frozen, 'imported_helper_bindings_start': helper_start,\n        'parser_at_start_sha256': parser_initial_sha256, 'corrected_netlist_sha256': netlist_digest, 'command': command}")
text = text.replace("    env = os.environ.copy()\n", "    inputs_sha256 = sha(HERE / 'inputs.json')\n    verify_helpers(helper_start)\n    env = os.environ.copy()\n")
text = text.replace("    before = parser['read_netlist'](expected_netlist)\n", "    if sha(HERE / 'inputs.json') != inputs_sha256:\n        raise ValueError('Saved inputs.json changed during export')\n    verify_helpers(helper_start)\n    before = parser['read_netlist'](expected_netlist)\n")
text = text.replace("    receipt = {'verdict': 'EMBEDDED_LIBRARY_REPAIR_AND_NATIVE_EXPORT_PASS', 'adopted': False,\n", "    helper_end = verify_helpers(helper_start)\n    if tree(HERE.parent / 'v1') != v1_initial:\n        raise ValueError('Frozen v1 was modified')\n    if sha(HERE / 'inputs.json') != inputs_sha256:\n        raise ValueError('Saved inputs.json changed before final receipt')\n    receipt = {'schema': 'source-library-restoration-v2-at-run-helpers',\n        'verdict': 'EMBEDDED_LIBRARY_REPAIR_AND_NATIVE_EXPORT_PASS', 'adopted': False,\n        'inputs_sha256': inputs_sha256, 'imported_helper_bindings_start': helper_start,\n        'imported_helper_bindings_end': helper_end, 'helper_binding_verdict': 'PASS',\n        'frozen_v1_unchanged': True, 'v1_derivation': json.loads((HERE / 'derivation.json').read_text()),\n        'run_scope': {'native_schematic_export': True, 'board_api_load': False, 'fill': False, 'drc': False, 'erc': False, 'gui_library_reload': False},\n")
text = text.replace("'Timing, ERC, DRC, electrical, live continuity and manufacturing gates remain open']}", "'Timing, ERC, DRC, electrical, live continuity and manufacturing gates remain open',\n                   'At-run helper provenance applies to v2 only; no retroactive v1 helper identity assertion']}")
output = HERE/'restore_libraries.py'
if output.exists(): raise ValueError('Fresh derivation only')
output.write_text(text, encoding='utf-8', newline='\n')
derived = output.read_bytes()
derivation = {'schema': 'source-library-v2-derivation-v1', 'source_path': str(V1/'restore_libraries.py'),
              'source_sha256': sha(source), 'source_v1_receipt_sha256': sha((V1/'receipt.json').read_bytes()),
              'derived_path': str(output), 'derived_sha256': sha(derived), 'builder_sha256': sha(Path(__file__).read_bytes()),
              'changes': ['Bind every loaded nonstdlib file-backed module, including all project transitive imports, at main entry/before native/after semantic checks',
                          'Bind AST-extracted parser before loading and export', 'Bind host Python executable alongside wrapper/native CLI/sh binaries',
                          'Bind exact saved inputs.json bytes before and after export', 'Verify complete frozen v1 tree remains unchanged',
                          'Record explicit SCH-export-only scope and no retroactive v1 provenance claim'],
              'preserved': ['Same original corrected source clone and exact four embedded-body library restoration',
                            'Complete380 symbol comparison and exact board/source/hash/semantic gates',
                            'Existing test-only heavyt.sh slot, no board/native API, refill, DRC, ERC or GUI'],
              'native_launched': False}
(HERE/'derivation.json').write_text(json.dumps(derivation, indent=2)+'\n', encoding='utf-8')
print(json.dumps({'script': str(output), 'sha256': sha(derived), 'derivation': str(HERE/'derivation.json')}))
