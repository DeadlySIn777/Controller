"""Preserve r3 source-line container mismatch; compare exact native coordinate values."""
from pathlib import Path
import py_compile
here=Path(__file__).resolve().parent
source=(here/'audit_ao1_reference_coupled_mon_r3.py').read_text()
source=source.replace("path.stem+'-independent-mon-r3.json'", "path.stem+'-independent-mon-r4.json'")
source=source.replace("path.stem+'-independent-reference-gaps-mon-r3'", "path.stem+'-independent-reference-gaps-mon-r4'")
source=source.replace("old_mon['a']!=(373.75,129.549999) or old_mon['b']!=(369.35,125.15)", "tuple(old_mon['a'])!=(373.75,129.549999) or tuple(old_mon['b'])!=(369.35,125.15)")
target=here/'audit_ao1_reference_coupled_mon_r4.py';assert not target.exists();target.write_text(source)
py_compile.compile(str(target),doraise=True,cfile=str(here/'ao1-independent-mon-r4-syntax-only.pyc'))
print('Fresh independent MON R4 syntax PASS; list/tuple identity fix only.')
