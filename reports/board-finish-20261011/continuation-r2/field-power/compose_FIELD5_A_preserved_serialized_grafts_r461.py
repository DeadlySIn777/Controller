"""Preserve R457 failure; verify actual serialized new pieces before emission."""
from pathlib import Path
H=Path(__file__).resolve().parent
owner=H/'compose_FIELD5_A_based_local_restoration_grafts_r457.py'
ns={'__file__':str(owner),'__name__':'_load_A_preserved_constructor_without_running'}
exec(compile(owner.read_text(encoding='utf-8').rsplit('\nexec(compile(s,',1)[0],str(owner),'exec'),ns)
s=ns['s'].replace('minimal-R155-A-array-exact-local-restoration-grafts-r457','minimal-R155-A-array-exact-serialized-grafts-r461')
needle="   bads={'outside_P':S.difference(P),'outside_R':S.difference(R),'outside_current_deficit':S.difference(D)}"
new="""   serialized=IM.records(S);pieces=L.poly(serialized)
   bads={'outside_P':S.difference(P),'outside_R':S.difference(R),'outside_current_deficit':S.difference(D)}
   for pi,piece in enumerate(pieces):
    bads['serialized_'+str(pi)+'_outside_P']=literal(piece).difference(P)
    bads['serialized_'+str(pi)+'_outside_R']=literal(piece).difference(R)
    bads['serialized_'+str(pi)+'_outside_D']=literal(piece).difference(D)"""
assert s.count(needle)==1;s=s.replace(needle,new)
s=s.replace("assert all(literal(x).difference(P).is_empty and literal(x).difference(R).is_empty for x in L.poly(sr))", "assert all(literal(x).difference(P).is_empty and literal(x).difference(R).is_empty and literal(x).difference(D).is_empty for x in L.poly(sr)),('serialized new S scope failure',key,index)")
s=s.replace("'R445_R451_R189_R372_failures_preserved':True", "'R445_R451_R189_R372_failures_preserved':True,'R457_serialized_new_piece_failure_preserved':True,'every_new_piece_actual_serialized_subset_checked':True")
exec(compile(s,str(H/'compose_FIELD5_R385_minimal_current_restore_r387.py'),'exec'))
