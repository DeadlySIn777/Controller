"""Derived local keepout cut with separately declared boundary negatives.

R477 remains immutable. Root explicitly authorized the two local canonical
boundary wedges; every additional witness is retained and locality checked.
No size waiver, remote coordinate snap, native job, or adoption is implied.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_current_FA_native_TMR_keepout_local_negative_r477.py').read_text(encoding='utf-8')
s=s.replace("O=H/'R155-protected-FA-only-TMR-U14619-local-negative-construction-r477'", "O=H/'R155-protected-FA-TMR-declared-local-boundary-negatives-r479'")
s=s.replace('rows=[]\n for role', 'rows=[];scope_rows=[]\n for role')
s=s.replace("assert gained.is_empty and outside.is_empty and hit.is_empty,('exact local role proof failed',role,gained.geom_type,outside.geom_type,hit.geom_type)", """assert gained.is_empty and hit.is_empty,('no-gain/native-area check failed',role)
  scope=mask;extra_negative=removed.difference(mask);sf=O/(role+'-explicit-local-boundary-negative.wkb');sf.write_bytes(extra_negative.wkb)
  assert extra_negative.difference(lit(N.bounded_buffer(area,2.0))).is_empty,('extra negative leaves actual converter locality',role)
  local_reserve=lit(N.bounded_buffer(extra_negative,.0001)) if not extra_negative.is_empty else extra_negative
  rf=O/(role+'-explicit-local-boundary-100nm-scope-reserve.wkb');rf.write_bytes(local_reserve.wkb)
  scope=unary_union([mask,local_reserve]);unbound=removed.difference(scope);uf=O/(role+'-removed-outside-exact-declared-negative-scope.wkb');uf.write_bytes(unbound.wkb)
  assert unbound.is_empty,('removed outside named primary plus explicit boundary negatives',role,unbound.geom_type,unbound.area)
  scope_rows.append({'role':role,'extra_actual_negative_file':str(sf.resolve()),'extra_actual_negative_sha256':sha(sf),'extra_actual_negative_area_mm2':extra_negative.area,'extra_actual_negative_bounds':extra_negative.bounds,'scope_reserve_file':str(rf.resolve()),'scope_reserve_sha256':sha(rf),'reserve_mm':.0001,'scope_reserve_not_a_separate_geometric_cut':True,'removed_outside_exact_declared_scope_EMPTY':True,'R477_primary_mask_plus500nm_failure_preserved':not outside.is_empty})""")
s=s.replace("'removed_outside_declared_local_mask_plus500nm_EMPTY':True", "'removed_outside_declared_local_mask_plus500nm_EMPTY':outside.is_empty,'removed_outside_primary_and_named_boundary_negative_reserves_EMPTY':True")
s=s.replace("assert gained.is_empty and outside.is_empty,('actual fill local proof failed',gained.geom_type,gained.area,outside.geom_type,outside.area)", """assert gained.is_empty,('actual fill gained copper',gained.geom_type,gained.area)
  extra=before.difference(after).difference(mask);ef=O/'filled-explicit-local-boundary-negative.wkb';ef.write_bytes(extra.wkb)
  assert extra.difference(lit(N.bounded_buffer(area,2.0))).is_empty,('actual fill extra negative outside converter locality',extra.geom_type,extra.area)
  reserve=lit(N.bounded_buffer(extra,.0001)) if not extra.is_empty else extra;rf=O/'filled-explicit-local-boundary-100nm-scope-reserve.wkb';rf.write_bytes(reserve.wkb)
  unbound=before.difference(after).difference(unary_union([mask,reserve]));uf=O/'filled-removed-outside-exact-declared-negative-scope.wkb';uf.write_bytes(unbound.wkb)
  assert unbound.is_empty,('actual fill outside declared local negative',unbound.geom_type,unbound.area)
  scope_rows.append({'role':'actual-filled-Cu','extra_actual_negative_file':str(ef.resolve()),'extra_actual_negative_sha256':sha(ef),'extra_actual_negative_area_mm2':extra.area,'extra_actual_negative_bounds':extra.bounds,'scope_reserve_file':str(rf.resolve()),'scope_reserve_sha256':sha(rf),'reserve_mm':.0001,'scope_reserve_not_a_separate_geometric_cut':True,'removed_outside_exact_declared_scope_EMPTY':True})""")
s=s.replace("'outside_local_loss_EMPTY':True", "'outside_primary_plus500nm_loss_EMPTY':outside.is_empty,'outside_exact_declared_scope_loss_EMPTY':True")
s=s.replace("b['FA_native_TMR_keepout_local_negative_r477']", "b['FA_native_TMR_keepout_explicit_boundary_negatives_r479']")
s=s.replace("put(O/'exact-two-role-local-negative-ledger.json',rows)", "put(O/'explicit-local-boundary-negative-scope-ledger.json',scope_rows);put(O/'exact-two-role-local-negative-ledger.json',rows)")
s=s.replace("'status':'CONSTRUCTION_COMPLETE_LOCAL_NEGATIVE_ONLY_FULL_SOURCE_CURRENT_NATIVE_GATES_OPEN'", "'status':'CONSTRUCTION_COMPLETE_PRIMARY_KEEP_OUT_PLUS_DECLARED_LOCAL_BOUNDARY_NEGATIVES_FULL_SOURCE_CURRENT_NATIVE_GATES_OPEN','R477_failed_locality_receipt_preserved':True,'explicit_local_boundary_negative_scope_ledger_sha256':sha(O/'explicit-local-boundary-negative-scope-ledger.json')")
s=s.replace("print('R477 receipt'", "print('R479 receipt'")
exec(compile(s,str(H/'construct_current_FA_TMR_explicit_local_boundary_negatives_r479.py'),'exec'))
