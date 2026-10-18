"""Preserve R461 failure; never let union hide a nonempty new-piece witness."""
from pathlib import Path
H=Path(__file__).resolve().parent
owner=H/'compose_FIELD5_A_preserved_serialized_grafts_r461.py'
ns={'__file__':str(owner),'__name__':'_load_individual_graft_constructor_without_running'}
exec(compile(owner.read_text(encoding='utf-8').rsplit('\nexec(compile(s,',1)[0],str(owner),'exec'),ns)
s=ns['s'].replace('minimal-R155-A-array-exact-serialized-grafts-r461','minimal-R155-A-array-exact-individual-graft-witnesses-r465')
old="""   bad=unary_union([b for b in bads.values()if not b.is_empty])
   if bad.is_empty:break
   bf=O/(key+'-parent-'+str(index)+'-new-graft-'+str(iteration)+'-literal-unbound.wkb');bf.write_bytes(bad.wkb)
   reserve=literal(N.bounded_buffer(bad,.0001));rf=O/(key+'-parent-'+str(index)+'-new-graft-'+str(iteration)+'-ONLY-new-piece-negative-100nm.wkb');rf.write_bytes(reserve.wkb)
   prior=S;S=literal(S).difference(reserve);negative=prior.difference(S)
   reserves.append({'raw_bad_file':str(bf.resolve()),'raw_bad_sha256':sha(bf),'bad_type':bad.geom_type,'bad_area_mm2':bad.area,'negative_file':str(rf.resolve()),'negative_sha256':sha(rf),'negative_mm2':negative.area,'ONLY_new_restoration_piece_changed':True})"""
new="""   rawbad=[(role,bad)for role,bad in bads.items()if not bad.is_empty]
   if not rawbad:break
   guardshapes=[];witnessrows=[]
   for role,bad in rawbad:
    bf=O/(key+'-parent-'+str(index)+'-new-graft-'+str(iteration)+'-'+role+'-literal-unbound.wkb');bf.write_bytes(bad.wkb)
    guarded=literal(N.bounded_buffer(bad,.0001));assert not guarded.is_empty;guardshapes.append(guarded)
    witnessrows.append({'role':role,'raw_file':str(bf.resolve()),'raw_sha256':sha(bf),'type':bad.geom_type,'area_mm2':bad.area,'length_mm':bad.length,'nonempty_kept_individually_without_union_classification':True})
   reserve=literal(unary_union(guardshapes));rf=O/(key+'-parent-'+str(index)+'-new-graft-'+str(iteration)+'-ONLY-new-piece-negative-100nm.wkb');rf.write_bytes(reserve.wkb)
   prior=S;S=literal(S).difference(reserve);negative=prior.difference(S)
   reserves.append({'raw_nonempty_witnesses':witnessrows,'negative_file':str(rf.resolve()),'negative_sha256':sha(rf),'negative_mm2':negative.area,'ONLY_new_restoration_piece_changed':True})"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("'every_new_piece_actual_serialized_subset_checked':True", "'every_new_piece_actual_serialized_subset_checked':True,'R461_union_erased_raw_line_witness_failure_preserved':True,'individual_raw_witness_empty_tests_before_any_union':True")
exec(compile(s,str(H/'compose_FIELD5_R385_minimal_current_restore_r387.py'),'exec'))
