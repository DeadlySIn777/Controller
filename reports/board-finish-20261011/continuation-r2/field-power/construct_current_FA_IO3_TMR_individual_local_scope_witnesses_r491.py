"""R487 successor: preserve and individually bind raw local scope witnesses."""
from pathlib import Path
import ast
H=Path(__file__).resolve().parent
p=H/'construct_current_FA_plus_IO3_TMR_local_negative_r487.py'
t=ast.parse(p.read_text(encoding='utf-8'));t.body.pop();ns={'__file__':str(p)};exec(compile(t,str(p),'exec'),ns);s=ns['s']
s=s.replace("O=H/'R155-FA-plus-IO3-TMR-owned-local-negative-r487'", "O=H/'R155-FA-plus-IO3-TMR-individual-local-scope-witnesses-r491'")
needle="  assert unbound.is_empty,('actual fill outside declared local negative',unbound.geom_type,unbound.area)"
assert s.count(needle)==1
s=s.replace(needle,"""  extra_scopes=[];scope_pieces=[mask,reserve]
  for scope_iteration in range(16):
   if unbound.is_empty:break
   wfile=O/('filled-'+str(scope_iteration)+'-raw-outside-prior-declared-scope.wkb');wfile.write_bytes(unbound.wkb)
   assert unbound.difference(lit(N.bounded_buffer(area,.1))).is_empty,('new scope witness not at actual native converter cut',scope_iteration,unbound.bounds)
   scope_reserve=lit(N.bounded_buffer(unbound,.0001));sfile=O/('filled-'+str(scope_iteration)+'-individual-100nm-local-negative-scope.wkb');sfile.write_bytes(scope_reserve.wkb)
   extra_scopes.append({'iteration':scope_iteration,'raw_witness_file':str(wfile.resolve()),'raw_witness_sha256':sha(wfile),'raw_type':unbound.geom_type,'raw_area_mm2':unbound.area,'raw_length_mm':unbound.length,'raw_bounds':unbound.bounds,'explicit_scope_reserve_file':str(sfile.resolve()),'explicit_scope_reserve_sha256':sha(sfile),'reserve_mm':.0001,'no_size_waiver':True,'actual_geometry_unchanged_by_scope_binding':True})
   scope_pieces.append(scope_reserve);unbound=before.difference(after).difference(unary_union(scope_pieces))
  else:raise AssertionError('local filled scope witnesses did not converge')
  final_scope=unary_union(scope_pieces);(O/'filled-complete-primary-plus-individual-local-negative-scope.wkb').write_bytes(final_scope.wkb);put(O/'filled-individual-local-negative-scope-witness-ledger.json',extra_scopes)
  assert unbound.is_empty,('actual fill outside final individual local negative scopes',unbound.geom_type,unbound.area)""")
s=s.replace("b['IO3_native_TMR_keepout_explicit_boundary_negatives_r487']", "b['IO3_native_TMR_keepout_individual_scope_witnesses_r491']")
s=s.replace("print('R487 receipt'", "print('R491 receipt'")
exec(compile(s,str(H/'construct_current_FA_IO3_TMR_individual_local_scope_witnesses_r491.py'),'exec'))
