"""Freeze the literal three-loop Source-preserving additive scope."""
from pathlib import Path
import json,hashlib
D=Path('reports/motherboard-return-zoning-20261001/ROOT93-stationary-bypass-actual-r01')
B=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-C11087-health-merged-r93/motherboard-bounded-merged-candidate.kicad_pcb')
A=D/'owned-bypass-loop-candidate.kicad_pcb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
r=json.loads((D/'receipt.json').read_text())
groups=[x for x in r['owned_loops']if x['retained']]
assert {x['ref']for x in groups}=={'C19033','C13017','C15004'}
ids=[u for x in groups for u in x['new_UUIDs']]
assert len(ids)==len(set(ids))==18
scope=dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=ids,
  reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Three exact stationary Source723 low-current receiving bypass loops;18newCu only, with actual own-reference annuli/stitches, allSource/pads/poses/Cu/zones preserved. No field/power/FPGA/BankA-B pose or Source change. Full baseline/current/source/reference/power/cut proofs mandatory; notmanufacturingready.')
(D/'bounded-scope.json').write_text(json.dumps(scope,indent=2)+'\n')
old=Path('reports/motherboard-return-zoning-20261001/C11087-moved-bypass-ground-transfer-r01/combined100-retained-plus1-replacement-manifest.json')
c=json.loads(old.read_text())
assert len(c['owned_loops'])==101
assert not({x['ref']for x in c['owned_loops']}&{x['ref']for x in groups})
c['owned_loops'].extend(groups)
c['board_sha256']=sha(A)
c['three_stationary_receivers_added']=dict(base_current101_manifest=str(old),base_current101_manifest_sha256=sha(old),actual_groups=groups,
  current104_fullproof_required=True,health4_not_included=True,high_current_or_measurement_claim=False)
(D/'combined-current104-bypass-manifest.json').write_text(json.dumps(c,indent=2)+'\n')
(D/'literal-delta-binding.json').write_text(json.dumps(dict(before_board=str(B),before_board_sha256=sha(B),board=str(A),board_sha256=sha(A),added_copper_UUIDs=ids,scope_sha256=sha(D/'bounded-scope.json')),indent=2)+'\n')
print(json.dumps(dict(passed=True,added_Cu=18,before_sha256=sha(B),board_sha256=sha(A))))
