"""Bind the completed local candidate to its exact unsuppressed native report."""
import json,hashlib,shutil
from pathlib import Path
root=Path(__file__).resolve().parents[2]
p=Path(__file__).parent/'source26-r73-typed-retry-r01'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
read=lambda p:json.loads(p.read_text())
r=read(p/'receipt.json');board=p/'owned-bypass-loop-candidate.kicad_pcb'
assert r['board_sha256']==sha(board) and not r['new_route_DRC_defects']
assert r['all_prior_native_source_pad_clusters_preserved'] and r['all_retained_native_copper_and_lands_pin_nets_preserved']
native=read(p/'routed-2.json')
assert native['violations']==r['known_unresolved_native_warnings_retained']
assert not native['ignored_checks'] and all(v['severity']=='warning'for v in native['violations'])
shutil.copyfile(p/'routed-2.json',p/'drc.json')
(p/'baseline-disposition.json').write_text(json.dumps(dict(board_sha256=sha(board),routing_incomplete=True,manufacturing_ready=False,known_unresolved_native_warnings=native['violations'],ignored_checks=[]),indent=2)+'\n')
old=root/'reports/motherboard-owned-bypass-routing-20261001/source26-r56-first-batch-r04/receipt.json'
kept=[g for g in read(old)['owned_loops']if g['retained']]+[g for g in r['owned_loops']if g['retained']]
assert len({g['ref']for g in kept})==len(kept)==97
(p/'combined97-bypass-manifest.json').write_text(json.dumps(dict(owned_loops=kept,actual_filled_supply_branch_return_reviews=[],source_receipts_sha256={str(old):sha(old),str(p/'receipt.json'):sha(p/'receipt.json')},board_sha256=sha(board),manufacturing_ready=False),indent=2)+'\n')
print(dict(candidate_native_bound=True,loops_to_recheck=len(kept),board_sha256=sha(board)))
