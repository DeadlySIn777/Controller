"""Freeze a standalone source for the exact R561 checks.

The prior wrapper's missing Decimal global is recorded as a checker failure.
All checks and actual native inputs stay the same; the required import is
declared in the generated checker itself, without inherited wrapper globals.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
p=H/'complete_TMR_R218_actual_native_empty_fill_exact_predicate_r561.py'
text=p.read_text(encoding='utf-8')
end="exec(compile(code,str(H/'audit_TMR_R218_actual_native_drilled_source_r553.py'),'exec'))"
assert end in text
ns={'__file__':str(p)}
exec(compile(text.replace(end,''),str(p),'exec'),ns)
code=ns['code']
code=code.replace("OUT=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r561'","OUT=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r563'")
assert 'from decimal import Decimal'not in code
code=code.replace('import sys,json,pickle,hashlib,time,re,collections,copy','import sys,json,pickle,hashlib,time,re,collections,copy\nfrom decimal import Decimal')
target=H/'audit_native_TMR_R218_resolved_r563.py';assert not target.exists();target.write_text(code,encoding='utf-8')
print(str(target.resolve()))
