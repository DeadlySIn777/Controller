"""Bind the nine independent native route proofs to their literal 56 Cu IDs."""
import json,hashlib
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=ROOT/'reports/motherboard-ordinary-routing-20261001/actual-source26-root71-local-clipped-r02'
review=json.loads((p/'review.json').read_text());ledger=json.loads((p/'proposed-local-groups.json').read_text())
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert review['passed']and review['board_sha256']==sha(p/'motherboard-ordinary-local-candidate.kicad_pcb')
assert len(ledger['groups'])==9 and len(ledger['added_copper_UUIDs'])==56
assert set(ledger['added_copper_UUIDs'])=={u for g in review['actual_SOURCE_endpoint_positive_checks']for u in g['new_copper_UUIDs']}
scope=dict(electrical_source_unchanged=True,reviewed_scope_reason='Nine independently SOURCE-connected ordinary-logic endpoint pairs. Exact existing source, lands, poses, old Cu and zones retained. Full own-return reference guard and actual copper-cut negative controls passed on donor; repeat on combined board.',reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=ledger['added_copper_UUIDs'],reviewed_added_zone_UUIDs=[],review_evidence_sha256={str(p/n):sha(p/n)for n in('review.json','proposed-local-groups.json','manifest.json')})
dest=Path(__file__).parent/'source26-ordinary9-bounded-scope-r75.json';assert not dest.exists()
dest.write_text(json.dumps(scope,indent=2)+'\n')
print(dict(exact_copper_items=len(scope['reviewed_copper_delta_UUIDs']),source_unchanged=True))
