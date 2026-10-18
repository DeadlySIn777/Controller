"""Package exact candidate and verified existing library/model resources; no adoption."""
from pathlib import Path
import hashlib,json,re,shutil,sys
import pcbnew
ROOT=Path.cwd();sys.path.insert(0,str(ROOT/'tools'))
from hardware_route_logic_return import identity
from publish_full_motherboard_board_review_wip_r03 import copy_layout_resources
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text(encoding='utf8'))
write=lambda p,v:p.write_text(json.dumps(v,indent=2)+'\n',encoding='utf8',newline='\n')
BOARD=ROOT/'reports/motherboard-return-zoning-20261002/ROOT103-bypass-PROC-composed-r01/motherboard-bounded-merged-candidate.kicad_pcb'
HASH='70b71c36778e49600b77f382cf84df81ef3ac6dce442cc0e576b494d307979cc'
BASE=ROOT/'hardware/board_review/revisions/20261001-29'
OUT=ROOT/'reports/motherboard-cad-publication-20261002/ROOT104-self-contained-native-r01'
assert sha(BOARD)==HASH and read(BOARD.parent/'local-positive-freeze-r01.json')['passed']
OUT.mkdir(exist_ok=False)
inputs={str(p):sha(p)for p in [BOARD,BOARD.with_suffix('.kicad_pro'),BOARD.with_suffix('.kicad_dru'),Path(__file__)]}
resources=[BASE/'fp-lib-table']+[f for d in BASE.iterdir()if d.is_dir()and(d.suffix in {'.pretty','.3dshapes'}or d.name=='3dmodels')for f in d.rglob('*')if f.is_file()]
for f in resources:
 dest=OUT/f.relative_to(BASE);dest.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(f,dest);inputs[str(f)]=sha(f)
for suffix in ['.kicad_pcb','.kicad_pro','.kicad_dru']:
 shutil.copyfile(BOARD.with_suffix(suffix),OUT/('motherboard-bounded-merged-candidate'+suffix))
models=[]
for name in sorted(set(re.findall(r'\(model "(\$\{KIPRJMOD\}/[^"\n]+)"',BOARD.read_text()))):
 relative=Path(name.replace('${KIPRJMOD}/',''));dest=OUT/relative
 assert dest.is_file(),name
 models.append(dict(native_reference=name,local_file=relative.as_posix(),sha256=sha(dest),resolved=True))
assert len(models)==2
layout=ROOT/'reports/motherboard-cad-publication-20261001/ROOT101-consolidated-layout-resource-review-r02.json'
verified=OUT/'resource-check';verified.mkdir()
target=OUT/BOARD.name
review=copy_layout_resources(target,ROOT/'hardware/motherboard',verified,pcbnew.LoadBoard(str(target)),layout)
old={t.m_Uuid.AsString():identity(t)for t in pcbnew.LoadBoard(str(BASE/'motherboard-native-candidate.kicad_pcb')).GetTracks()}
new={t.m_Uuid.AsString():identity(t)for t in pcbnew.LoadBoard(str(target)).GetTracks()}
assert all(new.get(u)==v for u,v in old.items())
actual=set(new)-set(old)
assert actual==set(read(BOARD.parent/'exact-composition-binding.json')['added_copper_UUIDs']) and len(actual)==48
write(OUT/'publisher-copper-delta.json',dict(changes=[],exact_additive_copper_UUIDs=sorted(actual)))
write(OUT/'warning-disposition.json',dict(board_sha256=HASH,routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=[],ignored_checks=[],remaining_required_joins=3508))
assert sha(target)==HASH and all(sha(Path(p))==h for p,h in inputs.items())
write(OUT/'preparation.json',dict(passed=True,board_sha256=HASH,input_sha256=inputs,layout_resources=review,resolved_native_project_models=models,changed_previous_copper_items=0,total_copper_delta_items=48,board_bytes_unchanged=True,published=False,adopted=False,manufacturing_ready=False))
print(json.dumps(dict(passed=True,used_libraries=len(review['used_footprint_land_checks']),models=len(models),added_copper_items=48)))
