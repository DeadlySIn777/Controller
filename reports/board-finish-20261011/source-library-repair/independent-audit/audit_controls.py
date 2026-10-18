"""Read-only independent v1 mapping audit and tiny isolated host controls."""
import hashlib, importlib.util, json, re, sys, tempfile, time, unittest
from pathlib import Path
sys.dont_write_bytecode = True
HERE = Path(__file__).resolve().parent
REPORT = HERE.parent.parent
V1 = HERE.parent/'v1'
BASE = REPORT/'electrical-correction/c11061-v2/native'
PARSER = REPORT/'parity-repair/c05/tools/netlist_parity.py'
sys.path.insert(0, str(REPORT/'final-bundle'))
import symbol_resources as SR
sys.path.insert(0, str(REPORT/'parity-repair'))
from host_parity import load_parser
from fresh_export import canonical as net_canonical
sys.path.insert(0, str(REPORT.parent/'routing-resume-20261011'))
from finish_bridge_proof import ReadSet
spec = importlib.util.spec_from_file_location('frozen_v1_restore', V1/'restore_libraries.py')
RESTORE = importlib.util.module_from_spec(spec); spec.loader.exec_module(RESTORE)

def sha(raw): return hashlib.sha256(raw).hexdigest()
def tree(path): return {p.relative_to(path).as_posix(): sha(p.read_bytes()) for p in sorted(path.rglob('*')) if p.is_file()}


def fixture(directory, external_number='1', external_name='SIGNAL', extra_schematic=None, duplicate_table=False, numeric_spellings=False):
    folder = Path(directory)
    lib = '(lib (name "test") (type "KiCad") (uri "${KIPRJMOD}/test.kicad_sym") (options "") (descr ""))'
    table = '(sym_lib_table '+lib+(' '+lib if duplicate_table else '')+')\n'
    folder.joinpath('sym-lib-table').write_text(table)
    def body(number, name, numeric='0'):
        return '(symbol "S_1_1" (pin input line (at '+numeric+' 0 0) (length 2.54) (name "'+name+'") (number "'+number+'")))'
    embedded = '(kicad_sch (lib_symbols (symbol "test:S" '+body('1', 'SIGNAL')+')))\n'
    external = '(kicad_symbol_lib (version 20241209) (generator "kicad_symbol_editor") (symbol "S" '+body(external_number, external_name, '0.000' if numeric_spellings else '0')+'))\n'
    folder.joinpath('root.kicad_sch').write_text(embedded)
    folder.joinpath('test.kicad_sym').write_text(external)
    if extra_schematic is not None:
        folder.joinpath('child.kicad_sch').write_text('(kicad_sch (lib_symbols (symbol "test:S" '+body(extra_schematic, 'SIGNAL')+')))\n')
    return folder


