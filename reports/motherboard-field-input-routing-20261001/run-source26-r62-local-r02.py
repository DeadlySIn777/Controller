from pathlib import Path
import sys,json,subprocess,hashlib
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from hardware_scope_anchored_reference_pieces import qualify
P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-orphan-free-adopted-r62'
OUT=ROOT/'reports/motherboard-field-input-routing-20261001/source26-r62-local-r02'
OUT.mkdir(exist_ok=False)
proof=qualify(P/'actual-board-bound-reference-review.json',ROOT/'reports/motherboard-domains-20261001/source26-r62-r01/domain-map.json',P/'motherboard-source26-WIP.kicad_pcb',{'/motherboard_do/FIELD_B_0V'},{'In1.Cu'})
(OUT/'piece-eligibility.json').write_text(json.dumps(proof,indent=2)+'\n')
args=[sys.executable,str(ROOT/'tools/hardware_route_field_input_cells.py'),
 '--board',str(P/'motherboard-source26-WIP.kicad_pcb'),
 '--source',str(ROOT/'hardware/motherboard'),
 '--adoption',str(ROOT/'reports/motherboard-integration-20261001/source26-reference-fuse-adopted-r04/adoption.json'),
 '--review',str(ROOT/'reports/motherboard-field-input-routing-20261001/source26-local-review-r01/source-review.json'),
 '--planes',str(OUT/'piece-eligibility.json'),
 '--baseline-disposition',str(P/'baseline-disposition.json'),
 '--out',str(OUT/'actual-routing')]
run=subprocess.run(args,capture_output=True,text=True)
(OUT/'command.json').write_text(json.dumps(dict(args=args,returncode=run.returncode),indent=2))
(OUT/'command.txt').write_text(run.stdout+run.stderr)
print(run.stdout+run.stderr);raise SystemExit(run.returncode)
