"""Freeze the actual R155 diagnostic authority, including every R368 failure."""
from pathlib import Path
import json,hashlib
import failure_bound_native_emit_gate_r298 as G
H=Path(__file__).resolve().parent;P=H.parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(p):return json.loads(Path(p).read_bytes())
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
out=H/'R155-known-failed-reference-diagnostic-manifest-r304';assert not out.exists();out.mkdir()
audit=P/'field-power/REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368/receipt.json';assert sha(audit)==G.AUDIT_SHA;a=read(audit)
identity=P/'R5051-own-drill-intended-only-current-R364-rebase-r155/receipt.json';assert sha(identity)==G.IDENTITY_SHA;i=read(identity)
model=Path(i['model_file']);assert sha(model)==G.MODEL_SHA
profiles=H/'R155-final-native-profile-authority-r296/receipt.json';assert sha(profiles)=='531fdcd7c8d8316e8cf15966dc2ed522e7a339acc8a74447532d7e2f166c15a6';p=read(profiles);assert p['current_model_sha256']==G.MODEL_SHA and p['unbound_profile_fields']==[]
inventory=H/'R155-final-current-native-inventory-r290/receipt.json';assert sha(inventory)=='35331c77acc28f584597d9eda82df66ee43b5b0e3dd86d395aabaf6e6ef4ef75';ir=read(inventory);assert ir['current_model_sha256']==G.MODEL_SHA and ir['unbound_original_difference_count']==0
packet=H/'DIC-C1022-one-R250-joint-native-integration-delta-r260/receipt.json';assert sha(packet)=='d9f59729bbed206b01a562bff0d7096341ba89507cca8df2d46395ff03eed0e7';d=read(packet)
oldfailure=Path(d['unresolved_inherited_production_gates_file']);assert sha(oldfailure)==d['unresolved_inherited_production_gates_sha256']
rawrefs=audit.parent/'three-bank-strict-zero-reference-rows.json';rows=read(rawrefs)
failure={'schema':'actual-R155-inherited-and-new-production-failures-r304','physical_audit_receipt_file':str(audit),'physical_audit_receipt_sha256':sha(audit),'physical_audited_model_sha256':G.BASE_SHA,'emitted_current_model_sha256':G.MODEL_SHA,'physical_identity_receipt_file':str(identity),'physical_identity_receipt_sha256':sha(identity),'previous_frozen_CORE_ROOT42_and_production_failure_ledger_file':str(oldfailure),'previous_frozen_CORE_ROOT42_and_production_failure_ledger_sha256':sha(oldfailure),'previous_frozen_CORE_ROOT42_and_production_failure_ledger_UNCHANGED':read(oldfailure),'strict_old_reference_gate_pass':False,'strict_old_reference_loss_count':28,'new_R7_raw_reference_failure_preserved':True,'all_raw_old_and_new_reference_planner_CORE_current_ROOT42_native_failures_preserved':True,'full_new_reference_gate_pass':False,'raw_R368_strict_old_reference_rows':rows,'raw_R368_new_true_copper_planner_errors':a['new_true_copper_errors'],'raw_R368_explicit_R7_extra_planner_failures':a['explicit_R7_extra_planner_failures'],'raw_R368_inherited_margin_deficits':a['inherited_margin_deficits'],'raw_R368_all_new_SBC_body_reference_rows':a['all_ten_SBC_new_body_reference_rows'],'inherited_CORE_full_body_reference_gap_mm2':a['inherited_CORE_reference_gap_mm2'],'overall_reference_acceptance':'FAIL','overall_production_acceptance':'FAIL_OPEN','native_fullfill_all_baselines_DRC_current_extracted_SI':'MANDATORY_OPEN','actual_native_old_masks_plus_new187In3_and_f6In4':'MANDATORY_OPEN; original serialization/flags retained','every99newordinaryvia_actual_all6_native_flash_and_source_reference_contact':'MANDATORY_OPEN','source_schematic_project_rule_canonical_allCu_allFP_API':'MANDATORY_OPEN','native_ordinary_rule_vs_planner_margin_gate_separation':'NATIVE_EFFECTIVE_HOST_PASS; all extra planner FAIL rows unchanged above; full native DRC OPEN','U10003_R153_not_composed':True,'manufacturing_ready':False,'adopted':False,'native_jobs':0}
failurefile=out/'full-raw-failure-ledger.json';put(failurefile,failure)
files={}
def pin(file,expected=None):
 file=Path(file).resolve();s=sha(file);assert expected is None or s==expected;files[str(file)]=s
