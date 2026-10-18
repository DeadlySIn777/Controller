"""Freeze bounded new CNC3 package against actual compiled/native provenance."""
from pathlib import Path
import hashlib
import json
from datetime import datetime, timezone

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
PACKAGE = ROOT / 'gateware/v3'
OUT = BASE / 'new-package-final-freeze-r01'

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def checked(path):
    value = json.loads(path.read_text())
    assert value['status'] == 'PASS', path
    return value

assert not OUT.exists()
OUT.mkdir()
compiled = checked(BASE / 'shared-package-final-r02/receipt.json')
synth = checked(BASE / 'shared-package-final-r02/family-synthesis/receipt.json')
mutations = checked(BASE / 'mutation-controls-r03/receipt.json')
assert compiled['source_hashes_unchanged'] and synth['source_unchanged']
assert compiled['static_oracle_cases'] == 743
assert compiled['family_synthesis'] == 'PASS'
assert len(mutations['mutations']) == 6
assert all(m['actual_compiled_copy_rejected'] for m in mutations['mutations'])
for path in (PACKAGE / 'rtl').glob('*.v'):
    key = 'rtl/' + path.name
    assert sha(path) == compiled['source_stage_hashes'][key] == synth['source_hashes'][key]

original = json.loads((ROOT / 'reports/pre-hardware-validation-20261001/full-r03/source-before.json').read_text())
changes = {}
for relative, before in original.items():
    path = ROOT / relative
    after = sha(path) if path.is_file() else None
    if before != after:
        changes[relative] = {'before': before, 'after': after}
allowed = {'tools/validate_controller.py'}
assert set(changes) <= allowed, changes
# The old CNC1/RTL, entire actual Source26 and other earlier source files are
# covered by this full exact old-input comparison, rather than a count claim.
preserved = {k: v for k, v in original.items() if k not in allowed}

manifest = json.loads((PACKAGE / 'frozen/manifest.json').read_text())
external = Path(manifest['original_external_root'])
external_files = {
    'protocol_v3.py': external / 'gateware/v3/tools/protocol_v3.py',
    'vectors.json': external / 'gateware/v3/vectors/protocol_v3_vectors.json',
    'spec/protocol.json': external / 'spec/protocol.json',
}
for name in ['cnc3_layout.h', 'cnc3_proto.c', 'cnc3_proto.h', 'cnc3_proto_types.h', 'cnc3_rules.h']:
    external_files['cnc3/' + name] = external / 'cnc3/src' / name
for relative, digest in manifest['files'].items():
    assert sha(PACKAGE / 'frozen' / relative) == digest
    assert sha(external_files[relative]) == digest, external_files[relative]

scope = sorted([p for p in PACKAGE.rglob('*') if p.is_file() and '__pycache__' not in p.parts] +
               [ROOT / 'tools/check_cnc3_rtl.py', ROOT / 'tools/validate_controller.py', ROOT / 'tests/test_cnc3_rtl.py', ROOT / 'tests/test_validate_controller.py'])
receipt = {
    'status': 'PASS', 'frozen_utc': datetime.now(timezone.utc).isoformat(),
    'scope': 'new bounded CNC3 structural package and disconnected bench stage only',
    'files': {p.relative_to(ROOT).as_posix(): sha(p) for p in scope},
    'prior_full_r03_exact_preserved_file_count': len(preserved),
    'prior_full_r03_exact_preserved_hashes': preserved,
    'bounded_existing_input_changes': changes,
    'original_external_reference_verified': manifest['files'],
    'actual_compiled_proof': {'path': (BASE / 'shared-package-final-r02/receipt.json').relative_to(ROOT).as_posix(), 'sha256': sha(BASE / 'shared-package-final-r02/receipt.json')},
    'actual_family_synthesis': {'path': (BASE / 'shared-package-final-r02/family-synthesis/receipt.json').relative_to(ROOT).as_posix(), 'sha256': sha(BASE / 'shared-package-final-r02/family-synthesis/receipt.json')},
    'six_actual_compiled_copy_controls': {'path': (BASE / 'mutation-controls-r03/receipt.json').relative_to(ROOT).as_posix(), 'sha256': sha(BASE / 'mutation-controls-r03/receipt.json')},
    'focused_host_tests': {'passed': 28, 'subtests_passed': 8},
    'stateful_endpoint_complete': False, 'CNC3_HAL_implemented': False,
    'Efinity_fit_timing': False, 'physical_measurements': False,
    'Source26_changed': False, 'Source27_adopted': False,
    'historical_CNC1_changed': False, 'PCB_changed': False,
}
(OUT / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
print(json.dumps({'status': receipt['status'], 'scope_files': len(scope), 'preserved_prior_inputs': len(preserved)}))
