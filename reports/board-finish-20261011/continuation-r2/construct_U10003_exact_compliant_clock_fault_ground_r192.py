"""Fresh isolated construction from DIC R262; no stale prior ground bores."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'construct_U10003_preserved_branch_exact_two_port_reference_r174.py';code=source.read_text()
code=code.replace('reference-construction-r174','compliant-clock-fault-ground-construction-r192')
code=code.replace('U10003-sparse-current-ground-fault-construction-r153/model.pkl','coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl').replace('2d7b4c1ff29121e909602f9d76c89c02b4f7d8e5bb6d8a3f3bf5fad7fa1fd1d8','64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144')
code=code.replace('U10003-exact-stub-source-seeded-ground-reference-nomination-r173','U10003-two-signal-port-compliant-coupled-clock-fault-ground-reference-nomination-r191').replace('2b76cfa2e66e614319f1e59778cc199e32d7a30b5100425b1f31317d2a55978e','1d089c22833bf2acfb18118df07e44f5966a5049fc6082899a7ac2e086f21470')
start=code.index(" newtracks=d['tracks'];newvias=");end=code.index(" h['tracks']=[t for t in h['tracks']",start)
replacement="""
 newtracks=d['tracks'];newvias=[d['new_ordinary_signal_via'],*d['replace_only_unadopted_ground_vias']];replace=d['replace_exact_two_unadopted_ground_roles'];replaceids={z['uuid']for z in replace}
 joint=d['exact_joint_packet'];delete={t['uuid']for t in joint['delete_original_tracks']}|{'bd3e65f9-fe77-4a1f-88a1-c704d85af39f','ca9b0c5d-8d6f-44b2-8bec-780b6f1b3f3f','774ec021-d81e-471e-a8c8-0ea85fa50f67'}
 assert len(newtracks)==9 and len(newvias)==3 and len(delete)==7 and len(replaceids)==2
 oldtracks={t['uuid']:t for t in h['tracks']};assert delete<=oldtracks.keys();assert all(any(s==oldtracks[u]for s in g['tracks'])for u in delete)
 assert not{t['uuid']for t in newtracks}&oldtracks.keys();assert not{v['uuid']for v in newvias}&{v['uuid']for v in h['vias']};assert all(v['d']==.5 and v['drill']==.2 for v in newvias)
"""
code=code[:start]+replacement+code[end:]
needle="for z in q:assert set_precision(z['shape'],0).difference(set_precision(z['zone_outline_shape'],0)).is_empty,('physical_outside_intended',z['uuid'])"
replacement="""inherited_outside=[];oldroles={z['uuid']:z for z in q0}
 for z in q:
  outside=set_precision(z['shape'],0).difference(set_precision(z['zone_outline_shape'],0));previous=oldroles.get(z['uuid'])
  if previous is not None and z['uuid']not in replaceids:
   oldoutside=set_precision(previous['shape'],0).difference(set_precision(previous['zone_outline_shape'],0));unchanged=all(z[role].wkb==previous[role].wkb for role in('shape','zone_outline_shape'))
   if unchanged:
    if not outside.is_empty:inherited_outside.append({'UUID':z['uuid'],'unchanged_physical_and_intended_WKB_exact':True,'raw_before_and_after_outside_area_mm2':outside.area,'raw_failure_preserved':True})
   else:assert outside.difference(oldoutside).is_empty,('new_physical_outside_intended',z['uuid'])
  else:assert outside.is_empty,('new_role_physical_outside_intended',z['uuid'])
 put(OUT/'inherited-unchanged-physical-outside-intention-FAIL-ledger.json',inherited_outside)"""
assert code.count(needle)==1;code=code.replace(needle,replacement)
code=code.replace("'two_prior_prospective_tracks_replaced':sorted(delete)","'seven_exact_original_track_replacements':sorted(delete),'both_saved_return_distances_mm':r['signal_return_distances_mm'],'saved_operator_window_mm':[.90,1.0],'unchanged_inherited_outside_intention_failures_preserved':inherited_outside,'R191_raw_new_reference_failures_preserved':r['rows']")
code=code.replace("'old_three_native_B_fault_removals_inherited_from_exact_R153':'NO_ADDITIONAL_NATIVE_DELETES'","'all_seven_native_replacements_require_full_retained_clock_fault_and_source_proof':True,'built_from_R262_to_avoid_stale_unadopted_ground_holes':True")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
