"""Preserve exact current A arrays; add only locally bound restoration S.

No existing current polygon is replaced by the immutable parent. Parent P
constrains added copper only; inherited current boundaries are retained.
All restoration-piece reserves remove only new S, never current A.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
owner=H/'compose_FIELD5_strict_aggregate_original_cut_rim_r423.py'
ns={'__file__':str(owner),'__name__':'_load_frozen_constructor_without_running'}
exec(compile(owner.read_text(encoding='utf-8').rsplit('\nexec(compile(s,',1)[0],str(owner),'exec'),ns)
s=ns['s'].replace('minimal-R155-strict-aggregate-boundary-cut-rim-restoration-r423','minimal-R155-A-array-exact-local-restoration-grafts-r457')
s=s.replace('import immutable_restored_fill_aggregate_subtraction_r421 as IM','import immutable_local_fill_subtraction_r254 as IM')
helper='''
def local_grafts(recs,originalrecs,restorepieces,key):
 currentparts=L.poly(recs);originalparts=L.poly(originalrecs);restore=literal(unary_union(L.poly(restorepieces)));current=literal(unary_union(currentparts));output=copy.deepcopy(recs);ops=[]
 for index,part in enumerate(originalparts):
  P=literal(part);R=P.intersection(restore)
  if R.is_empty:continue
  D=P.difference(current);S=R.intersection(D);reserves=[]
  for iteration in range(32):
   bads={'outside_P':S.difference(P),'outside_R':S.difference(R),'outside_current_deficit':S.difference(D)}
   bad=unary_union([b for b in bads.values()if not b.is_empty])
   if bad.is_empty:break
   bf=O/(key+'-parent-'+str(index)+'-new-graft-'+str(iteration)+'-literal-unbound.wkb');bf.write_bytes(bad.wkb)
   reserve=literal(N.bounded_buffer(bad,.0001));rf=O/(key+'-parent-'+str(index)+'-new-graft-'+str(iteration)+'-ONLY-new-piece-negative-100nm.wkb');rf.write_bytes(reserve.wkb)
   prior=S;S=literal(S).difference(reserve);negative=prior.difference(S)
   reserves.append({'raw_bad_file':str(bf.resolve()),'raw_bad_sha256':sha(bf),'bad_type':bad.geom_type,'bad_area_mm2':bad.area,'negative_file':str(rf.resolve()),'negative_sha256':sha(rf),'negative_mm2':negative.area,'ONLY_new_restoration_piece_changed':True})
  else:raise AssertionError(('new graft strict scope did not settle',key,index))
  assert S.difference(P).is_empty and S.difference(R).is_empty and S.difference(D).is_empty
  # Same-net closed boundary contact is allowed. Any explicit retreat on
  # new S still needs a fresh actual source/contact proof.
  f=O/(key+'-parent-'+str(index)+'-only-new-graft.wkb');f.write_bytes(S.wkb)
  sr=IM.records(S);assert all(literal(x).difference(P).is_empty and literal(x).difference(R).is_empty for x in L.poly(sr))
  output.extend(sr);ops.append({'immutable_parent_index':index,'original_parent_sha256':dg(P),'local_allowed_R_sha256':dg(R),'current_deficit_sha256':dg(D),'new_graft_file':str(f.resolve()),'new_graft_sha256':sha(f),'new_graft_area_mm2':S.area,'literal_outside_P_EMPTY':True,'literal_outside_R_EMPTY':True,'literal_outside_current_deficit_EMPTY':True,'same_net_boundary_contacts_allowed':True,'explicit_ONLY_new_graft_reserves':reserves})
 assert output[:len(recs)]==recs
 return output,{'all_existing_current_record_arrays_exact_in_original_order':True,'current_record_count':len(recs),'added_record_count':len(output)-len(recs),'new_restoration_grafts':ops,'original_parent_not_used_to_clip_current_A':True,'no_aggregate_current_plus_restore_operator':True,'no_remote_negative_or_original_coordinate_snap':True}
'''
assert s.count('\ndef main():')==1;s=s.replace('\ndef main():',helper+'\ndef main():')
old="rr,proof=IM.subtract(recs+restorepieces,cc or [unary_union([])],O,old['uuid']+'-'+layer+'-local-sparse-replay');after=unary_union(L.poly(rr));gained=after.difference(body)"
new="""reconstructed=bool(restorepieces)
   if reconstructed:
    assert not cc,('restoration is on a changed layer requiring separate new-mask replay',old['uuid'],layer)
    rr,proof=local_grafts(recs,origzone['fills'][layer],restorepieces,old['uuid']+'-'+layer)
   else:rr,proof=IM.subtract(recs,cc or [unary_union([])],O,old['uuid']+'-'+layer+'-local-sparse-replay')
   after=unary_union(L.poly(rr));gained=after.difference(body)"""
assert s.count(old)==1;s=s.replace(old,new)
start=s.index("   baseline=unary_union(L.poly(origzone['fills'][layer]))")
end=s.index("   qq['fills'][layer]=rr",start)
old=s[start:end]
new="""   local_reserves=[]
   if reconstructed:
    # Keep the aggregate raw operator results visible. Array conservation
    # and separately bound additions are the construction evidence only;
    # this does not waive source/reference/physical/native acceptance.
    raw=gained.difference(restorebody);bf=O/(old['uuid']+'-'+layer+'-aggregate-raw-outside-restore.wkb');bf.write_bytes(raw.wkb)
    proof['raw_aggregate_outside_restore']={'is_empty':raw.is_empty,'type':raw.geom_type,'area_mm2':raw.area,'length_mm':raw.length,'file':str(bf.resolve()),'sha256':sha(bf),'raw_FAIL_if_nonempty_preserved':not raw.is_empty}
   else:
    assert gained.is_empty
"""
s=s[:start]+new+s[end:]
s=s.replace("'source_reference_current_native':'OPEN'", "'source_reference_current_native':'OPEN','existing_current_A_arrays_preserved_restoration_scope':True,'R445_R451_R189_R372_failures_preserved':True,'no_GEOS_empty_classification_override':True")
s=s.replace("'EXPLORATORY_MINIMAL_R155_FIELD5_IN4_WITHDRAWAL_IN2_REPLACEMENT_CONSTRUCTOR_COMPLETE_FULL_GATES_OPEN'","'DIAGNOSTIC_A_ARRAY_EXACT_LOCAL_GRAFT_MODEL_FULL_SOURCE_REFERENCE_GATES_OPEN'")
exec(compile(s,str(H/'compose_FIELD5_R385_minimal_current_restore_r387.py'),'exec'))