for file in (audit,identity,profiles,inventory,packet,oldfailure,Path(ir['diff_file']),H/'emit_known_failed_reference_native_recipe_r298.py',H/'failure_bound_native_emit_gate_r298.py',P/'field-power/restore_field_current_mixed_precision_states_r366.py',P/'sbc-power/emit_complete_power_recipe_r114.py',P/'native_owned_root_pose_contract_r3.py',P/'two-rotated-FP-native-collector-contract-r87/frozen-rotation-rows.json'):pin(file)
for file in sorted(audit.parent.glob('*.json')):pin(file)
for file in sorted(audit.parent.glob('*.wkb')):pin(file)
for row in p['owned_zone_native_profile_completion_rows']:
 pin(row['authorizing_receipt_file'],row['authorizing_receipt_sha256'])
 for authority in row['exact_source_authorities']:
  if 'file'in authority:pin(authority['file'],authority['sha256'])
  else:pin(authority['model_file'],authority['model_sha256'])
for file,s in ir['owner_packet_pins'].items():pin(file,s)
for row in d['add_rows']:
 pin(row['chunk_path'],row['chunk_sha256']);pin(row['authorizing_packet_file'],row['authorizing_packet_sha256'])
for key,v in read(oldfailure).items():
 if key.endswith('_file')and key[:-5]+'_sha256'in read(oldfailure):pin(v,read(oldfailure)[key[:-5]+'_sha256'])
m={'schema':'known-failed-reference-current-native-diagnostic-manifest-r298','exploratory_diagnostic_only':True,'adopted':False,'manufacturing_ready':False,'current_model_file':str(model),'current_model_sha256':G.MODEL_SHA,'incremental_current_audit_file':str(audit),'incremental_current_audit_sha256':sha(audit),'current_physical_identity_file':str(identity),'current_physical_identity_sha256':sha(identity),'raw_strict_old_reference_ledger_file':str(rawrefs),'raw_strict_old_reference_ledger_sha256':sha(rawrefs),'raw_R7_new_reference_gap_file':str(audit.parent/'e970af2a-6700-5e45-ba56-d7ae7fa1b5d8-SBC-new-full-body-reference-gap.wkb'),'raw_R7_new_reference_gap_sha256':'b72938fa404ed7b8744fdad120abd0317180d0d4770897e39a95d42c9317cde7','production_failure_ledger_file':str(failurefile),'production_failure_ledger_sha256':sha(failurefile),'complete_inventory_receipt_file':str(inventory),'complete_inventory_receipt_sha256':sha(inventory),'frozen_read_set':[{'file':k,'sha256':v}for k,v in sorted(files.items())],'fresh_actual_incremental_contact_source_native_effective_Cu_gate_pass':True,'strict_old_reference_gate_pass':False,'full_new_reference_gate_pass':False,'known_failed_reference_diagnostic_explicitly_authorized':True,'authorization_origin':'ROOT message 2026-10-12 explicitly authorizes failure-bound native diagnostic of exact R155 with full raw R368 28-reference failures, no adoption or production gates flipped','all_current_sparse_operations_authorized_and_bound':True,'all_failed_or_open_current_native_reference_production_gates_recorded':True,'generated_precision_profile':'LITERAL_ZERO_ED_D8_PHYSICAL_AND_NM_ALL_OTHER_ROLES_R366','generated_precision_adapter_sha256':'54a006c5785b2756ccabf92f20bb0bec47f355c8e753c5f94dd7b411e57a8121','parent_native_board_file':d['parent_native_board_file'],'parent_native_board_sha256':d['parent_native_board_sha256'],'fresh_source_file':str(P/'field-power/combined-power-source-r3-hierarchy/source-export/fresh.net'),'fresh_source_sha256':'070444b08e9225319d80e54a7e23a841218d5bb32e38a10c3739052e3197e7b2','owned_zone_native_profile_completion_rows':p['owned_zone_native_profile_completion_rows'],'frozen_new_discrete_addition_rows':d['add_rows']}
G.validate(m,model,audit,failurefile)
manifest=out/'immutable-diagnostic-manifest.json';put(manifest,m)
print(json.dumps({'manifest_file':str(manifest),'manifest_sha256':sha(manifest),'failure_ledger_sha256':sha(failurefile),'frozen_read_set_count':len(files),'strict_old_reference_gate_pass':False,'new_R7_reference_gap_mm2':0.03141874628400019}),flush=True)
