"""Root-authorized diagnostic; preserve raw non-associative proof FAILs.

The exact per-parent after shape is retained when direct immutable-parent
and both outside-restoration checks pass. The derived gain check remains a
bound raw FAIL, never a construction/source/current/native acceptance.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
owner=H/'compose_FIELD5_immutable_parent_subtractive_restore_r445.py'
ns={'__file__':str(owner),'__name__':'_load_parent_replay_without_running'}
exec(compile(owner.read_text(encoding='utf-8').rsplit('\nexec(compile(s,',1)[0],str(owner),'exec'),ns)
s=ns['s'].replace('minimal-R155-immutable-parent-subtractive-rim-restoration-r445','minimal-R155-immutable-parent-raw-FAIL-diagnostic-r451')
s=s.replace("ZERO={", "RAW_FAILURES=[]\nZERO={",1)
old="assert all(checks.values()),('strict immutable parent subtractive repair failure',key,index,checks)"
new="""assert all(checks[k]for k in('after_inside_immutable_parent','outside_restore_before_minus_after_empty','outside_restore_after_minus_before_empty')),('direct parent formula gate failed',key,index,checks)
  if not all(checks.values()):
   row['known_raw_derived_gain_scope_FAIL_preserved']=True;RAW_FAILURES.append({'key':key,'immutable_parent':index,'checks':checks,'P_file':str((O/(key+'-immutable-parent-'+str(index)+'-P.wkb')).resolve()),'A_file':str((O/(key+'-immutable-parent-'+str(index)+'-A.wkb')).resolve()),'R_file':str((O/(key+'-immutable-parent-'+str(index)+'-R.wkb')).resolve()),'after_file':str((O/(key+'-immutable-parent-'+str(index)+'-after.wkb')).resolve()),'gain_file':str((O/(key+'-immutable-parent-'+str(index)+'-gain.wkb')).resolve())});put(O/'known-raw-failed-scope-witnesses.json',RAW_FAILURES)
"""
assert s.count(old)==1;s=s.replace(old,new)
old="rr,proof=IM.subtract(replay,cc or [unary_union([])],O,old['uuid']+'-'+layer+'-local-sparse-replay');after=unary_union(L.poly(rr));gained=after.difference(body)"
new="""if reconstructed and not cc:
    rr=replay;proof={'no_new_masks_on_reconstructed_records':True,'all_exact_parent_formula_records_preserved':True,'no_aggregate_negative_or_coordinate_snap':True}
   else:rr,proof=IM.subtract(replay,cc or [unary_union([])],O,old['uuid']+'-'+layer+'-local-sparse-replay')
   after=unary_union(L.poly(rr));gained=after.difference(body)"""
assert s.count(old)==1;s=s.replace(old,new)
old="if reconstructed:raise AssertionError(('structural restore leaves literal out-of-scope remainder; no remote negative admitted',old['uuid'],layer,bad.area))"
new="""if reconstructed:
     direct_checks={'before_outside_R_lost_empty':body.difference(restorebody).difference(after.difference(restorebody)).is_empty,'after_outside_R_gained_empty':after.difference(restorebody).difference(body.difference(restorebody)).is_empty}
     assert all(direct_checks.values()),('whole record direct outside-R diagnostic gate failed',old['uuid'],layer,direct_checks)
     RAW_FAILURES.append({'UUID':old['uuid'],'layer':layer,'known_raw_aggregate_derived_scope_FAIL':True,'raw_failure_file':str(bf.resolve()),'raw_failure_sha256':sha(bf),'raw_failure_mm2':bad.area,'raw_failure_type':bad.geom_type,'direct_checks':direct_checks,'no_remote_negative_or_original_snap':True});put(O/'known-raw-failed-scope-witnesses.json',RAW_FAILURES);break
"""
assert s.count(old)==1;s=s.replace(old,new)
old="gained=after.difference(body);assert gained.difference(restorebody).is_empty\n   if baseline is not None:assert after.difference(baseline).is_empty"
new="""gained=after.difference(body)
   if not reconstructed:
    assert gained.difference(restorebody).is_empty
    if baseline is not None:assert after.difference(baseline).is_empty
   else:assert all(op['checks']['after_inside_immutable_parent']for op in parent_proof['immutable_parent_operations'])"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("'source_reference_current_native':'OPEN'", "'source_reference_current_native':'OPEN','known_raw_construction_FAILURES_preserved':RAW_FAILURES,'diagnostic_only_never_construction_PASS':True")
s=s.replace("'EXPLORATORY_MINIMAL_R155_FIELD5_IN4_WITHDRAWAL_IN2_REPLACEMENT_CONSTRUCTOR_COMPLETE_FULL_GATES_OPEN'", "'KNOWN_RAW_FAILURE_DIAGNOSTIC_PARENT_FORMULA_MODEL_EMITTED_NOT_CONSTRUCTION_PASS'")
s=s.replace("'all_contact_source_reference_true_geometry_current_and_native_gates':'OPEN'", "'all_contact_source_reference_true_geometry_current_and_native_gates':'OPEN','known_raw_construction_failures':RAW_FAILURES,'no_native_staging_or_adoption_authorized':True,'root_authorized_failure_bound_host_diagnostic_only':True")
exec(compile(s,str(H/'compose_FIELD5_R385_minimal_current_restore_r387.py'),'exec'))
