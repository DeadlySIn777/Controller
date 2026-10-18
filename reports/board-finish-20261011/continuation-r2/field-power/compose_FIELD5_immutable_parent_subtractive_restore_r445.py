"""Restore local old Cu by one subtraction from its immutable parent.

No overlapping current+restore record concatenation, native coordinate snap,
or remote aggregate-negative repair is admitted by this successor.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
owner=H/'compose_FIELD5_strict_aggregate_original_cut_rim_r423.py'
ns={'__file__':str(owner),'__name__':'_load_frozen_restore_source_without_running'}
exec(compile(owner.read_text(encoding='utf-8').rsplit('\nexec(compile(s,',1)[0],str(owner),'exec'),ns)
s=ns['s'].replace('minimal-R155-strict-aggregate-boundary-cut-rim-restoration-r423','minimal-R155-immutable-parent-subtractive-rim-restoration-r445')
helper='''
def parent_subtractive_restore(recs,originalrecs,restorepieces,key):
 """A is exact current descendants; P is exact original, R bound support."""
 currentparts=L.poly(recs);originalparts=L.poly(originalrecs);restore=unary_union(L.poly(restorepieces));used=set();output=[];operations=[]
 for index,part in enumerate(originalparts):
  pp=literal(part);rr=restore.intersection(pp)
  if rr.is_empty:continue
  descendants=[]
  for ci,cp in enumerate(currentparts):
   if cp.difference(pp).is_empty:
    assert ci not in used,('ambiguous immutable parent',key,index,ci);descendants.append(ci);used.add(ci)
   elif cp.intersects(rr):
    raise AssertionError(('current record crosses bound immutable parent',key,index,ci,cp.difference(pp).area))
  aa=unary_union([literal(currentparts[i])for i in descendants]);deficit=pp.difference(aa);withdrawal=deficit.difference(rr);after=pp.difference(withdrawal);gain=after.difference(aa)
  checks={'after_inside_immutable_parent':after.difference(pp).is_empty,'gain_inside_declared_local_restore':gain.difference(rr).is_empty,'outside_restore_before_minus_after_empty':aa.difference(rr).difference(after.difference(rr)).is_empty,'outside_restore_after_minus_before_empty':after.difference(rr).difference(aa.difference(rr)).is_empty}
  for role,shape in(('P',pp),('A',aa),('R',rr),('D',deficit),('D_minus_R',withdrawal),('after',after),('gain',gain)):
   f=O/(key+'-immutable-parent-'+str(index)+'-'+role+'.wkb');f.write_bytes(shape.wkb)
  row={'immutable_original_record':index,'current_descendant_records':descendants,'original_sha256':dg(pp),'current_sha256':dg(aa),'restore_sha256':dg(rr),'deficit_sha256':dg(deficit),'withdrawal_sha256':dg(withdrawal),'after_sha256':dg(after),'literal_restored_mm2':gain.area,'checks':checks,'all_metadata_zero_without_coordinate_snap':True};operations.append(row);put(O/(key+'-immutable-parent-subtractive-checkpoint.json'),operations)
  assert all(checks.values()),('strict immutable parent subtractive repair failure',key,index,checks)
  output.extend(IM.records(after))
 for i,rec in enumerate(recs):
  if i not in used:output.append(rec)
 outputpieces=L.poly(output);remaining=restore.difference(unary_union(originalparts));assert remaining.is_empty,('restore outside every exact original parent',key,remaining.area)
 return output,{'immutable_parent_operations':operations,'unaffected_current_record_indices':sorted(set(range(len(recs)))-used),'unaffected_current_arrays_exact':True,'no_overlapping_restore_record_concatenation':True,'no_native_coordinate_snap':True}
'''
assert s.count('\ndef main():')==1;s=s.replace('\ndef main():',helper+'\ndef main():')
old="rr,proof=IM.subtract(recs+restorepieces,cc or [unary_union([])],O,old['uuid']+'-'+layer+'-local-sparse-replay');after=unary_union(L.poly(rr));gained=after.difference(body)"
new="""reconstructed=bool(restorepieces);parent_proof=None
   if reconstructed:
    replay,parent_proof=parent_subtractive_restore(recs,origzone['fills'][layer],restorepieces,old['uuid']+'-'+layer)
   else:replay=recs
   rr,proof=IM.subtract(replay,cc or [unary_union([])],O,old['uuid']+'-'+layer+'-local-sparse-replay');after=unary_union(L.poly(rr));gained=after.difference(body)"""
assert s.count(old)==1;s=s.replace(old,new)
needle="bf=O/(old['uuid']+'-'+layer+'-'+str(iteration)+'-literal-unbound-filled-gain.wkb');bf.write_bytes(bad.wkb)"
assert s.count(needle)==1;s=s.replace(needle,needle+"\n    if reconstructed:raise AssertionError(('structural restore leaves literal out-of-scope remainder; no remote negative admitted',old['uuid'],layer,bad.area))")
s=s.replace("'strict_current_plus_bound_restore_record_proof':proof", "'strict_current_plus_bound_restore_record_proof':proof,'immutable_parent_subtractive_replay':parent_proof")
s=s.replace("'R417_aggregate_literal_gain_failure_preserved':True", "'R417_aggregate_literal_gain_failure_preserved':True,'R423_R429_R431_failed_evidence_preserved':True,'local_restore_formula':'P-(D-R), D=P-A; strict_literal_unchanged_outside_R','no_remote_aggregate_negative_for_restoration':True")
exec(compile(s,str(H/'compose_FIELD5_R385_minimal_current_restore_r387.py'),'exec'))
