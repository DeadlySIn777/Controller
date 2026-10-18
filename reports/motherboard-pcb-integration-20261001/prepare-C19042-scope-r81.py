"""Correct stale explanatory wording; literal reviewed geometry unchanged."""
from pathlib import Path
import json,hashlib
root=Path(__file__).resolve().parents[2]
folder=root/'reports/motherboard-return-zoning-20261001/source26-r74-C19042-coupled-source-cell-r05'
source=folder/'bounded-scope.json';scope=json.loads(source.read_text())
assert scope['reviewed_footprint_references']==['C19042']
assert len(scope['reviewed_copper_delta_UUIDs'])==10 and len(scope['reviewed_added_zone_UUIDs'])==1
assert len(scope['reviewed_existing_zone_outline_deltas'])==1
row=scope['reviewed_existing_zone_outline_deltas'][0]
row['electrical_outline_correction_reason']=row['electrical_outline_correction_reason'].replace('Two Source-preserving capacitor poses','One Source-preserving C19042 capacitor pose')
scope['review_evidence_sha256']={str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in[source,folder/'closure-freeze-r06.json']}
scope['scope_text_correction_only']='Only C19042 moves; C19037 is unchanged. Literal source/geometry/UUID/zone definition hashes remain exactly those independently proved by donor.'
dest=Path(__file__).parent/'source26-C19042-scope-r81.json';assert not dest.exists()
dest.write_text(json.dumps(scope,indent=2)+'\n')
