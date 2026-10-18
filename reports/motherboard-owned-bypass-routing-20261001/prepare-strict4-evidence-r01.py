"""Bind four actual direct supply branches; previous97 guards stay unchanged."""
import json,hashlib,shutil
from pathlib import Path
ROOT=Path(__file__).resolve().parents[2]
p=Path(__file__).parent/'source26-r76-strict-same-side-r01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
r=read(p/'receipt.json');board=p/'owned-bypass-loop-candidate.kicad_pcb'
assert r['board_sha256']==sha(board) and not r['new_route_DRC_defects']
assert r['all_prior_native_source_pad_clusters_preserved'] and r['all_retained_native_copper_and_lands_pin_nets_preserved']
assert read(p/'independent-native-cut-proof.json')['passed']
native=read(p/'routed-0.json')
assert native['violations']==r['known_unresolved_native_warnings_retained']
assert not native['ignored_checks'] and all(v['severity']=='warning'for v in native['violations'])
assert not(p/'drc.json').exists()
shutil.copyfile(p/'routed-0.json',p/'drc.json')
old=ROOT/'reports/motherboard-owned-bypass-routing-20261001/source26-r73-typed-retry-r01/combined97-bypass-manifest.json'
new=[g for g in r['owned_loops']if g['retained']]
kept=read(old)['owned_loops']+new
assert len({g['ref']for g in kept})==len(kept)==101
ids=[u for g in new for u in g['new_UUIDs']]
assert len(ids)==len(set(ids))==9
evidence={str(q):sha(q)for q in [old,p/'receipt.json',p/'independent-native-cut-proof.json',p/'drc.json']}
(p/'combined101-bypass-manifest.json').write_text(json.dumps(dict(owned_loops=kept,actual_filled_supply_branch_return_reviews=[],source_receipts_sha256=evidence,board_sha256=sha(board),manufacturing_ready=False),indent=2)+'\n')
(p/'bounded-scope.json').write_text(json.dumps(dict(electrical_source_unchanged=True,reviewed_footprint_references=[],reviewed_copper_delta_UUIDs=ids,reviewed_added_zone_UUIDs=[],reviewed_scope_reason='Four complete local supply branches, nine literal surface conductors; same-side no supply vias. Original both-reference ground/receiving guards and exact native DRC retained. Four actual owner-loop positive and real copper-cut negative controls passed. No source, pose, land, old copper or zone-outline change.',review_evidence_sha256=evidence),indent=2)+'\n')
print(dict(passed=True,actual_new_loops=4,actual_added_Cu=9,all_loops_to_recheck=101))
