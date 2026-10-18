"""Copy the adopted native project into an isolated, verified routing handoff."""
from pathlib import Path
import hashlib
import json
import re
import shutil
import zipfile
import pcbnew

ROOT = Path.cwd().resolve()
HERE = ROOT / 'reports/argus-routing-handoff-20261002'
OUT = HERE / 'ROOT104-CAD30'
SOURCE = ROOT / 'hardware/board_review/revisions/20261002-30'
BOARD_NAME = 'motherboard-native-candidate.kicad_pcb'
EXPECTED = '70b71c36778e49600b77f382cf84df81ef3ac6dce442cc0e576b494d307979cc'
ADOPT = ROOT / 'reports/motherboard-return-zoning-20261002/ROOT103-bypass-PROC-composed-r01'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
read = lambda p: json.loads(p.read_text(encoding='utf8'))

def write(p, value):
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(value, indent=2) + '\n', encoding='utf8', newline='\n')

assert HERE.is_relative_to(ROOT) and OUT.is_relative_to(HERE)
assert not OUT.exists()
assert sha(SOURCE / BOARD_NAME) == EXPECTED
assert sha(ROOT / 'hardware/motherboard/design.json') == '6ec697f7ab420648de187b963b35825a695c3af00d25a9efd5844a8c908a8cb8'
assert sha(ROOT / 'hardware/motherboard/netlist.xml') == '9f2c3c7b1e1b8f8cf108d0460dd0f709033f6ebdbf7f7a1b596abf1190eec633'
inputs = {}
origin = {}

def copy(src, dest):
    assert src.is_file() and not src.is_symlink(), src
    inputs[str(src.relative_to(ROOT))] = sha(src)
    dest.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(src, dest)
    assert sha(dest) == inputs[str(src.relative_to(ROOT))]
    origin[dest.relative_to(OUT).as_posix()] = src.relative_to(ROOT).as_posix()

OUT.mkdir()
for src in sorted(SOURCE.rglob('*')):
    if src.is_file() and src.suffix not in ('.kicad_prl', '.lck'):
        copy(src, OUT / 'native' / src.relative_to(SOURCE))

proofs = [
    ADOPT / 'adoption.json', ADOPT / 'current120-bypass-manifest.json',
    ADOPT / 'current120-strict-proof-r01.json', ADOPT / 'literal-resources-r01.json',
    ADOPT / 'unchanged-global-IO3-r07.json', ADOPT / 'new-drill-registration-r01.json',
    ADOPT / 'composed-PROC-return-r01.json', ADOPT / 'independent-inventory-r01/review.json',
    ROOT / 'reports/pre-hardware-validation-20261002/full-bypass-PROC-seeded-IS2-r08/report.json',
    ROOT / 'reports/motherboard-pcb-integration-20261002/ROOT103-bypass-PROC-full-drill-SMD-r01/receipt.json',
    ROOT / 'reports/motherboard-erc-20261002/source26-exact-warning-disposition-r01/receipt.json',
    ROOT / 'reports/motherboard-integration-20261001/source27-health-feed-reset-staged-r02/source27-successor-rebinding-plan-r02.json',
    ROOT / 'reports/motherboard-power-entry-20261001/Source27-Argus-report-only-checkpoint-r644/checkpoint.json',
    ROOT / 'reports/freerouting-evaluation-20261002/ROOT103-GPIO-config-visual-allowlist-r04/selected-nets.json',
    ROOT / 'reports/freerouting-evaluation-20261002/ROOT103-GPIO-config-visual-allowlist-r04/source-scope-review.json',
    ROOT / 'reports/freerouting-evaluation-20261002/ROOT103-local-topology-handoff-r01/receipt.json',
    ROOT / 'reports/freerouting-evaluation-20261002/ROOT103-local-topology-handoff-r01/README.md',
    ROOT / 'hardware/fpga_core/pin-allocation.json',
    ROOT / 'hardware/motherboard/fpga-allocation-applied.json',
    ROOT / 'hardware/motherboard/bom.csv',
    ROOT / 'docs/MOTHERBOARD_IS2.md', ROOT / 'docs/CURRENT_ACCEPTANCE_GATES.md',
]
for src in proofs:
    copy(src, OUT / 'evidence' / src.relative_to(ROOT))
for name in ('START_HERE.md', 'ARGUS_PROMPT.txt'):
    copy(HERE / name, OUT / name)

