"""Only explicit converter-local actual filled negative witnesses added."""
from pathlib import Path
import ast
H=Path(__file__).resolve().parent
p=H/'construct_IO3_TMR_union_individual_local_negative_scopes_r509.py';t=ast.parse(p.read_text(encoding='utf-8'));t.body.pop();ns={'__file__':str(p)};exec(compile(t,str(p),'exec'),ns);s=ns['s']
s=s.replace("O=H/'IO3-TMR-bypass-only-two-role-union-individual-local-scopes-r509'", "O=H/'IO3-TMR-bypass-only-two-role-union-individual-role-fill-scopes-r511'")
needle="  assert gain.is_empty and outside.is_empty,('actual union local negative filled proof',label,summary(gain),summary(outside))"
assert s.count(needle)==1
s=s.replace(needle,"""  fill_scope=[lit(N.bounded_buffer(scope,.0001))];filled_witnesses=[]
  for fill_scope_it in range(16):
   if outside.is_empty:break
   assert outside.difference(locality).is_empty,('actual filled negative not at converter join',label,fill_scope_it,summary(outside))
   wf=O/(label+'-'+str(fill_scope_it)+'-actual-negative-outside-prior-scope.wkb');wf.write_bytes(outside.wkb)
   reserve=lit(N.bounded_buffer(outside,.0001));rf=O/(label+'-'+str(fill_scope_it)+'-individual-100nm-scope.wkb');rf.write_bytes(reserve.wkb)
   filled_witnesses.append({'iteration':fill_scope_it,'raw_actual_negative':summary(outside),'witness_file':str(wf.resolve()),'witness_sha256':sha(wf),'explicit_scope_reserve_file':str(rf.resolve()),'scope_reserve_sha256':sha(rf),'reserve_mm':.0001,'actual_geometry_unchanged_by_scope_binding':True,'no_size_waiver':True})
   fill_scope.append(reserve);outside=removed.difference(unary_union(fill_scope))
  assert gain.is_empty and outside.is_empty,('actual union gain/unbound local negative',label,summary(gain),summary(outside))
  put(O/(label+'-individual-filled-negative-scope-ledger.json'),filled_witnesses)""")
s=s.replace("print('R509 receipt'", "print('R511 receipt'").replace("b['IO3_native_TMR_individual_scope_same_settings_union_r509']", "b['IO3_native_TMR_individual_role_fill_scope_same_settings_union_r511']")
exec(compile(s,str(H/'construct_IO3_TMR_union_individual_role_and_fill_scopes_r511.py'),'exec'))
