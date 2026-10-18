"""Make an exact board copy with its actual resolved footprint libraries local.

No footprint definition, native board, Source or fabrication-rule edit.
"""
from pathlib import Path
import sys,re,json,shutil
sys.path.insert(0,str(Path('tools').resolve()))
from hardware_populate_motherboard_pcb import sha,write
from publish_full_motherboard_board_review_wip_r02 import copy_layout_resources
import pcbnew
base=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-U25-C19033-merged-trial-r101')
out=Path('reports/motherboard-cad-publication-20261001/ROOT101-self-contained-native-r01')
assert not out.exists();out.mkdir()
board=base/'motherboard-bounded-merged-candidate.kicad_pcb'
inputs={str(p.resolve()):sha(p)for p in [board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru'),base/'fp-lib-table',Path(__file__)]}
for f in [board,board.with_suffix('.kicad_pro'),board.with_suffix('.kicad_dru')]:shutil.copyfile(f,out/f.name)
table=(base/'fp-lib-table').read_text();rows=[]
for nickname,uri in re.findall(r'\(lib \(name "([^"]+)"\) \(type "KiCad"\) \(uri "([^"]+)"\)',table):
 actual=Path(uri.replace('${KIPRJMOD}',str(base.resolve())))
 assert actual.is_dir(),(nickname,actual)
 dest=out/(nickname+'.pretty');assert not dest.exists();shutil.copytree(actual,dest)
 files={str(f.resolve()):sha(f)for f in actual.rglob('*')if f.is_file()};inputs.update(files)
 for f,h in files.items():assert sha(dest/Path(f).relative_to(actual.resolve()))==h
 rows.append(dict(nickname=nickname,original_uri=uri,actual_library=str(actual.resolve()),files=len(files)))
 table=table.replace('(uri "'+uri+'")','(uri "${KIPRJMOD}/'+nickname+'.pretty")')
(out/'fp-lib-table').write_text(table)
assert sha(out/board.name)==sha(board)
# Use the existing strict publisher check to qualify every actual FPID's
# manufacturer lands and the exact original reviewed silk/Fab overrides.
layout=Path('hardware/board_review/revisions/20260930-24/layout-graphics-review.json')
check=out/'verified-copy';check.mkdir()
result=copy_layout_resources(out/board.name,Path('hardware/motherboard'),check,pcbnew.LoadBoard(str(out/board.name)),layout)
assert all(sha(Path(k))==h for k,h in inputs.items())
write(out/'receipt.json',dict(passed=True,board_sha256=sha(board),input_sha256=inputs,libraries=rows,actual_resource_land_review=result,only_relative_library_locations_changed=True,native_board_and_project_rule_bytes_preserved=True,manufacturing_ready=False))
print(dict(passed=True,libraries=len(rows),used_FPIDs_checked=len(result['used_footprint_land_checks'])))
