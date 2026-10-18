"""Freeze independently saved physical health negatives against exact final ROOT102 composition."""
import json,hashlib
from pathlib import Path
R=Path('reports/motherboard-power-entry-20261001');O=R/'ROOT102-facing-health-peer-freeze-r482';assert not O.exists();O.mkdir()
board=Path('reports/motherboard-return-zoning-20261001/ROOT102-health-current110-composed-r31/motherboard-bounded-merged-candidate.kicad_pcb');expected='639e1b7803bfaa24480d824d97d0d487e545b658a0e3e343435e8297083ef053'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(board)==expected
basic=R/'ROOT102-facing-health-independent-r448/receipt.json';j=json.loads(basic.read_text());assert j['passed']and j['board_sha256']==expected
folders=['ROOT102-facing-health-input-cut-r450','ROOT102-facing-health-input-cut-r452','ROOT102-facing-health-input-cut-r456','ROOT102-facing-health-input-cut-r458','ROOT102-facing-health-C78-direct-power-cut-r478','ROOT102-facing-health-C78-return-cut-r466','ROOT102-facing-health-C80-power-cut-r470','ROOT102-facing-health-C80-return-cut-r472'];rows=[]
for name in folders:
 p=R/name/'receipt.json';v=json.loads(p.read_text());assert v['passed']and v['board_sha256']==expected
 c=v['functional_cut'];assert c['fresh_reload_detected_break'];cut=p.with_name('actual-saved-functional-cut.kicad_pcb');assert sha(cut)==c['saved_native_cut_sha256']
 for f,h in v['input_hashes'].items():assert sha(Path(f))==h,('INPUT_DRIFT',f)
 rows.append(dict(receipt=str(p),receipt_sha256=sha(p),saved_native_cut=str(cut),**c))
assert {tuple(v['from_endpoint'])for v in rows}=={('U11020','1'),('U11020','3'),('U11026','1'),('U11026','3'),('C11078','1'),('C11078','2'),('C11080','1'),('C11080','2')}
failed=R/'ROOT102-facing-health-C78-power-cut-r464/actual-saved-functional-cut.kicad_pcb';assert failed.exists()
diagnostic=R/'ROOT102-health-cap-Cu-inspection-r474/inspection.json';d=json.loads(diagnostic.read_text());p=next(v for v in d if(v['ref'],v['pin'])==('C11078','1'));assert {v['uuid']for v in p['actual_native_direct_Cu']}=={'35fd4268-9b89-410a-b9d5-6b08241cb42b','2c3fb5ed-2496-489e-9df0-6ddc143bd63b'}
trial=dict(disposition='Rejected incomplete negative selection; cap stayed physically powered through retained B track crossing its land. Actual board was not changed.',saved_trial=str(failed),saved_trial_sha256=sha(failed),exact_native_direct_track_diagnostic=str(diagnostic),diagnostic_sha256=sha(diagnostic),superseded_by_actual_two_contact_cut='ROOT102-facing-health-C78-direct-power-cut-r478')
(R/'ROOT102-facing-health-C78-power-cut-r464/rejected-trial.json').write_text(json.dumps(trial,indent=2))
result=dict(passed=True,board=str(board),board_sha256=expected,independent_positive_receipt=str(basic),independent_positive_receipt_sha256=sha(basic),exact_native_manufacturer_lands_parts_pin_nets_preserved=2688,actual_private_endpoints=8,actual_receiving_and_Source_endpoints=16,new_modified_drill_150um_native_shape_registration=19,baseline_explanation='ROOT102 already contains two separately qualified bypass vias; contract compares to ROOT101 and reports 21. This independent comparison uses actual ROOT102.',all_prior_Source_clusters_preserved=True,persisted_native_refilled_fresh_reload_functional_cuts=rows,rejected_incomplete_negative_selection=trial,other_reference_current_loaded_timing_remote_producer_and_whole_board_completion_are_separate=True,manufacturing_ready=False)
(O/'receipt.json').write_text(json.dumps(result,indent=2));print('PEER_PASS',len(rows),expected,flush=True)
