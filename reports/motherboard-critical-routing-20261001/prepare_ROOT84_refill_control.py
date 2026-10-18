from pathlib import Path
import shutil,json,hashlib
BASE=Path('reports/motherboard-pcb-integration-20261001/source26-FPGA-flash-MISO-r84/motherboard-bounded-merged-candidate.kicad_pcb');OUT=Path('reports/motherboard-critical-routing-20261001/source26-root84-unchanged-native-refill-control-r01');OUT.mkdir(exist_ok=False)
dest=OUT/BASE.name;shutil.copyfile(BASE,dest)
for suffix in('.kicad_pro','.kicad_dru'):shutil.copyfile(BASE.with_suffix(suffix),dest.with_suffix(suffix))
for f in BASE.parent.iterdir():
 if f.is_dir()and f.suffix=='.pretty':shutil.copytree(f,OUT/f.name)
 elif f.name=='fp-lib-table':shutil.copyfile(f,OUT/f.name)
(OUT/'initial-hash.json').write_text(json.dumps(dict(base_sha256=hashlib.sha256(BASE.read_bytes()).hexdigest(),control_sha256=hashlib.sha256(dest.read_bytes()).hexdigest(),no_electrical_or_geometry_change_before_refill=True),indent=2)+'\n')
print(dest)
