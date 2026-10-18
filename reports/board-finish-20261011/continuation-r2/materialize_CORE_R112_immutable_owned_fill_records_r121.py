"""Preserve R214 actual owned filled records outside exact role withdrawals."""
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'materialize_CORE_wide_reserved_IO3_R214_r112.py';code=source.read_text()
needle="out=H/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112'";assert code.count(needle)==1
code=code.replace(needle,"out=H/'CORE-R112-immutable-native-and-owned-filled-records-r121'")
needle=" for q in owned:native.append({'uuid':q['uuid']"
assert code.count(needle)==1
start=code.index(needle);end=code.index("\n current={**new_h,'zones':native}",start)
old=code[start:end]
assert old.count('native.append(')==1
replacement=""" immutable_tuple=pickle.loads(immutable_head.read_bytes());prior_owned={q['uuid']:q for q in immutable_tuple[3]};prior_actual={q['uuid']:q for q in immutable_tuple[4]['zones']};owned_record_rows=[]
 for q in owned:
  if q['uuid'] not in prior_owned:
   assert q['uuid']==core['uuid'];fills={q['layer']:G.records(q['shape'])};ledger={'UUID':q['uuid'],'layer':q['layer'],'new_only_generated_CORE_role':True,'after_filled_WKB_sha256':digest(unary_union(C.poly(fills[q['layer']]))) }
  else:
   original=prior_owned[q['uuid']];actual_before=prior_actual[q['uuid']];assert q['layer']==original['layer'];oldshape=set_precision(original['shape'],0);newshape=set_precision(q['shape'],0);assert oldshape.wkb==original['shape'].wkb and newshape.wkb==q['shape'].wkb
   added=newshape.difference(oldshape);assert added.is_empty,'Existing owned role gained physical Cu';withdrawal=oldshape.difference(newshape);wf=out/(q['uuid']+'.exact-role-withdrawal.wkb');wf.write_bytes(withdrawal.wkb)
   fills=copy.deepcopy(actual_before['fills']);before_filled=unary_union(C.poly(fills[q['layer']]))
   if withdrawal.is_empty:
    assert newshape.equals(oldshape);unchanged=True
   else:
    base_zero=set_precision(before_filled,0);assert base_zero.wkb==before_filled.wkb;remaining=base_zero.difference(withdrawal);fills[q['layer']]=G.records(remaining);unchanged=False
   after_filled=unary_union(C.poly(fills[q['layer']]));assert after_filled.difference(before_filled).is_empty,'No reclaimed owned filled Cu is credited'
   ledger={'UUID':q['uuid'],'layer':q['layer'],'R214_physical_before_WKB_sha256':digest(original['shape']),'R112_physical_after_WKB_sha256':digest(q['shape']),'R214_intended_before_WKB_sha256':digest(original['zone_outline_shape']),'R112_intended_after_WKB_sha256':digest(q['zone_outline_shape']),'R214_before_filled_WKB_sha256':digest(before_filled),'after_filled_WKB_sha256':digest(after_filled),'exact_withdrawal_file':str(wf.resolve()),'exact_withdrawal_WKB_sha256':digest(withdrawal),'physical_role_withdrawal_mm2':withdrawal.area,'filled_removed_mm2':before_filled.difference(after_filled).area,'filled_added_mm2':0.,'unchanged_filled_records_byte_structure':unchanged and fills==actual_before['fills'],'new_primitive_role_cut_UUIDs':[r['UUID'] for r in rolecuts if r['UUID']==q['uuid']]}
  owned_record_rows.append(ledger)
  native.append({'uuid':q['uuid'],'net':q['net'],'priority':int(q.get('priority',124)),'clearance_mm':float(q.get('clearance_mm',.15)),'min_thickness_mm':float(q.get('min_thickness_mm',.15)),'pad_connect_mode':q.get('pad_connect_mode','FULL_SOLID'),'island_removal_mode':int(q.get('island_removal_mode',1)),'thermal_gap_mm':float(q.get('thermal_gap_mm',.15)),'thermal_bridge_width_mm':float(q.get('thermal_bridge_width_mm',.3)),'fills':fills,'prospective_not_native':True})
 put(out/'immutable-R214-owned-filled-record-delta-ledger.json',owned_record_rows)
"""
code=code[:start]+replacement+code[end:]
needle=" current={**new_h,'zones':native};";assert code.count(needle)==1
check=""" prior_R112=H/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112/model.pkl';assert sha(prior_R112)=='6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e';prior_tuple=pickle.loads(prior_R112.read_bytes());assert g==prior_tuple[0] and new_h==prior_tuple[1];assert len(owned)==len(prior_tuple[3])
 for now,earlier in zip(owned,prior_tuple[3]):
  assert set(now)==set(earlier)
  for key in now:
   assert now[key].wkb==earlier[key].wkb if hasattr(now[key],'wkb') else now[key]==earlier[key],(now['uuid'],key)
 put(out/'exact-R112-role-discrete-native-definition-identity.json',{'R112_model_sha256':sha(prior_R112),'R112_receipt_sha256':sha(prior_R112.with_name('receipt.json')),'all_g_h_fields_exact':True,'all_owned_physical_intended_settings_metadata_exact':True,'only_current_filled_record_provenance_changes':True,'no_native_outline_or_physical_role_mutation':True})
"""
code=code.replace(needle,check+needle)
needle="'model_sha256':sha(out/'model.pkl')";assert code.count(needle)==1
code=code.replace(needle,needle+",'immutable_owned_fill_delta_ledger_sha256':sha(out/'immutable-R214-owned-filled-record-delta-ledger.json'),'R112_geometry_identity_sha256':sha(out/'exact-R112-role-discrete-native-definition-identity.json')")
code=code.replace('R112_','R121_')
exec(compile(code,str(source),'exec'))
