"""Assemble bounded proposed routing against the separately reviewed cleanup.

This is a trial only. Adoption requires full unchanged return/power guards on
the combined native board and an independent literal-cleanup proof.
"""
from pathlib import Path
import sys,json,hashlib,subprocess
p=Path(__file__).parent;donor=p/'actual-source26-root83-In2-batch-r12';target=p/'IO3-literal-unused-tip-cleanup-r01';base=Path('reports/motherboard-pcb-integration-20261001/source26-reference-closure-and-spurs-r83/motherboard-bounded-merged-candidate.kicad_pcb')
plan=json.loads((donor/'proposed-groups.json').read_text());ids=sorted(u for g in plan['groups']for u in g['new_copper_UUIDs']);assert len(ids)==len(set(ids))==65
sha=lambda path:hashlib.sha256(path.read_bytes()).hexdigest()
scope=p/'seven-path-combined-trial-r15-scope.json';assert not scope.exists()
scope.write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=ids,reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Exact65 proposed Cu on seven already source-checked ordinary SOURCE-pair paths; assemble only for full combined native review against the separate literal IO3-tip cleanup. The donor was NOT accepted against old ROOT83 because its relative power contour failed. No exception to the routing guard or manufacturing acceptance is granted by this assembly.',review_evidence_sha256={str(donor/'proposed-groups.json'):sha(donor/'proposed-groups.json'),str(donor/'native.json'):sha(donor/'native.json'),str(donor/'independent-connectivity/review.json'):sha(donor/'independent-connectivity/review.json'),str(target/'proposal.json'):sha(target/'proposal.json')},adoption_pending=True),indent=2))
out=Path('reports/motherboard-pcb-integration-20261001/source26-seven-path-IO3-tip-trial-r85')
cmd=['C:/Program Files/KiCad/10.0/bin/python.exe','tools/hardware_merge_bounded_pcb_delta.py','--before',str(base),'--donor',str(donor/'motherboard-ordinary-In2-batch-candidate.kicad_pcb'),'--target',str(target/'motherboard-IO3-literal-tip-cleanup-candidate.kicad_pcb'),'--scope',str(scope),'--out',str(out)]
with(p/'seven-path-combined-trial-r15-merge-command.txt').open('w')as log:r=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)
print(json.dumps(dict(command_exit=r.returncode,trial_only=True)));sys.exit(r.returncode)
