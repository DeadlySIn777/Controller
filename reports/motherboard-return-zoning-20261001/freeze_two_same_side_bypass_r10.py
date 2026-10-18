"""Freeze the native-qualified two-capacitor donor without promoting PCB release."""
from pathlib import Path
import json,hashlib
p=Path('reports/motherboard-return-zoning-20261001/ROOT101-two-same-side-bypass-restored-r06')
sha=lambda q:hashlib.sha256(q.read_bytes()).hexdigest()
read=lambda n:json.loads((p/n).read_text())
board=p/'motherboard-two-same-side-bypass-candidate.kicad_pcb';h=sha(board)
assert h=='769541d11876ea0050240ec065f6b0b85bff19c7c8324f1c26b9b637212a8af5'
assert not(p/'freeze-receipt.json').exists()
proofs=['receipt.json','combined108-proof.json','current-full-delta-power-proof.json','literal-reference-resources.json','retained-FPGA38-rule-proof.json','combined-C19042-proof.json','combined-C14804-proof.json','current82-motor-reference-proof.json','current-retained-reference-bridges.json','new-drill-SMD-land-review.json','combined-ordinary-proof/review.json','combined-critical-proof/review.json','combined-AO1-verification/review.json','retained-MISO-and-seven-proof/review.json','current-four-pair-proof/review.json']
for name in proofs:
 v=read(name);assert v['passed']and v['board_sha256']==h,name
bypass=read('combined108-proof.json');assert bypass['retained_local_loops_checked']==108 and len(bypass['actual_receiving_return_anchor_reviews'])==221
resource=read('literal-reference-resources.json');assert resource['filled_component_count']==188 and not resource['unanchored_components']and not resource['derived_nonphysical_computation_artifacts']
co=read('independent-connectivity/review.json');assert co['source_net_checks_pass']and co['complete_source_population_pass']and not co['errors']and not co['orphan_copper_items']
assert co['uncapped_unconnected_ratsnest_edges']==co['independent_physical_cluster_missing_joins']==3524
commands=read('native-check-command-results.json');assert commands['all_commands_completed']and commands['exact_inputs_unchanged']
assert len(commands['results'])==14 and all(x['returncode']==0 for x in commands['results'])
assert not read('drc.json')['violations']and not read('drc.json')['ignored_checks']
health=read('current-health20-proof/receipt.json');assert health['source_board_sha256']==h and all(x['passed']for x in health['actual_endpoint_checks'])
raw=read('current-RAW3-proof/receipt.json');assert raw['board_sha256']==h and raw['source_EP_VIN_VBIAS_cap_native_continuity']and raw['all_three_original_power_transitions_preserved']
cuts=[]
for ref in('C13006','C13007'):
 for case in('VCC_branch','cap_return_branch','Ground_barrel'):
  stem=f'actual-cut-{ref}-{case}';v=read(stem+'.fresh-review.json');m=read(stem+'.mutation.json')
  assert v['passed']and v['fresh_native_reload']and v['all_actual_owner_Source_endpoints_disconnected']
  assert sha(p/(stem+'.kicad_pcb'))==v['board_sha256']==m['board_sha256']and m['native_zones_refilled']
  cuts.append(dict(ref=ref,case=case,review=stem+'.fresh-review.json',sha256=sha(p/(stem+'.fresh-review.json'))))
for name in('current-health20-proof/receipt.json','current-RAW3-proof/receipt.json','independent-connectivity/review.json','native-check-command-results.json','drc.json','bounded-scope.json','current108-bypass-manifest.json'):proofs.append(name)
result=dict(passed=True,scope='Two exact existing Source26 capacitor poses and six added conductors; native-qualified donor, not adopted motherboard or manufacturing release',board=str(board),board_sha256=h,baseline_sha256=read('receipt.json')['baseline_sha256'],exact_changed_poses=['C13006','C13007'],exact_added_copper_UUIDs=read('receipt.json')['exact_added_Cu'],all5903_ROOT101_prior_Source_clusters_preserved=read('receipt.json')['prior_Source_clusters']['passed'],retained_prior_bypass_groups=106,total_verified_bypass_groups=108,actual_receiving_return_endpoints=221,actual_Source_anchored_reference_components=188,native_errors=0,native_warnings=0,ignored_checks=[],native_missing_joins=3524,independent_missing_joins=3524,orphan_copper=0,six_refilled_and_freshly_reloaded_actual_cut_negatives=cuts,new_drills_clear_fitted_SMD_lands=True,relative_IO3_CORE_power_guard_passed=True,source_or_old_Cu_or_zone_definitions_changed=False,evidence_sha256={n:sha(p/n)for n in proofs},physical_load_or_SI_qualification=False,manufacturing_ready=False)
(p/'freeze-receipt.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps(dict(passed=True,missing_joins=3524,bypass_groups=108,actual_cut_controls=6)))
