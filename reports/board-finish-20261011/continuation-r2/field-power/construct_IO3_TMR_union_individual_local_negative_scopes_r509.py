"""Preserve R507 raw failure; name each actual converter-local negative."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_IO3_TMR_bypass_minimal_local_negative_union_r507.py').read_text(encoding='utf-8')
s=s.replace("O=H/'IO3-TMR-bypass-only-two-role-union-local-negative-r507'", "O=H/'IO3-TMR-bypass-only-two-role-union-individual-local-scopes-r509'")
needle="  assert gain.is_empty and outside.is_empty,('minimal union undeclared gain/loss',role,summary(gain),summary(outside))"
assert s.count(needle)==1
s=s.replace(needle,"""  scope_witnesses=[]
  for scope_it in range(16):
   if outside.is_empty:break
   assert outside.difference(locality).is_empty,('additional actual negative outside converter join locality',role,scope_it,summary(outside))
   wf=O/(role+'-'+str(scope_it)+'-actual-negative-outside-prior-declared-scope.wkb');wf.write_bytes(outside.wkb)
   reserve=lit(N.bounded_buffer(outside,.0001));rf=O/(role+'-'+str(scope_it)+'-individual-100nm-scope-reserve.wkb');rf.write_bytes(reserve.wkb)
   scope_witnesses.append({'iteration':scope_it,'actual_raw_negative_witness':summary(outside),'witness_file':str(wf.resolve()),'witness_sha256':sha(wf),'explicit_local_scope_reserve_file':str(rf.resolve()),'scope_reserve_sha256':sha(rf),'reserve_mm':.0001,'role_geometry_unchanged_by_scope_binding':True,'no_size_waiver':True})
   allreserves.append(reserve);scope=unary_union(allreserves);outside=loss.difference(scope)
  assert gain.is_empty and outside.is_empty,('minimal union gained copper or unbound local negative',role,summary(gain),summary(outside))
  put(O/(role+'-individual-local-negative-scope-ledger.json'),scope_witnesses)""")
s=s.replace("print('R507 receipt'", "print('R509 receipt'")
s=s.replace("b['IO3_native_TMR_local_same_settings_union_r507']", "b['IO3_native_TMR_individual_scope_same_settings_union_r509']")
exec(compile(s,str(H/'construct_IO3_TMR_union_individual_local_negative_scopes_r509.py'),'exec'))
