"""Preserved R288 successor: actual 100 nm reserve and exact guard scope.

All full-row inherited failures remain explicit. A scoped PASS cannot be used
as global/native acceptance. Only the positive restored patch and the actual
changed owned bodies are eligible for an incremental geometry pass.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'repair_exact_required_native_reference_masks_r288.py').read_text(encoding='utf-8')
s=s.replace('REG-exact-required-native-reference-mask-repair-r288','REG-exact-reference-local-owned-guard-repair-r290').replace('R288','R290')
# R288 recorded 0.1 nm (.0000001 mm). Correct this derived constructor to the
# intended 100 nm (.0001 mm); unchanged required domain guard remains .625.
s=s.replace('.0000001','.0001')
anchor=" # Rebuild only effective fill rows whose precise owned obstacle or restored"
insertion="""
 # Resolve the reconstructed ed7 actual gap by withdrawing ONLY its owned
 # physical/native-outline body around exact nearest foreign native points.
 # Keep every native filled point; do not trade reference copper for margin.
 local_actual_gap_cuts=[]
 for uid in (ED,D8):
  q=zm[uid];layer=q['layer']
  for native in c['zones']:
   if native['uuid'] not in {r['uuid'] for r in h['zones']} or C.norm(native['net'])==C.norm(q['net']):continue
   body=restore.get((native['uuid'],layer),actual(native,layer))
   if body.is_empty:continue
   required=max(G.gap(h,native['net'],q['net']),float(native.get('clearance_mm',.15)),float(q.get('clearance_mm',.15)))+.025
   for iteration in range(100):
    gap=body.distance(q['shape'])
    if gap+1e-10>=required:break
    point,_=nearest_points(body,q['shape']);cut=set_precision(P.bounded_disk({'x':point.x,'y':point.y},required+.0001),0)
    row={'owned_UUID':uid,'foreign_native_UUID':native['uuid'],'layer':layer,'iteration':iteration,'actual_before_mm':gap,'required_mm':required,'constructor_reserve_mm':.0001,'exact_native_point_mm':[point.x,point.y],'cutter_SHA256':P.digest(cut),'roles':[]}
    cf=O/(uid+'-'+native['uuid']+'-actual-margin-'+str(iteration)+'.wkb');cf.write_bytes(cut.wkb);row['cutter_file']=str(cf.resolve());row['cutter_file_SHA256']=sha(cf)
    for role in ('shape','zone_outline_shape'):
     old=q[role];new=set_precision(old,0).difference(cut) if role=='shape' else native_role(old,cut)
     assert new.difference(set_precision(old,0)).area<1e-12;q[role]=new
     row['roles'].append({'role':role,'before_SHA256':P.digest(old),'after_SHA256':P.digest(new),'removed_mm2':old.difference(new).area,'added_mm2':new.difference(old).area,'explicit_precision_grid_mm':get_precision(new)})
    local_actual_gap_cuts.append(row)
   else:raise AssertionError(('unresolved actual native guard',uid,native['uuid']))
 write(O/'exact-native-point-owned-margin-cuts.json',local_actual_gap_cuts)
"""
assert s.count(anchor)==1;s=s.replace(anchor,insertion+anchor)
old="""   if gap<required+.001:guards.append({'kind':'restored_actual_native_to_foreign_owned','owned_UUID':other['uuid'],'foreign_UUID':uid,'layer':layer,'required_mm':required,'actual_mm':gap,'PASS':gap+1e-10>=required})"""
new="""   prior=actual(candidate_native[uid],layer);added=sh.difference(prior);added_gap=other['shape'].distance(added) if not added.is_empty else None;prior_gap=other['shape'].distance(prior)
   if gap<required+.001:guards.append({'kind':'restored_actual_native_to_foreign_owned','owned_UUID':other['uuid'],'foreign_UUID':uid,'layer':layer,'required_mm':required,'actual_mm':gap,'full_actual_row_PASS':gap+1e-10>=required,'full_row_actual_before_local_restore_mm':prior_gap,'full_row_gap_not_decreased_by_restore':gap+1e-10>=prior_gap,'positive_restored_patch_mm2':added.area,'positive_restored_patch_actual_gap_mm':added_gap,'PASS':added_gap is None or added_gap+1e-10>=required,'unchanged_inherited_full_row_failures_remain_global_gate_open':gap+1e-10<required})"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("'only_changed_owned_UUIDs':[ED,D8],", "'only_changed_owned_UUIDs':[ED,D8],'R288_wrong_reserve_mm_preserved':.0000001,'corrected_constructor_reserve_mm':.0001,'unchanged_inherited_full_row_guard_errors':[q for q in guards if q.get('full_actual_row_PASS') is False],")
s=s.replace('SCOPED_OLD_REFERENCE_REPAIR_PASS_FULL_JOINT_NATIVE_REVIEW_OPEN','SCOPED_OLD_REFERENCE_NEW_GUARD_PASS_INHERITED_GLOBAL_NATIVE_GATES_OPEN')
exec(compile(s,str(H/'repair_exact_required_native_reference_masks_r288.py'),'exec'))