native = OUT / 'native' / BOARD_NAME
board = pcbnew.LoadBoard(str(native))
board.BuildConnectivity()
counts = dict(footprints=len(board.GetFootprints()), copper_objects=len(board.GetTracks()),
              zones_and_ruleareas=len(board.Zones()), copper_layers=board.GetCopperLayerCount())
assert counts == dict(footprints=2688, copper_objects=11807, zones_and_ruleareas=1544, copper_layers=6), counts
models = []
for ref in sorted(set(re.findall(r'\(model "(\$\{KIPRJMOD\}/[^"\n]+)"', native.read_text(encoding='utf8')))):
    p = native.parent / ref.replace('${KIPRJMOD}/', '')
    assert p.is_file(), ref
    models.append(dict(reference=ref, file=p.relative_to(OUT).as_posix(), sha256=sha(p)))
assert len(models) == 2
for table in [native.parent / 'fp-lib-table', native.parent / 'source-inputs/sym-lib-table']:
    for ref in re.findall(r'\(uri "\$\{KIPRJMOD\}/([^"\n]+)"', table.read_text(encoding='utf8')):
        assert (table.parent / ref).exists(), (table, ref)

inventory = read(ADOPT / 'independent-inventory-r01/review.json')
assert inventory['board_sha256'] == EXPECTED
write(OUT / 'baseline.json', dict(
    board_sha256=EXPECTED, revision='ROOT104 / CAD30', electrical_source='Source26',
    native_board='native/' + BOARD_NAME, counts=counts,
    required_joins=3508, fully_joined_multi_pad_nets=633, incomplete_multi_pad_nets=1101,
    regular_DRC_errors=0, regular_DRC_warnings=0, ignored_checks=[],
    ERC_errors=0, ERC_unsuppressed_warnings=70, manufacturing_ready=False,
    source27_included=False, current_scoped_bypass_loops=120,
    current_scoped_receiving_returns=245, current_source_anchored_filled_resources=188,
    native_bytes_unchanged=True, existing_copper_mechanically_locked_by_this_handoff=False,
    protection='Preserve baseline object identities and geometry; no KiCad lock flags changed.',
    models=models, report_paths='Evidence snapshots retain original workspace paths; use origin-map.json to find included copies.'))
write(OUT / 'origin-map.json', origin)
assert sha(native) == EXPECTED
assert all(sha(ROOT / rel) == h for rel, h in inputs.items())
files = {p.relative_to(OUT).as_posix(): dict(sha256=sha(p), bytes=p.stat().st_size)
         for p in sorted(OUT.rglob('*')) if p.is_file()}
write(OUT / 'SHA256-MANIFEST.json', dict(files=files, excludes_self=True, board_sha256=EXPECTED))
archive = HERE / 'ROOT104-CAD30-Argus-routing.zip'
assert not archive.exists()
with zipfile.ZipFile(archive, 'x', compression=zipfile.ZIP_DEFLATED, compresslevel=6) as z:
    for p in sorted(OUT.rglob('*')):
        if p.is_file():
            z.write(p, (Path(OUT.name) / p.relative_to(OUT)).as_posix())
with zipfile.ZipFile(archive) as z:
    assert z.testzip() is None
    for rel, row in files.items():
        assert hashlib.sha256(z.read(OUT.name + '/' + rel)).hexdigest() == row['sha256'], rel
    assert z.read(OUT.name + '/SHA256-MANIFEST.json') == (OUT / 'SHA256-MANIFEST.json').read_bytes()
assert all(sha(ROOT / rel) == h for rel, h in inputs.items())
write(HERE / 'packaging-receipt-r01.json', dict(
    passed=True, native_load_pass=True, counts=counts, board_sha256=EXPECTED,
    archive=archive.relative_to(ROOT).as_posix(), archive_sha256=sha(archive), archive_bytes=archive.stat().st_size,
    packaged_file_count=len(files)+1, all_zip_member_hashes_verified=True, sources_unchanged=True,
    input_sha256=inputs, CAD_or_source_adopted=False, new_routing=False,
    native_ERC_DRC_rerun=False, reason='Copy-only packaging; unchanged exact prior validation included.',
    manufacturing_ready=False))
print(json.dumps(dict(passed=True, archive=str(archive), bytes=archive.stat().st_size,
                     files=len(files)+1, board_sha256=EXPECTED, counts=counts)))
