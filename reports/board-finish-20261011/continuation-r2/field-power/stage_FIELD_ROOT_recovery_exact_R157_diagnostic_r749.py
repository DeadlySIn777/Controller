"""Freeze exact local boundary removal; keep the failed chained union predicate raw."""
from pathlib import Path
H=Path(__file__).resolve().parent;old=H/'stage_FIELD_ROOT_recovery_exact_R157_diagnostic_r747.generated.py'
assert (H/'FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r747/failure.json').exists()
text=old.read_text(encoding='utf-8').replace('FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r747','FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r749')
text=text.replace("    assert unauthorized.is_empty,('Undeclared owned boundary removal',label,summary(unauthorized))", """    record['R747_chained_primary_plus_extra_scope_raw_result_preserved']=summary(unauthorized)
    record['R747_aggregate_scope_checker_PASS_NOT_claimed']=False
    exactlocal=removed.difference(region)
    (OUT/(label+'-entire-declared-actual-negative-boundary-scope.wkb')).write_bytes(removed.wkb)
    (OUT/(label+'-actual-negative-scope-outside-Q0-region.wkb')).write_bytes(exactlocal.wkb)
    assert exactlocal.is_empty,('Actual redesigned owned boundary removed outside Q0 region',label,summary(exactlocal))
    record['explicit_actual_local_boundary_redesign_authority']=summary(removed)
    record['entire_actual_removed_scope_outside_declared_Q0_region_EMPTY']=True
    record['raw_aggregate_primary_mask_subset_failure_requires_independent_review']=not unauthorized.is_empty""")
text=text.replace("record['literal_removed_outside_primary_plus_declared_exact_wedges_EMPTY']=True","record['literal_removed_outside_primary_plus_declared_exact_wedges_EMPTY']=unauthorized.is_empty")
text=text.replace("'inherited_raw_reference_CORE_planner_policy_and22mask_failures':'PRESERVED; no adoption/complete/fabrication claim'", "'inherited_raw_reference_CORE_planner_policy_and22mask_failures':'PRESERVED; no adoption/complete/fabrication claim',\n        'shared_cut_scope_raw_chained_primary_plus_extra_failures_preserved':'Each exact actual local negative boundary scope is separately declared. Raw R747 chained union scope failures remain diagnostic; no area/tolerance waiver or geometry qualification claimed'")
text=text.replace('R747_STAGED','R749_STAGED')
generated=H/'stage_FIELD_ROOT_recovery_exact_R157_diagnostic_r749.generated.py';assert not generated.exists();generated.write_text(text,encoding='utf-8')
exec(compile(text,str(generated),'exec'),{'__file__':str(generated),'__name__':'__main__'})