class Controls(unittest.TestCase):
    def inventory(self, folder):
        reads = ReadSet(); result = SR.inventory(folder, folder, PARSER, reads); reads.verify(); return result

    def test_equal_full_definition_passes(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            result = self.inventory(fixture(tmp)); self.assertEqual(result['verdict'], 'PASS')

    def test_pin_number_leading_zero_remains_exact(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            result = self.inventory(fixture(tmp, external_number='01'))
            self.assertEqual(result['verdict'], 'OPEN_RESOURCE_MISMATCH')
            self.assertEqual(result['definition_mismatches'][0]['lib_id'], 'test:S')

    def test_pin_name_change_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            self.assertEqual(self.inventory(fixture(tmp, external_name='OTHER_SIGNAL'))['verdict'], 'OPEN_RESOURCE_MISMATCH')

    def test_only_geometry_numeric_spelling_normalised(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            self.assertEqual(self.inventory(fixture(tmp, numeric_spellings=True))['verdict'], 'PASS')

    def test_conflicting_embedded_cache_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            folder = fixture(tmp, extra_schematic='2')
            with self.assertRaisesRegex(ValueError, 'Conflicting embedded symbol definitions'):
                self.inventory(folder)

    def test_duplicate_effective_role_rejected(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            folder = fixture(tmp, duplicate_table=True)
            with self.assertRaisesRegex(ValueError, 'Duplicate symbol library identity'):
                self.inventory(folder)

    def test_missing_library_stays_open(self):
        with tempfile.TemporaryDirectory(dir=HERE) as tmp:
            folder = fixture(tmp); folder.joinpath('test.kicad_sym').unlink()
            self.assertEqual(self.inventory(folder)['verdict'], 'OPEN_RESOURCE_MISMATCH')

    def test_exact_span_parser_respects_quotes_and_escaped_parentheses(self):
        raw = '(root (property "Description" "text \\\"quoted\\\" (nested) \\\\ tail") (symbol "x" (pin (number "01"))))'
        children = RESTORE.children_raw(raw)
        self.assertEqual(len(children), 2); self.assertTrue(children[0].endswith('tail")'))
        self.assertIn('(number "01")', children[1])
        with self.assertRaises(ValueError): RESTORE.children_raw('(root (symbol "unfinished")')


def main():
    initial = {'v1': tree(V1), 'corrected_base': tree(BASE)}
    reads = ReadSet()
    inputs = json.loads(reads.read(V1/'inputs.json')); receipt = json.loads(reads.read(V1/'receipt.json'))
    for relative, expected in inputs['base_files'].items():
        if sha(reads.read(BASE/relative)) != expected: raise ValueError('Original corrected source changed: '+relative)
    created = set(receipt['created_libraries'])
    expected_missing = {'motherboard_diagnostics.kicad_sym', 'motherboard_operator.kicad_sym', 'motherboard_power_entry.kicad_sym', 'motherboard_terminals.kicad_sym'}
    if created != expected_missing or set(inputs['native_files'])-set(inputs['base_files']) != created: raise ValueError('Unexpected repair scope')
    for relative, expected in receipt['native_design_input_hashes'].items():
        if sha(reads.read(V1/'native'/relative)) != expected: raise ValueError('Restored clone changed: '+relative)
    for relative, expected in inputs['base_files'].items():
        if relative != 'motherboard.kicad_prl' and sha(reads.read(V1/'native'/relative)) != expected: raise ValueError('Original design bytes changed: '+relative)
    parser = load_parser(PARSER)
    table = parser['sexpr_parse'](reads.read(BASE/'sym-lib-table').decode())
    roles = [(parser['atom'](row, 'name'), parser['atom'](row, 'uri')) for row in parser['children'](table, 'lib')]
    if len({name for name, _ in roles}) != len(roles): raise ValueError('Actual table has duplicate effective role')
    missing = {name: uri.removeprefix('${KIPRJMOD}/') for name, uri in roles if not (BASE/uri.removeprefix('${KIPRJMOD}/')).is_file()}
    if set(missing.values()) != expected_missing: raise ValueError('Actual missing mapping differs')
    definitions = {name: {} for name in missing}; authoritative_files = []
    for path in sorted(BASE.glob('*.kicad_sch')):
        # Verify exact text reconstruction independently of the receipt's
        # parsed/numeric canonical comparison. The bounded span parser itself
        # has a quoted-parenthesis rejection control above.
        # Match the reviewed producer's read_text/write_text newline roundtrip
        # on Windows, without normalising any symbol/property/pin content.
        raw = reads.read(path).decode().replace('\r\n', '\n'); groups = [child for child in RESTORE.children_raw(raw) if child.startswith('(lib_symbols')]
        if len(groups) != 1: raise ValueError('Ambiguous embedded group')
        touched = False
        for symbol in RESTORE.children_raw(groups[0]):
            match = re.match(r'\(symbol\s+"([^"\\]+)"', symbol)
            if not match: raise ValueError('Unexpected embedded name')
            identity = match[1]; lib, name = identity.split(':', 1)
            if lib not in missing: continue
            prefix = '(symbol "'+identity+'"'; exact = '(symbol "'+name+'"'+symbol[len(prefix):]
            if name in definitions[lib] and definitions[lib][name] != exact: raise ValueError('Conflicting authoritative body')
            definitions[lib][name] = exact; touched = True
        if touched: authoritative_files.append(path.name)
    mapping = []
    for role, filename in missing.items():
        expected = '(kicad_symbol_lib\n\t(version 20241209)\n\t(generator "kicad_symbol_editor")\n'+'\n'.join(definitions[role][name] for name in sorted(definitions[role]))+'\n)\n'
        actual = reads.read(V1/'native'/filename)
        expected_bytes = expected.encode().replace(b'\n', b'\r\n')
        if actual != expected_bytes: raise ValueError('Library is not exact embedded-body reconstruction: '+filename)
        if sha(actual) != receipt['created_libraries'][filename]['sha256']: raise ValueError('Created library receipt digest differs')
        mapping.append({'effective_role': role, 'uri': '${KIPRJMOD}/'+filename, 'symbols': len(definitions[role]), 'sha256': sha(actual), 'exact_body_replay': True, 'text_newline_roundtrip': 'Windows CRLF, matching producer read_text/write_text'})
    # The native export already ran. Only reproduce its host semantic check.
    corrected = REPORT/'electrical-correction/c11061-v2/corrected.net'
    reads.read(corrected); reads.read(V1/'fresh.net')
    semantic_exact = net_canonical(parser['read_netlist'](corrected)) == net_canonical(parser['read_netlist'](V1/'fresh.net'))
    if not semantic_exact: raise ValueError('Existing fresh native export semantics differ')
    for path in [Path(__file__), V1/'restore_libraries.py', Path(SR.__file__), PARSER,
                 REPORT/'parity-repair/host_parity.py', REPORT/'parity-repair/fresh_export.py',
                 REPORT.parent/'routing-resume-20261011/finish_bridge_proof.py']:
        reads.read(path)
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(Controls)
    with (HERE/'controls.log').open('w', encoding='utf-8') as stream:
        result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    if not result.wasSuccessful(): raise ValueError('Isolated host rejection control failed')
    reads.verify()
    if tree(V1) != initial['v1'] or tree(BASE) != initial['corrected_base']: raise ValueError('Frozen source/input tree mutated during audit')
    output = {'schema': 'source-library-v1-independent-mapping-audit-v1', 'verdict': 'PASS_WITH_DECLARED_SCOPE',
              'frozen_v1_receipt_sha256': sha((V1/'receipt.json').read_bytes()), 'frozen_v1_inputs_sha256': sha((V1/'inputs.json').read_bytes()),
              'corrected_board_sha256': receipt['board_sha256'], 'all_original_design_files_byte_exact': True,
              'only_four_missing_libraries_created': True, 'mapping': mapping, 'authoritative_embedded_source_files': authoritative_files,
              'reported_complete_definition_comparison': {'embedded_unique_symbols': receipt['library_comparison']['embedded_unique_symbols'], 'external_symbols': receipt['library_comparison']['external_symbols'], 'verdict': receipt['library_comparison']['verdict']},
              'existing_native_export_host_semantics_reproduced_exact': semantic_exact, 'components': receipt['components'], 'nodes': receipt['nodes'],
              'isolated_host_controls': result.testsRun, 'controls_passed': result.wasSuccessful(), 'controls_log_sha256': sha((HERE/'controls.log').read_bytes()),
              'observed_file_hashes': reads.hashes, 'frozen_source_trees_unchanged': True, 'native_jobs': 0, 'adopted': False, 'manufacturing_ready': False,
              'limits': ['Authority is corrected schematic embedded definitions, not manufacturer datasheet validation',
                         'Native fresh export uses embedded source cache; native GUI external-library reload not independently proven',
                         '380-definition full host audit is inherited v1 receipt; four generated libraries independently replayed byte-exact',
                         'Original v1 tool closure omits imported canonical/load_parser/ReadSet source hashes; their current identities captured by this audit, not retroactive at-run proof',
                         'Corrected C11061 board hash differs from prior c05 DRC; ERC/DRC/live continuity/timing/electrical/manufacturing gates remain open']}
    (HERE/'receipt.json').write_text(json.dumps(output, indent=1)+'\n', encoding='utf-8')
    print(json.dumps({'receipt': str(HERE/'receipt.json'), 'verdict': output['verdict'], 'controls': result.testsRun, 'mapping': mapping}, indent=1))


if __name__ == '__main__': main()
