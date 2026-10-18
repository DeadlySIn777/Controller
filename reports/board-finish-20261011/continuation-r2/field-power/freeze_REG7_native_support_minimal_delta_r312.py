"""Derived R300 packet: corrected supported integer outline, exact local ops."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'freeze_REG7_minimal_current_integration_delta_r300.py').read_text(encoding='utf-8')
s=s.replace("R=H/'REG-local-reference-true-copper-and-state-contract-r292'","R=H/'REG-explicit-local-integer-boundary-reference-repair-r307'")
s=s.replace('REG7-minimal-current-integration-delta-r300','REG7-native-support-minimal-current-delta-r312')
s=s.replace("assert rr['true_Cu_errors']==[] and sha(R/'model.pkl')==rr['model_SHA256']","assert rr['verdict']=='EXPLICIT_NATIVE_INTEGER_BOUNDARY_LOCAL_GUARD_SUPPORT_CONTACT_REF_PASS_NATIVE_OPEN' and sha(R/'model.pkl')==rr['model_SHA256']")
s=s.replace("rr['inherited_full_row_guard_errors_preserved']","json.loads((H/'REG-local-reference-true-copper-and-state-contract-r292/receipt.json').read_text())['inherited_full_row_guard_errors_preserved']")
s=s.replace("'R292_expected_WKB_SHA256'","'R307_expected_WKB_SHA256'")
s=s.replace("prior[role].difference(q[role]).area","set_precision(prior[role],0).difference(set_precision(q[role],0)).area")
s=s.replace("q[role].difference(prior[role]).area","set_precision(q[role],0).difference(set_precision(prior[role],0)).area")
s=s.replace("R214-only-expected-two-role-objects.pkl","current-baseline-exact-only-expected-two-role-objects.pkl")
anchor=" (O/'new-REG7-zones.pkl').write_bytes"
insertion="""
 # The expected native outline has a real, explicitly declared local positive
 # integer delta. It is a representation proposal with required native fill,
 # not a positive effective native-fill-row replacement.
 local_intent_ops=[]
 r302=H/'REG-two-native-intents-literal-gain-correction-r302'
 r302rows=json.loads((r302/'native-intended-local-gain-ledger.json').read_text())
 for row in r302rows:
  for entry in row.get('all_executed_local_cuts',[]):
   path=Path(entry['cutter_file']);assert sha(path)==entry['cutter_file_SHA256']
   local_intent_ops.append({'owned_UUID':row['owned_UUID'],'kind':'native_intended_only_local_gain_cut','shape':from_wkb(path.read_bytes()),'cutter_file':str(path.resolve()),'cutter_file_SHA256':sha(path),'required_guard_changed':False})
 operation=pickle.loads((R/'ED-native-intended-local-replacement.pkl').read_bytes())
 operation.pop('new_intended');operation['kind']='exact_integer_vertex_replacement_only';operation['new_native_intended_positive_sliver_mm2']=rr['explicit_positive_native_intended_sliver_mm2'];operation['physical_added_credit_mm2']=0
 local_intent_ops.append(operation)
 (O/'native-intended-only-local-operations.pkl').write_bytes(pickle.dumps(local_intent_ops,protocol=5))
 write(O/'explicit-positive-intended-boundary-ledger.json',{'operation':{k:v for k,v in operation.items() if k!='shape'},'positive_sliver_file':str((R/'ED-explicit-new-native-intended-sliver.wkb').resolve()),'positive_sliver_SHA256':rr['explicit_positive_native_intended_sliver_SHA256'],'independent_required_actual_foreign_guard_ledger':str((R/'explicit-integer-endpoint-and-positive-sliver-guards.json').resolve()),'independent_required_actual_foreign_guard_ledger_SHA256':sha(R/'explicit-integer-endpoint-and-positive-sliver-guards.json'),'strict_physical_inside_intended_ledger':str((R/'two-physical-support-role-ledger.json').resolve()),'strict_physical_inside_intended_ledger_SHA256':sha(R/'two-physical-support-role-ledger.json'),'native_fill_qualification':False})
"""
assert s.count(anchor)==1;s=s.replace(anchor,insertion+anchor)
s=s.replace("files=['new-REG7-zones.pkl'","files=['native-intended-only-local-operations.pkl','explicit-positive-intended-boundary-ledger.json','new-REG7-zones.pkl'")
s=s.replace("'R292_scoped_gate_receipt_SHA256':sha(R/'receipt.json')","'R307_supported_integer_outline_gate_receipt_SHA256':sha(R/'receipt.json'),'R292_prior_true_Cu_gate_receipt_SHA256':sha(H/'REG-local-reference-true-copper-and-state-contract-r292/receipt.json')")
s=s.replace("'local_owned_correction_UUIDs':sorted({q['owned_UUID'] for q in cutters})","'local_owned_correction_UUIDs':sorted({q['owned_UUID'] for q in cutters}),'explicit_positive_intended_owned_delta_mm2':rr['explicit_positive_native_intended_sliver_mm2'],'only_two_physical_roles_also_require_inside_final_intended_clip':True")
s=s.replace("'no_saved_native_effective_fill_rows_from_R292_to_be_overlaid':True","'no_saved_native_effective_fill_rows_from_R292_to_be_overlaid':True,'native_intended_local_operations':str((O/'native-intended-only-local-operations.pkl').resolve()),'explicit_small_positive_native_intended_delta_is_not_remove_only':True,'effective_physical_roles_must_be_intersected_with_final_current_native_intents':True")
exec(compile(s,str(H/'freeze_REG7_minimal_current_integration_delta_r300.py'),'exec'))
