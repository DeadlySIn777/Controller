"""Correct the R359 metadata UUID inventory using its bound 96 role rows."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'construct_U10003_sparse_current_ground_fault_r151.py';code=source.read_text()
code=code.replace('construction-r151','construction-r152')
needle='q=copy.deepcopy(q0);PS.restore_bound_generated_precision_states(b,q)';assert code.count(needle)==1
replacement="""q=copy.deepcopy(q0);rows=b['generated_precision_state_ledger'];bound={r['new_generated_UUID']for r in rows};assert bound=={z['uuid']for z in q};assert len(rows)==len(q)*2 and {(r['new_generated_UUID'],r['role'])for r in rows}=={(z['uuid'],role)for z in q for role in('shape','zone_outline_shape')};original_expected=list(b['restored_generated_grid_UUIDs']);b['restored_generated_grid_UUIDs']=sorted(bound);PS.restore_bound_generated_precision_states(b,q);put(OUT/'R359-metadata-only-bound-UUID-inventory-repair.json',{'exact_parent_model_sha256':sha(mp),'original_expected_UUIDs':original_expected,'validated_complete_generated_role_row_count':len(rows),'repaired_expected_UUIDs':sorted(bound),'all_existing_bound_WKB_exact':True,'no_coordinate_or_native_snap':True})"""
code=code.replace(needle,replacement);compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
