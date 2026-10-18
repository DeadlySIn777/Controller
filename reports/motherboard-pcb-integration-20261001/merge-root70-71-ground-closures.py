"""Integrate two independently checked additive ground transactions."""
import json,subprocess,sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2];sys.path.insert(0,str(ROOT/'tools'))
from hardware_populate_motherboard_pcb import sha,write
base=ROOT/'reports/motherboard-pcb-integration-20261001/source26-C17014-bypass-r69/motherboard-bounded-merged-candidate.kicad_pcb'
assert json.loads((base.parent/'adoption.json').read_text())['adopted']
local=ROOT/'reports/motherboard-local-ground-ties-20261001/source26-r69-r01'
for name in('receipt.json','independent-native-cut-proof.json','combined-bypass-proof.json'):
 r=json.loads((local/name).read_text());assert r['passed']and r['board_sha256']==sha(local/'local-CMOS-ground-ties-candidate.kicad_pcb')
ground=ROOT/'reports/motherboard-return-zoning-20261001/source26-r69-four-source-ground-pieces-r01'
ground_files=list(ground.glob('*.kicad_pcb'));assert len(ground_files)==1
target=base
for donor,scope,revision in[(local/'local-CMOS-ground-ties-candidate.kicad_pcb',local/'bounded-scope.json','source26-CMOS-ground-ties-r70'),(ground_files[0],ground/'bounded-scope.json','source26-four-reference-closures-r71')]:
 out=ROOT/'reports/motherboard-pcb-integration-20261001'/revision
 run=subprocess.run([sys.executable,str(ROOT/'tools/hardware_merge_bounded_pcb_delta.py'),'--before',str(base),'--donor',str(donor),'--target',str(target),'--scope',str(scope),'--out',str(out)],capture_output=True,text=True)
 (out/'merge-command.txt').write_text(run.stdout+run.stderr)
 if run.returncode:raise ValueError(run.stdout[-1000:]+run.stderr[-2000:])
 target=out/'motherboard-bounded-merged-candidate.kicad_pcb'
 native=json.loads((out/'drc.json').read_text());assert not native['ignored_checks']and all(v['severity']=='warning'for v in native['violations'])
 write(out/'baseline-disposition.json',dict(board_sha256=sha(target),routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=native['violations'],ignored_checks=[]))
 print(revision,sha(target),len(native['violations']),flush=True)
