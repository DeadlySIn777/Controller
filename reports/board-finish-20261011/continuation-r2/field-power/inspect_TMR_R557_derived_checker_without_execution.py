"""Read-only source expansion for the preserved failed checker."""
from pathlib import Path
H=Path(__file__).resolve().parent
p=H/'audit_TMR_R218_actual_native_drilled_source_r557.py'
s=p.read_text(encoding='utf-8')
old="exec(compile(code,str(prior),'exec'))"
new="print('\\n'.join(str(i+1)+':'+x for i,x in enumerate(code.splitlines()) if 112<=i<=140))"
assert old in s
exec(compile(s.replace(old,new),str(p),'exec'),{'__file__':str(p)})
