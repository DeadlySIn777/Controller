"""Preserve r15 diagnostic failure; fix optional physical-hole key reporting."""
from pathlib import Path
import py_compile
here=Path(__file__).resolve().parent
source=(here/'diagnose_ao1_mon_reference_r15.py').read_text()
source=source.replace("OUT=HERE/'ao1-mon-reference-diagnostic-r15.json'", "OUT=HERE/'ao1-mon-reference-diagnostic-r16.json'")
source=source.replace('ao1-mon-r15-', 'ao1-mon-r16-')
source=source.replace("'key':list(row['key'])", "'key':list(row.get('key',('physical-hole',row['uuid'])))")
source=source.replace("region=box(367,124,377,132)", "print(json.dumps({'early_fill_errors':len(fillerrors)}),flush=True)\n    region=box(367,124,377,132)")
target=here/'diagnose_ao1_mon_reference_r16.py';assert not target.exists();target.write_text(source)
py_compile.compile(str(target),doraise=True,cfile=str(here/'ao1-mon-diagnostic-r16-syntax-only.pyc'))
print('Fresh diagnostic R16 syntax PASS; exact physical-hole UUID fallback.')
