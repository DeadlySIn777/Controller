from pathlib import Path
import json,hashlib
D=Path('reports/motherboard-return-zoning-20261001/ROOT94-health-U25-field-collars-r03')
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=Path('reports/motherboard-pcb-integration-20261001/source26-BankA-health-DI7-merged-r94/motherboard-bounded-merged-candidate.kicad_pcb')
s=json.loads((D/'bounded-scope.json').read_text());s['reviewed_copper_delta_UUIDs']=['9557a691-472b-4af0-87c3-b0e91cf52409','501f396f-2ba8-4dcf-980c-3c37bef08384'];s['reviewed_scope_reason']='Combined exact U11025 receiving health return: two actual Source-backed peer Ground conductors, two native own-field local reference collars, and exact2 existing-field unused positive-triangle DFM outline cuts. No source/land/pad/pose/other Cu/zone change; unchanged physical annulus/Source margin guards, no area waiver.'
(D/'combined-from-ROOT94-bounded-scope.json').write_text(json.dumps(s,indent=2)+'\n')
board=D/'motherboard-health-U25-field-reference-candidate.kicad_pcb';receipt=json.loads((D/'receipt.json').read_text());resource=json.loads((D/'full-native-resource-review.json').read_text());assert resource['passed']and resource['filled_component_count']==188
controls=sorted(D.glob('physical-cut-r04-*.review.json'))+sorted(D.glob('physical-cut-r04-*.fresh-native-review.json'));assert len(controls)==6 and all(json.loads(p.read_text())['passed']for p in controls)
proofs=[D/'receipt.json',D/'actual-one-health-bypass-proof.json',D/'full-native-resource-review.json',D/'all-native-Source-cluster-proof.json',D/'native.json',D/'combined-from-ROOT94-bounded-scope.json',D/'actual-one-health-bypass-manifest.json',D/'domain-map.json']+controls
f=dict(passed=True,before_board=str(base),before_board_sha256=sha(base),board=str(board),board_sha256=sha(board),complete_delta_scope=str(D/'combined-from-ROOT94-bounded-scope.json'),frozen_proof_sha256={str(p):sha(p)for p in proofs},native_errors=0,native_warnings=0,ignored_checks=[],actual_physical_negatives_and_fresh_reload_checks=6,actual_native_resources=188,unanchored_resources=0,synthetic_resources=0,old_Source_pads_clusters_Cu_lands_poses_preserved=True,actual_one_health_supply_and_return_proved=True,independent_inventory_pending=True,full_four_health_loops_or_current_20ms_thermal_qualified=False,manufacturing_ready=False)
(D/'closure-freeze-r01.json').write_text(json.dumps(f,indent=2)+'\n')
print(json.dumps({k:f[k]for k in('passed','before_board_sha256','board_sha256','actual_native_resources')}))
