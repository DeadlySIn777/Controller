"""Bind the independently checked additive health-supply delta to merger schema."""
from pathlib import Path
import json,hashlib
p=Path('reports/motherboard-power-entry-20261001/health-supply-r99')
scope=json.loads((p/'bounded-scope.json').read_text())
assert scope['electrical_source_unchanged']and not scope['reviewed_footprint_references']and len(scope['reviewed_copper_delta_UUIDs'])==218 and not scope['reviewed_added_zone_UUIDs']
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
assert sha(p/'motor-health-supply-candidate.kicad_pcb')=='a220e48cce4688c6bd7af6c680abda2b5c5537dd511beb119bf9bdd88969bd50'
scope['reviewed_scope_reason']='Exact 218 additive CORE5/FIELD5 health-supply and bias copper objects, with actual source endpoints and four local bypass cut proofs. No old copper, poses, lands, source fields or zones change; current combined proofs still required.'
scope['original_scope_sha256']=sha(p/'bounded-scope.json')
out=Path(__file__).parent/'health-r91-bounded-scope.json';assert not out.exists();out.write_text(json.dumps(scope,indent=2))
