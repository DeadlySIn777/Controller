"""Preserve R387 strict failure; bound every literal restoration point."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'compose_FIELD5_R385_minimal_current_restore_r387.py').read_text(encoding='utf-8')
s=s.replace('minimal-R155-local-immutable-restoration-composition-r387','minimal-R155-local-literal-bound-restoration-composition-r389')
needle="  gain=literal(after).difference(literal(prior));assert gain.difference(oldmask).is_empty and gain.difference(orig).is_empty"
new="""  for iteration in range(32):
   gain=literal(after).difference(literal(prior));outside=unary_union([gain.difference(oldmask),gain.difference(orig)])
   if outside.is_empty:break
   gf=O/(ED+'-'+role+'-'+str(iteration)+'-literal-unbound-restoration-gain.wkb');gf.write_bytes(outside.wkb)
   reserve=literal(N.bounded_buffer(outside,.0001));rf=O/(ED+'-'+role+'-'+str(iteration)+'-explicit-literal-100nm-negative.wkb');rf.write_bytes(reserve.wkb)
   remaining=literal(after).difference(reserve)
   if role=='shape':after=remaining
   else:after,extra=canon_subset(remaining,literal(after),ED+'-'+role+'-literal-bound-'+str(iteration));reserves.extend(extra)
   reserves.append({'iteration':iteration,'literal_unbound_gain_file':str(gf.resolve()),'literal_unbound_gain_sha256':sha(gf),'literal_unbound_gain_mm2':outside.area,'explicit_negative_reserve_file':str(rf.resolve()),'explicit_negative_reserve_sha256':sha(rf)})
  else:raise AssertionError(('strict restored-point original/former-mask bound did not converge',role))
  gain=literal(after).difference(literal(prior));assert gain.difference(oldmask).is_empty and gain.difference(orig).is_empty"""
assert s.count(needle)==1;s=s.replace(needle,new)
exec(compile(s,str(H/'compose_FIELD5_R385_minimal_current_restore_r387.py'),'exec'))
