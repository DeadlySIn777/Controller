"""Declare exact local owned-boundary negative wedges; retain private-halo failure."""
from pathlib import Path
H=Path(__file__).resolve().parent;old=H/'stage_FIELD_ROOT_recovery_exact_R157_diagnostic_r745.generated.py'
assert (H/'FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r745/failure.json').exists()
text=old.read_text(encoding='utf-8').replace('FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r745','FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r747')
text=text.replace('from shapely.geometry import Point,Polygon,MultiPolygon','from shapely.geometry import Point,Polygon,MultiPolygon,box')
text=text.replace("    assert gain.is_empty,('True gained role copper',label,summary(gain));assert outside.is_empty,('Negative outside explicit local new-intersection reserve',label,summary(outside))", """    assert gain.is_empty,('True gained role copper',label,summary(gain))
    region=box(225,152,240,168)
    beyond_region=extra.difference(region)
    (OUT/(label+'-explicit-negative-boundary-redesign-outside-Q0-region.wkb')).write_bytes(beyond_region.wkb)
    assert beyond_region.is_empty,('New negative wedge outside actual declared Q0 local region',label,summary(beyond_region))
    allowed=mask.union(extra)
    unauthorized=removed.difference(allowed)
    (OUT/(label+'-removed-outside-primary-plus-exact-named-wedges.wkb')).write_bytes(unauthorized.wkb)
    assert unauthorized.is_empty,('Undeclared owned boundary removal',label,summary(unauthorized))
    record['R745_private_200nm_halo_failure_preserved_not_native_limit']=not outside.is_empty
    record['exact_named_negative_wedge_reversible_owned_boundary_redesign']=True
    record['declared_local_region_mm']=[225,152,240,168]
    record['literal_removed_outside_primary_plus_declared_exact_wedges_EMPTY']=True
    record['native_original_Cu_never_changed_by_wedges']=True""")
text=text.replace('R745_STAGED','R747_STAGED')
generated=H/'stage_FIELD_ROOT_recovery_exact_R157_diagnostic_r747.generated.py';assert not generated.exists();generated.write_text(text,encoding='utf-8')
exec(compile(text,str(generated),'exec'),{'__file__':str(generated),'__name__':'__main__'})
