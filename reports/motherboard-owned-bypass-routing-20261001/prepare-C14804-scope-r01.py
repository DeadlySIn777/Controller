"""Freeze the exact one-trace, source-preserving C14804 delta."""
from pathlib import Path
import json,hashlib
p=Path(__file__).parent/'source26-r79-adjacent-same-side-r01'
read=lambda q:json.loads(q.read_text());sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
r=read(p/'receipt.json');proof=read(p/'independent-native-cut-proof.json')
assert proof['passed'] and proof['board_sha256']==sha(p/'owned-bypass-loop-candidate.kicad_pcb')
g=[v for v in r['owned_loops']if v['retained']];assert len(g)==1 and g[0]['ref']=='C14804'
scope=dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=g[0]['new_UUIDs'],reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Complete direct F-only C14804 to U14802 local supply branch, exact adjacent In1 Source-reference and real surface/annulus return. Separate verified same-side proof; unchanged old101 guards still independently required. No supply via, pose, old Cu, zone, source or land changes.',review_evidence_sha256={str(q.resolve()):sha(q)for q in(p/'receipt.json',p/'independent-native-cut-proof.json',Path(__file__))})
assert not(p/'bounded-scope.json').exists()
(p/'bounded-scope.json').write_text(json.dumps(scope,indent=2)+'\n')
