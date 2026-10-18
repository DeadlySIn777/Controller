"""Stage exact health PCB bytes and local primary-source resources; no publication/adoption."""
from pathlib import Path
import hashlib, json, re, shutil, sys
import pcbnew
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
from hardware_route_logic_return import identity
from publish_full_motherboard_board_review_wip_r03 import copy_layout_resources
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8',newline='\n')
BOARD=ROOT/'reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb'
HASH='639e1b7803bfaa24480d824d97d0d487e545b658a0e3e343435e8297083ef053'
BASE=ROOT/'hardware/board_review/revisions/20261001-28'
OUT=ROOT/'reports/motherboard-cad-publication-20261001/health-r31-self-contained-native-r01'
assert sha(BOARD)==HASH and read(BOARD.parent/'local-positive-freeze-r01.json')['passed']
OUT.mkdir(exist_ok=False)
inputs={str(p):sha(p)for p in [BOARD,BOARD.with_suffix('.kicad_pro'),BOARD.with_suffix('.kicad_dru'),Path(__file__)]}
resources=[BASE/'fp-lib-table']+[f for directory in BASE.iterdir()if directory.is_dir()and(directory.suffix in {'.pretty','.3dshapes'}or directory.name=='3dmodels')for f in directory.rglob('*')if f.is_file()]
for f in resources:
    dest=OUT/f.relative_to(BASE);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);inputs[str(f)]=sha(f)
for suffix in ['.kicad_pcb','.kicad_pro','.kicad_dru']:
    shutil.copyfile(BOARD.with_suffix(suffix),OUT/('motherboard-bounded-merged-candidate'+suffix))
# Resolve actual native model references; a successful render alone doesn't
# establish that the manufacturer's socket body was loaded.
models=[]
for name in sorted(set(re.findall(r'\(model "(\$\{KIPRJMOD\}/[^"\n]+)"',BOARD.read_text()))):
    relative=Path(name.replace('${KIPRJMOD}/',''));dest=OUT/relative
    if not dest.exists():
        source=ROOT/'hardware/motherboard_compute'/relative
        if not source.exists():raise ValueError('Unresolved native model resource: '+name)
        dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(source,dest);inputs[str(source)]=sha(source)
    models.append(dict(native_reference=name,local_file=relative.as_posix(),sha256=sha(dest),resolved=True))
assert len(models)==2
layout=ROOT/'reports/motherboard-cad-publication-20261001/ROOT101-consolidated-layout-resource-review-r02.json'
verified=OUT/'resource-check';verified.mkdir()
target=OUT/BOARD.name
review=copy_layout_resources(target,ROOT/'hardware/motherboard',verified,pcbnew.LoadBoard(str(target)),layout)
oldboard=BASE/'motherboard-native-candidate.kicad_pcb'
old={t.m_Uuid.AsString():identity(t)for t in pcbnew.LoadBoard(str(oldboard)).GetTracks()}
new={t.m_Uuid.AsString():identity(t)for t in pcbnew.LoadBoard(str(target)).GetTracks()}
merger=read(BOARD.parent/'receipt.json')
allowed={x['uuid']for x in merger['exact_copper_delta']}
changed={u for u,v in old.items()if new.get(u)!=v}
actual={u for u in set(old)|set(new)if old.get(u)!=new.get(u)}
assert actual==allowed
ledger=dict(changes=[dict(uuid=u,old_identity=old[u],new_identity=new.get(u),
    reason='Exact retained-copper replacement in Source26 health receiving-cell correction. Final r31 strict loops, source-cluster preservation, registration, reference/control and independent connectivity are retained. This is incomplete-board CAD publication scope only.')for u in sorted(changed)],
    bounded_merge_receipt_sha256=sha(BOARD.parent/'receipt.json'))
write(OUT/'publisher-copper-delta.json',ledger)
write(OUT/'warning-disposition.json',dict(board_sha256=HASH,routing_incomplete=True,manufacturing_ready=False,
    known_unresolved_native_warnings=[],ignored_checks=[],remaining_required_joins=3521))
assert sha(target)==HASH and all(sha(Path(p))==h for p,h in inputs.items())
write(OUT/'preparation.json',dict(passed=True,board_sha256=HASH,input_sha256=inputs,layout_resources=review,
    resolved_native_project_models=models,changed_previous_copper_items=len(changed),total_copper_delta_items=len(actual),
    missed_project_models_in_prior_CAD28=[m['native_reference']for m in models if not(BASE/m['local_file']).exists()],
    board_bytes_unchanged=True,published=False,adopted=False,manufacturing_ready=False))
print(json.dumps(dict(passed=True,used_libraries=len(review['used_footprint_land_checks']),models=len(models),changed_previous_copper_items=len(changed))))
