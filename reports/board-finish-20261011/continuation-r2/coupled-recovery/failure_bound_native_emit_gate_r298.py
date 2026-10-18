"""Identity-bound R155/R368 diagnostic gate; never a reference acceptance gate."""
import json,hashlib
from pathlib import Path
AUDIT_SHA='e4a9373b5816de6926cc3b3cea82d1751e5db6cb70d9f150443dff577afff29e'
IDENTITY_SHA='cc0aa7aa4328d2cdf0a071d1c987c94c910a0850f4bafb094ec492c0e93866e7'
MODEL_SHA='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
BASE_SHA='a39e7784abf8969b7f68176555b2c37b5227981cbc615c4bd542205e410373ad'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def pinned(m,key):
 p=Path(m[key+'_file']);assert sha(p)==m[key+'_sha256'];return p
def validate(m,model,audit,failure):
 assert m['schema']=='known-failed-reference-current-native-diagnostic-manifest-r298'
 assert sha(model)==MODEL_SHA and sha(audit)==AUDIT_SHA
 identity=pinned(m,'current_physical_identity');assert sha(identity)==IDENTITY_SHA
 i=read(identity);a=read(audit);f=read(failure)
 assert i['model_sha256']==MODEL_SHA and i['base_model_sha256']==BASE_SHA==a['current_model_SHA256']
 for k in ('all_g_h_and_actual_filled_candidate_records_exact','every_physical_q_WKB_and_profile_exact','all_other_intended_q_WKB_exact','only_binding_changes_exact_one_role_hash_and_explicit_native_intent_receipt','CORE_ROOT42_source_current_native_all_failed_or_open_flags_not_changed'):assert i[k]is True
 assert i['only_changed_role']=='zone_outline_shape' and i['one_changed_proposal_UUID']=='47888e35-9a96-5393-b579-7c0b4a64ec93'
 assert i['intended_only_exact_own_drill_void_added_mm2']==0.07067875376800178
 assert a['verdict']=='SPARSE_COMBINED_INCREMENTAL_PHYSICAL_SOURCE_OLDREF_REPAIR_REQUIRED'
 assert a['all_net_count']==78 and a['old_relationship_loss_count']==0 and a['direct_contact_losses']==[] and a['all_nine_prior_source_loss_count']==0
 assert a['new_true_copper_checks']==1271 and all(r['native_PASS']is True for r in a['new_true_copper_errors']+a['explicit_R7_extra_planner_failures']+a['inherited_margin_deficits'])
 refs=pinned(m,'raw_strict_old_reference_ledger');rr=read(refs);losses=[r for bank in rr for r in bank['strict_ZERO_retained_old_reference_losses']]
 assert len(losses)==a['strict_ZERO_old_reference_losses']==28
 assert f['raw_R368_strict_old_reference_rows']==rr and f['strict_old_reference_gate_pass']is False
 assert f['raw_R368_new_true_copper_planner_errors']==a['new_true_copper_errors'] and f['raw_R368_explicit_R7_extra_planner_failures']==a['explicit_R7_extra_planner_failures'] and f['raw_R368_inherited_margin_deficits']==a['inherited_margin_deficits']
 assert f['raw_R368_all_new_SBC_body_reference_rows']==a['all_ten_SBC_new_body_reference_rows'] and f['full_new_reference_gate_pass']is False
 newbad=[r for r in a['all_ten_SBC_new_body_reference_rows']if not r['gap_empty']];assert len(newbad)==1 and newbad[0]['UUID']=='e970af2a-6700-5e45-ba56-d7ae7fa1b5d8'
 gap=pinned(m,'raw_R7_new_reference_gap');assert sha(gap)==newbad[0]['gap_sha256']=='b72938fa404ed7b8744fdad120abd0317180d0d4770897e39a95d42c9317cde7'
 assert f['inherited_CORE_full_body_reference_gap_mm2']==a['inherited_CORE_reference_gap_mm2']==93.04195929171794
 assert f['overall_reference_acceptance']=='FAIL' and f['overall_production_acceptance']=='FAIL_OPEN' and f['native_fullfill_all_baselines_DRC_current_extracted_SI']=='MANDATORY_OPEN'
 assert m['fresh_actual_incremental_contact_source_native_effective_Cu_gate_pass']is True and m['strict_old_reference_gate_pass']is False and m['full_new_reference_gate_pass']is False
 assert 'fresh_actual_incremental_contact_source_strict_old_reference_native_effective_Cu_gate_pass'not in m
 assert m['all_current_sparse_operations_authorized_and_bound']is True and m['all_failed_or_open_current_native_reference_production_gates_recorded']is True
 assert m['known_failed_reference_diagnostic_explicitly_authorized']is True
 return {'schema':m['schema'],'physical_audit_receipt_file':str(audit),'physical_audit_receipt_sha256':AUDIT_SHA,'current_physical_identity_file':str(identity),'current_physical_identity_sha256':IDENTITY_SHA,'actual_physical_audited_model_sha256':BASE_SHA,'emitted_model_sha256':MODEL_SHA,'only_native_intended_own_drill_identity_delta':True,'all78_old_contacts_direct_nine_source_roots_native_effective_Cu_pass':True,'strict_old_reference_gate_pass':False,'strict_old_reference_failure_count':28,'raw_strict_old_reference_ledger_file':str(refs),'raw_strict_old_reference_ledger_sha256':sha(refs),'new_R7_full_body_reference_gate_pass':False,'raw_R7_new_gap_file':str(gap),'raw_R7_new_gap_sha256':sha(gap),'all_full_production_gates_false_or_open':True,'native_measurement_only_no_adoption':True}
