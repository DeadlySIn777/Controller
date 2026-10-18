"""Combine exact donor scopes for a trial merge; this does not grant adoption."""
from pathlib import Path
import json,hashlib
base=Path('reports/motherboard-pcb-integration-20261001')
p=base/'source26-motor-bank-A-merge-trial-r88';p.mkdir(exist_ok=False)
paths=[Path('reports/motherboard-power-entry-20261001/motor-bank-A-reference-ready-r141/bounded-scope.json'),Path('reports/motherboard-return-zoning-20261001/motor-bank-A-r138-logic-reference-collars-r06/bounded-scope.json')]
data=[json.loads(v.read_text())for v in paths]
assert all(v['electrical_source_unchanged']for v in data)
keys=['reviewed_footprint_references','reviewed_copper_delta_UUIDs','reviewed_added_zone_UUIDs']
scope={key:sorted({u for row in data for u in row[key]})for key in keys}
assert len(scope[keys[0]])==23 and len(scope[keys[1]])==401 and len(scope[keys[2]])==9
scope.update(electrical_source_unchanged=True,reviewed_scope_reason='Exact combined Bank A receiving-head 23 poses, 331 additive/70 retired Cu and nine Logic collars; all current target outlines retained. Trial pending actual combined power/default/reference qualification and native donor negative controls.',input_sha256={str(v):hashlib.sha256(v.read_bytes()).hexdigest()for v in paths})
(p/'bounded-scope.json').write_text(json.dumps(scope,indent=2))
