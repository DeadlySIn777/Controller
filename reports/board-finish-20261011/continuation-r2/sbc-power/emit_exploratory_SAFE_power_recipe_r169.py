"""Measurement-only derivative; all failed production host gates stay false."""
from pathlib import Path
p=Path(__file__).resolve().parent
s=(p/'emit_complete_power_recipe_r114.py').read_text()
s=s.replace("OUT=L.OUT/'complete-power-native-recipe-r114'","OUT=L.OUT/'exploratory-SAFE-power-native-recipe-r169'")
s=s.replace("'EXACT_OWNED_NATIVE_FORMAT_RECIPE_HOST_CONTACT_GATES_RECORDED_NATIVE_ELECTRICAL_PENDING'","'EXPLORATORY_NATIVE_MEASUREMENT_RECIPE_FAILED_PRODUCTION_GATES_PRESERVED'")
needle="    write_json(OUT/'receipt.json',receipt);print('EXACT_COMPLETE_POWER_RECIPE'"
replacement='''    geometry_gate=L.OUT/'SAFE-repaired-independent-true-geometry-r161/receipt.json';assert sha(geometry_gate)=='c69486b72b0391cfd4064368febec14b12e81c47ce4fd2b1484bddcf06f47991'
    geom=json.loads(geometry_gate.read_bytes());assert geom['model_sha256']==sha(model) and geom['verdict']=='PASS_STRICT_TRUE_GEOMETRY_SCOPE'
    ref_gate=L.OUT/'SAFE-strict-source-reference-audit-r151/receipt.json';assert ref_gate.exists();refdata=json.loads(ref_gate.read_bytes());assert refdata['model_sha256']==sha(model)
    root_gate=L.OUT.parent/'SAFE-full-root42-retention-r50/receipt.json';assert sha(root_gate)=='6ee956571dc162306ed1d5bcced1cf8cb05f3c8af1fabd7c672e773a5acbd68c'
    rootdata=json.loads(root_gate.read_bytes());assert rootdata['model_sha256']==sha(model) and rootdata['verdict']=='FAIL_SAFE_FULL76_ROOT42_RETENTION'
    failures={'original198b_power_rows':[{'net':r['net_normalized_for_lookup_only'],'old_group_split_count':len(r['old_group_splits']),'unowned_missing_old_contact_count':len(r['unowned_missing_old_contacts']),'old_Cu_branch_split_count':len(r['old_Cu_union_branch_splits']),'entirely_lost_old_Cu_union_parts':len(r['entirely_lost_old_Cu_union_parts']),'unrooted_named_pad_count':sum(not q['source_connected'] for q in r['all_named_pads']),'all_native_dc936_loss_groups_restored':r['all_native_dc936_loss_groups_restored'],'all_new_polygons_rooted':r['all_new_polygons_rooted']} for r in ar['rows']],'strict_source_reference_verdict':refdata['verdict'],'strict_source_reference_rows':refdata['rows']}
    failures['root42_full76_verdict']=rootdata['verdict']
    failures['root42_full76_rows']=[{'net':r['net'],'before_groups':r['before_groups'],'after_groups':r['after_groups'],'old_discrete_relationship_loss_count':len(r['old_discrete_contact_losses'])} for r in rootdata['all76_zone_bearing_nets']]
    failures['root42_actual_sources']=rootdata['sources']
    failures['root42_full_failure_receipt_file']=str(root_gate.resolve())
    failures['root42_full_failure_receipt_sha256']=sha(root_gate)
    failures['root42_retained_reference_sha256']=rootdata['retained_reference_sha256']
    ff=OUT/'unresolved-production-host-gates.json';write_json(ff,failures)
    receipt.update({'exploratory_measurement_only':True,'production_readiness':False,'board_adoption_authorized':False,'failed_or_open_host_gates_not_waived':True,'actual_original198b_host_relationship_gate':host_retained_pass,'actual_complete_supply_source_gate':host_all_supply_rooted,'unresolved_production_host_gate_ledger_file':str(ff.resolve()),'unresolved_production_host_gate_ledger_sha256':sha(ff),'independent_strict_geometry_receipt_file':str(geometry_gate.resolve()),'independent_strict_geometry_receipt_sha256':sha(geometry_gate),'strict_source_reference_receipt_file':str(ref_gate.resolve()),'strict_source_reference_receipt_sha256':sha(ref_gate),'strict_source_reference_verdict':refdata['verdict'],'original_ordinary_production_emitter_unchanged_file':str((L.OUT/'emit_complete_power_recipe_r114.py').resolve()),'original_ordinary_production_emitter_sha256':sha(L.OUT/'emit_complete_power_recipe_r114.py'),'native_RULE126_and_other_rule_adapters_not_implicitly_adopted':True})
    receipt.update({'root42_full76_retention_receipt_file':str(root_gate.resolve()),'root42_full76_retention_receipt_sha256':sha(root_gate),'root42_full76_retention_verdict':rootdata['verdict'],'root42_full76_host_retention_gate':False})
    write_json(OUT/'receipt.json',receipt);print('EXACT_EXPLORATORY_POWER_RECIPE'
'''
assert needle in s;s=s.replace(needle,replacement)
exec(compile(s,str(p/'emit_complete_power_recipe_r114.py'),'exec'))
