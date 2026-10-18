"""Preserve r17 append failure; append only new items beyond retained initial copper."""
from pathlib import Path
import py_compile
here=Path(__file__).resolve().parent
source=(here/'ao1_reference_coupled_r17.py').read_text()
source=source.replace("OUT=HERE/'ao1-reference-coupled-r17.json'", "OUT=HERE/'ao1-reference-coupled-r18.json'")
source=source.replace('ao1-r17-', 'ao1-r18-')
needle='I.append(initial,new,identity)';assert source.count(needle)==2
source=source.replace(needle,'I.append(initial,{u:ch for u,ch in new.items() if u not in preserved},identity)')
target=here/'ao1_reference_coupled_r18.py';assert not target.exists();target.write_text(source)
py_compile.compile(str(target),doraise=True,cfile=str(here/'ao1-reference-r18-syntax-only.pyc'))
print('Fresh R18 syntax PASS; no duplicated initial retained copper.')
