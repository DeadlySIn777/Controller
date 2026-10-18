"""Correct intersection search nm→mm scaling; preserve failed R743."""
from pathlib import Path
H=Path(__file__).resolve().parent;old=H/'stage_FIELD_ROOT_recovery_exact_R157_diagnostic_r743.py'
assert (H/'FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r743/failure.json').exists()
text=old.read_text(encoding='utf-8').replace('FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r743','FIELD-ROOT-Q0-DIC-DI6-exact-R157-native-diagnostic-stage-r745')
text=text.replace('(.000000002,.000000005,.000000010,.000000020,.000000050,.000000100)','(.000002,.000005,.000010,.000020,.000050,.000100)')
text=text.replace('mask.buffer(.000000200,quad_segs=64)','mask.buffer(.000200,quad_segs=64)')
text=text.replace('R743_STAGED','R745_STAGED')
generated=H/'stage_FIELD_ROOT_recovery_exact_R157_diagnostic_r745.generated.py';assert not generated.exists();generated.write_text(text,encoding='utf-8')
exec(compile(text,str(generated),'exec'),{'__file__':str(generated),'__name__':'__main__'})
