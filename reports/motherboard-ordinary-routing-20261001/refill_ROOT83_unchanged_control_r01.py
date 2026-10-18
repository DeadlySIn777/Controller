"""Unchanged-native-board refill control for the remote IO3 contour diagnostic."""
from pathlib import Path
import sys,shutil,subprocess,json,hashlib
p=Path(__file__).parent;src=Path('reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83/motherboard-bounded-merged-candidate.kicad_pcb');out=p/'ROOT83-unchanged-refill-control-r01';out.mkdir(exist_ok=False);dest=out/src.name
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();original=sha(src);shutil.copyfile(src,dest)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(src.with_suffix(suffix),dest.with_suffix(suffix))
for f in src.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,out/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,out/f.name)
with(out/'native-command.txt').open('w')as log:r=subprocess.run(['C:/Program Files/KiCad/10.0/bin/kicad-cli.exe','pcb','drc','--refill-zones','--save-board','--format','json','--severity-all','--all-track-errors','-o',str(out/'native.json'),str(dest)],stdout=log,stderr=subprocess.STDOUT)
assert sha(src)==original
(out/'refill.json').write_text(json.dumps(dict(original_sha256=original,refilled_sha256=sha(dest),no_input_copper_or_project_change=True,native_command_exit=r.returncode,analysis_pending=True),indent=2));print(r.returncode)
