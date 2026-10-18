"""Compose immutable final local positives and independent physical negative controls."""
from pathlib import Path
import hashlib,json
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
R=Path('reports/motherboard-return-zoning-20261001')
D=R/'ROOT102-health-current110-composed-r31'
P=D/'local-positive-freeze-r01.json'
Q=Path('reports/motherboard-power-entry-20261001/ROOT102-facing-health-peer-freeze-r482/receipt.json')
S=D/'registration-scope-reconciliation-r01.json'
a=json.loads(P.read_text());b=json.loads(Q.read_text());s=json.loads(S.read_text())
expected='639e1b7803bfaa24480d824d97d0d487e545b658a0e3e343435e8297083ef053'
assert all(r['passed']and r['board_sha256']==expected for r in(a,b,s))
assert sha(a['board'])==expected
assert b['all_prior_Source_clusters_preserved']and b['exact_native_manufacturer_lands_parts_pin_nets_preserved']==2688
assert s['our_changed_barrels21']==21 and s['peer_health_changed_barrels19']==19 and s['exact_same_health_UUID_set']
assert sha(b['independent_positive_receipt'])==b['independent_positive_receipt_sha256']
cuts=b['persisted_native_refilled_fresh_reload_functional_cuts']
assert len(cuts)==8
expected_pairs={('U11020','1'),('U11020','3'),('U11026','1'),('U11026','3'),('C11078','1'),('C11078','2'),('C11080','1'),('C11080','2')}
assert {tuple(c['from_endpoint'])for c in cuts}==expected_pairs
deps={str(p):sha(p)for p in(P,Q,S,Path(__file__),Path(a['board']))}
for c in cuts:
 assert c['fresh_reload_detected_break']and c['removed_UUIDs']
 cp=Path(c['receipt']);cut=Path(c['saved_native_cut'])
 assert sha(cp)==c['receipt_sha256']and sha(cut)==c['saved_native_cut_sha256']
 cr=json.loads(cp.read_text());assert cr['passed']and cr['board_sha256']==expected
 assert cr['functional_cut']['fresh_reload_detected_break']
 deps[str(cp)]=sha(cp);deps[str(cut)]=sha(cut)
for p,h in a['input_sha256'].items():assert sha(p)==h
rejected=b['rejected_incomplete_negative_selection']
assert sha(rejected['saved_trial'])==rejected['saved_trial_sha256']
assert sha(rejected['exact_native_direct_track_diagnostic'])==rejected['diagnostic_sha256']
out=D/'final-scoped-freeze-r01.json';assert not out.exists()
result=dict(a,scope='Complete bounded ROOT102 health physical/electrical receiving correction. All local positive and eight persisted independent negative checks pass. Parent complete bench/adoption/publication remain separate; Source27/loaded thermal/timing/global assembly/full routing are not qualified.',
 input_sha256={**a['input_sha256'],**deps},local_scoped_complete=True,
 independent_physical_positive_receipt=b['independent_positive_receipt'],independent_peer_freeze=str(Q),
 eight_persisted_native_refilled_fresh_reload_cuts=cuts,persisted_new_health_cut_controls_pending=False,
 exact_registration_19_health_plus2_retained_cap_reconciliation=str(S),
 retained_rejected_incomplete_single_contact_cut=rejected,
 adoption_prerequisite='Parent fresh full bench and explicit adoption on the exact immutable board; no live pointer/publication change by this agent.',
 parent_complete_bench_pending=True,live_pointers_or_CAD_published=False,manufacturing_ready=False)
out.write_text(json.dumps(result,indent=2))
assert all(sha(p)==h for p,h in result['input_sha256'].items())
print(json.dumps(dict(passed=True,scoped_complete=True,board_sha256=expected,receipt_sha256=sha(out),loops=110,returns=225,physical_cut_controls=8)),flush=True)
