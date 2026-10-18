"""Named FA controlling-edge negative redesign, original native copper exact."""
from pathlib import Path
H=Path(__file__).resolve().parent;old=H/'stage_FIELD_ROOT_recovery_exact_R157_diagnostic_r749.generated.py'
assert (H/'FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r749/failure.json').exists()
text=old.read_text(encoding='utf-8').replace('FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r749','FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r751')
text=text.replace('    region=box(225,152,240,168)', """    region=box(221,152,240,168) if label.startswith('7ef3cb5e-') else box(225,152,240,168)
    record['R749_FA_controlling_old_edge_private_Q0_bound_failure_preserved']=label.startswith('7ef3cb5e-')
    record['named_FA_only_existing_owned_boundary_redesign_extent_mm']=[221,152,240,168] if label.startswith('7ef3cb5e-') else None
    record['exact_negative_old_owned_boundary_wedge_WKB_authority_file']=str((OUT/(label+'-extra-negative-new-intersection-wedges.wkb')).resolve())""")
text=text.replace("record['declared_local_region_mm']=[225,152,240,168]", "record['declared_local_region_mm']=list(region.bounds)")
text=text.replace('R749_STAGED','R751_STAGED')
generated=H/'stage_FIELD_ROOT_recovery_exact_R157_diagnostic_r751.generated.py';assert not generated.exists();generated.write_text(text,encoding='utf-8')
exec(compile(text,str(generated),'exec'),{'__file__':str(generated),'__name__':'__main__'})
