"""Keep failed R389; explicitly remove any literal unbound fill boundary."""
from pathlib import Path
H=Path(__file__).resolve().parent
t=(H/'compose_FIELD5_R385_explicit_literal_restore_boundary_r389.py').read_text(encoding='utf-8')
needle="exec(compile(s,str(H/'compose_FIELD5_R385_minimal_current_restore_r387.py'),'exec'))"
addition="""
s=s.replace('minimal-R155-local-literal-bound-restoration-composition-r389','minimal-R155-strict-filled-restoration-composition-r393')
start=s.index('   if not gained.difference(restorebody).is_empty:')
end=s.index(\"   qq['fills'][layer]=rr;filled.append\",start)
s=s[:start]+\"\"\"   baseline=unary_union(L.poly(origzone['fills'][layer])) if origzone is not None and layer in origzone['fills'] else None
   local_reserves=[]
   for iteration in range(32):
    gained=after.difference(body);bad=unary_union([gained.difference(restorebody),after.difference(baseline)if baseline is not None else unary_union([])])
    if bad.is_empty:break
    bf=O/(old['uuid']+'-'+layer+'-'+str(iteration)+'-literal-unbound-filled-gain.wkb');bf.write_bytes(bad.wkb)
    reserve=literal(N.bounded_buffer(bad,.0001));rf=O/(old['uuid']+'-'+layer+'-'+str(iteration)+'-explicit-100nm-filled-negative.wkb');rf.write_bytes(reserve.wkb)
    rr,extra=IM.subtract(rr,[reserve],O,old['uuid']+'-'+layer+'-strict-local-bound-'+str(iteration));after=unary_union(L.poly(rr))
    local_reserves.append({'iteration':iteration,'literal_unbound_file':str(bf.resolve()),'literal_unbound_sha256':sha(bf),'literal_unbound_mm2':bad.area,'explicit_negative_file':str(rf.resolve()),'explicit_negative_sha256':sha(rf),'per_record_strict_subset_proof':extra})
   else:raise AssertionError(('strict filled local restore region did not converge',old['uuid'],layer))
   gained=after.difference(body);assert gained.difference(restorebody).is_empty
   if baseline is not None:assert after.difference(baseline).is_empty
\"\"\"+s[end:]
s=s.replace(\"'strict_current_plus_bound_restore_record_proof':proof\",\"'strict_current_plus_bound_restore_record_proof':proof,'explicit_local_literal_boundary_negative_reserves':local_reserves\")
exec(compile(s,str(H/'compose_FIELD5_R385_minimal_current_restore_r387.py'),'exec'))
"""
assert t.count(needle)==1;t=t.replace(needle,addition)
exec(compile(t,str(H/'compose_FIELD5_R385_explicit_literal_restore_boundary_r389.py'),'exec'))
