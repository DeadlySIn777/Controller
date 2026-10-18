"""Restore exact embedded symbol definitions into an isolated editable copy.

No board/source circuit modification, adoption, refill, DRC or ERC.
"""
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys
import sysconfig
import time

sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPORT = HERE.parent.parent
BASE = REPORT / 'electrical-correction/c11061-v2/native'
sys.path.insert(0, str(REPORT / 'final-bundle'))
import symbol_resources
sys.path.insert(0, str(REPORT / 'parity-repair'))
from host_parity import load_parser
from fresh_export import canonical
sys.path.insert(0, str(REPORT.parent / 'routing-resume-20261011'))
from finish_bridge_proof import ReadSet


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def tree(folder):
    return {p.relative_to(folder).as_posix(): sha(p)
            for p in sorted(folder.rglob('*')) if p.is_file()}


def children_raw(raw):
    """Exact spans of direct children; respect escaped quoted parentheses."""
    depth, start, quoted, escaped = 0, None, False, False
    children = []
    for i, ch in enumerate(raw):
        if quoted:
            if escaped:
                escaped = False
            elif ch == '\\':
                escaped = True
            elif ch == '"':
                quoted = False
            continue
        if ch == '"':
            quoted = True
        elif ch == '(':
            depth += 1
            if depth == 2:
                start = i
        elif ch == ')':
            if depth == 2:
                children.append(raw[start:i+1])
            depth -= 1
            if depth < 0:
                raise ValueError('Unbalanced source parentheses')
    if depth or quoted or escaped:
        raise ValueError('Incomplete source expression')
    return children


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


