from pathlib import Path
import json,sys,subprocess
ROOT=Path(__file__).resolve().parents[2]
P=ROOT/'reports/motherboard-pcb-integration-20261001/source26-C17014-ground-r68'
old=json.loads((ROOT/'reports/motherboard-pcb-integration-20261001/source26-orphan-free-adopted-r62/bounded-C17014-retrial-scope.json').read_text())
old['reviewed_scope_reason']='Restore only five literal C17014 local bypass objects after the exact field-ground In1-to-In3 transfer clears its actual LOGIC return corridor. Actual final94-loop/native/SOURCE proofs required; no source, old Cu, poses or zones altered here.'
(P/'bounded-C17014-restore-scope-r02.json').write_text(json.dumps(old,indent=2)+'\n')
cmd=[sys.executable,str(ROOT/'tools/hardware_merge_bounded_pcb_delta.py'),
 '--before',str(ROOT/'reports/motherboard-pcb-integration-20261001/source26-orphan-free-adopted-r62/motherboard-source26-WIP.kicad_pcb'),
 '--donor',str(ROOT/'reports/motherboard-pcb-integration-20261001/source26-C17014-retrial-r63/motherboard-bounded-merged-candidate.kicad_pcb'),
 '--target',str(P/'motherboard-bounded-merged-candidate.kicad_pcb'),
 '--scope',str(P/'bounded-C17014-restore-scope-r02.json'),
 '--out',str(ROOT/'reports/motherboard-pcb-integration-20261001/source26-C17014-bypass-r69')]
run=subprocess.run(cmd,capture_output=True,text=True);(P/'C17014-restore-command.txt').write_text(run.stdout+run.stderr);print(run.stdout+run.stderr);raise SystemExit(run.returncode)