def main():
    native = HERE / 'native'
    helper_start = helper_identities()
    v1_initial = tree(HERE.parent / 'v1')
    if native.exists() or (HERE / 'receipt.json').exists():
        raise ValueError('Fresh isolated output required')
    base_files = tree(BASE)
    if sha(BASE / 'motherboard.kicad_pcb') != '513becb4b4ccab5626db70b64012812a58f207bfccc168fcc779c3b1a4bb1b2e':
        raise ValueError('Corrected board binding differs')
    parser_path = REPORT / 'parity-repair/c05/tools/netlist_parity.py'
    parser_initial_sha256 = sha(parser_path)
    parser = load_parser(parser_path)
    if sha(parser_path) != parser_initial_sha256:
        raise ValueError('AST parser changed while loading')
    table = parser['sexpr_parse']((BASE / 'sym-lib-table').read_text(encoding='utf-8'))
    libraries = {parser['atom'](r, 'name'): parser['atom'](r, 'uri').removeprefix('${KIPRJMOD}/')
                 for r in parser['children'](table, 'lib')}
    if any('/' in name or not name.endswith('.kicad_sym') for name in libraries.values()):
        raise ValueError('Unsupported library table location')
    missing = {name: filename for name, filename in libraries.items() if not (BASE / filename).exists()}
    if set(missing.values()) != {'motherboard_diagnostics.kicad_sym', 'motherboard_operator.kicad_sym',
                                 'motherboard_power_entry.kicad_sym', 'motherboard_terminals.kicad_sym'}:
        raise ValueError('Unexpected missing effective libraries')
    definitions = {name: {} for name in missing}
    for schematic in sorted(BASE.glob('*.kicad_sch')):
        groups = [c for c in children_raw(schematic.read_text(encoding='utf-8')) if c.startswith('(lib_symbols')]
        if len(groups) != 1:
            raise ValueError('Expected one embedded-symbol group')
        for symbol in children_raw(groups[0]):
            match = re.match(r'\(symbol\s+"([^"\\]+)"', symbol)
            if not match:
                raise ValueError('Unsupported embedded definition')
            identity = match[1]
            lib, symbol_name = identity.split(':', 1)
            if lib not in missing:
                continue
            prefix = '(symbol "' + identity + '"'
            if not symbol.startswith(prefix):
                raise ValueError('Unsupported serialized name prefix')
            exact = '(symbol "' + symbol_name + '"' + symbol[len(prefix):]
            previous = definitions[lib].get(symbol_name)
            if previous is not None and previous != exact:
                raise ValueError('Conflicting exact embedded definitions')
            definitions[lib][symbol_name] = exact
    if any(not symbols for symbols in definitions.values()):
        raise ValueError('Missing authoritative embedded definitions')
    shutil.copytree(BASE, native)
    created = {}
    for name, filename in missing.items():
        content = '(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "kicad_symbol_editor")\n'
        content += '\n'.join(definitions[name][key] for key in sorted(definitions[name])) + '\n)\n'
        (native / filename).write_text(content, encoding='utf-8')
        created[filename] = {'sha256': sha(native / filename), 'symbols': sorted(definitions[name]),
                             'derivation': 'Exact embedded body; top-level qualified lib_id converted to library symbol name only'}
    reads = ReadSet()
    library_check = symbol_resources.inventory(native, native, parser_path, reads)
    reads.verify()
    if library_check['verdict'] != 'PASS':
        raise ValueError('Complete embedded/external definition comparison failed')
    initial = tree(native)
    if any(initial.get(name) != digest for name, digest in base_files.items()) or set(initial)-set(base_files) != set(created):
        raise ValueError('Unexpected clone/source change')
    wrapper = Path('Z:/pcb-runs/claude-finish/tools/heavyt.sh')
    binaries = [Path('C:/Program Files/KiCad/10.0/bin/kicad-cli.exe'), Path('C:/Program Files/Git/usr/bin/sh.exe')]
    verify_helpers(helper_start)
    if sha(parser_path) != parser_initial_sha256:
        raise ValueError('AST parser changed before native export')
    tools = [Path(__file__), HERE / 'derivation.json', HERE / 'build_derivation.py', Path(symbol_resources.__file__), parser_path, wrapper, *binaries, Path(sys.executable),
             *[Path(identity['path']) for identity in helper_start.values()]]
    frozen = {str(p.resolve()): sha(p) for p in tools}
    expected_netlist = REPORT / 'electrical-correction/c11061-v2/corrected.net'
    netlist_digest = sha(expected_netlist)
    command = [binaries[1].as_posix(), wrapper.as_posix(), 'kicad', binaries[0].as_posix(),
               'sch', 'export', 'netlist', '--format', 'kicadsexpr', '--output',
               (HERE / 'fresh.net').as_posix(), (native / 'motherboard.kicad_sch').as_posix()]
    (HERE / 'inputs.json').write_text(json.dumps({'base_files': base_files, 'new_library_files': created,
        'native_files': initial, 'tools': frozen, 'imported_helper_bindings_start': helper_start,
        'parser_at_start_sha256': parser_initial_sha256, 'corrected_netlist_sha256': netlist_digest, 'command': command}, indent=2)+'\n')
    inputs_sha256 = sha(HERE / 'inputs.json')
    verify_helpers(helper_start)
    env = os.environ.copy()
    env['PATH'] = 'C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;' + env['PATH']
    env.update(OMP_NUM_THREADS='2', MKL_NUM_THREADS='2', OPENBLAS_NUM_THREADS='2')
    start = time.time()
    with (HERE / 'export.log').open('w', encoding='utf-8') as log:
        run = subprocess.run(command, env=env, stdout=log, stderr=subprocess.STDOUT)
    if run.returncode:
        raise ValueError('Native source export failed')
    if sha(HERE / 'inputs.json') != inputs_sha256:
        raise ValueError('Saved inputs.json changed during export')
    verify_helpers(helper_start)
    before = parser['read_netlist'](expected_netlist)
    after = parser['read_netlist'](HERE / 'fresh.net')
    if canonical(before) != canonical(after):
        raise ValueError('Circuit/component/node export semantics changed')
    final = tree(native)
    changed = {name for name in set(initial)|set(final) if initial.get(name) != final.get(name)}
    if changed - {'motherboard.kicad_prl'} or tree(BASE) != base_files:
        raise ValueError('Design inputs mutated during export')
    if sha(expected_netlist) != netlist_digest or any(sha(path) != digest for path, digest in frozen.items()):
        raise ValueError('Tool/netlist binding changed during export')
    helper_end = verify_helpers(helper_start)
    if tree(HERE.parent / 'v1') != v1_initial:
        raise ValueError('Frozen v1 was modified')
    if sha(HERE / 'inputs.json') != inputs_sha256:
        raise ValueError('Saved inputs.json changed before final receipt')
    receipt = {'schema': 'source-library-restoration-v2-at-run-helpers',
        'verdict': 'EMBEDDED_LIBRARY_REPAIR_AND_NATIVE_EXPORT_PASS', 'adopted': False,
        'inputs_sha256': inputs_sha256, 'imported_helper_bindings_start': helper_start,
        'imported_helper_bindings_end': helper_end, 'helper_binding_verdict': 'PASS',
        'frozen_v1_unchanged': True, 'v1_derivation': json.loads((HERE / 'derivation.json').read_text()),
        'run_scope': {'native_schematic_export': True, 'board_api_load': False, 'fill': False, 'drc': False, 'erc': False, 'gui_library_reload': False},
        'manufacturing_ready': False, 'board_sha256': sha(native / 'motherboard.kicad_pcb'),
        'created_libraries': created, 'all_original_native_source_files_exact': True,
        'library_comparison': library_check, 'native_export_seconds': round(time.time()-start,3),
        'fresh_netlist_sha256': sha(HERE / 'fresh.net'), 'semantic_changes': [],
        'components': len(after['components']), 'nodes': len(after['node_net']),
        'native_design_input_hashes': {k:v for k,v in final.items() if k != 'motherboard.kicad_prl'},
        'runtime_preferences_changed': sorted(changed), 'tools': frozen,
        'limits': ['Native GUI library reload not run; export uses embedded definitions',
                   'Board/source unchanged; previous c05 DRC applies to a different capacitor value hash',
                   'Historical sch.net retained; fresh.net is current corrected export',
                   'Timing, ERC, DRC, electrical, live continuity and manufacturing gates remain open',
                   'At-run helper provenance applies to v2 only; no retroactive v1 helper identity assertion']}
    (HERE / 'receipt.json').write_text(json.dumps(receipt, indent=2)+'\n')
    print(json.dumps({k:v for k,v in receipt.items() if k in ('verdict','board_sha256','components','nodes','native_export_seconds')}))


if __name__ == '__main__':
    try:
        main()
    except Exception as exc:
        (HERE / 'failure.json').write_text(json.dumps({'verdict':'FAIL','reason':str(exc),'adopted':False},indent=2)+'\n')
        raise
