"""Fix the bounded MON endpoint window, preserving r12 and exact owned copper."""
from pathlib import Path
import py_compile
here=Path(__file__).resolve().parent
source=(here/'ao1_reference_coupled_r12.py').read_text()
source=source.replace("OUT=HERE/'ao1-reference-coupled-r12.json'", "OUT=HERE/'ao1-reference-coupled-r13.json'")
source=source.replace('WINDOW=box(369.5,125,379,133)', 'WINDOW=box(368.8,124.7,379,133)')
source=source.replace('ao1-r12-', 'ao1-r13-')
source=source.replace('strict_pairs=pairs[:120]', 'strict_pairs=[] # Fixed exact promising r12 case; no repeat prefix sweep.')
old="nominations=[((373.4,128.3),(374.225,128.4)),((373.4,128.3),(374.2,128.5)),((373.4,128.3),(374.25,128.5)),((373.4,128.3),(374.3,128.6)),((374.0,129.0),(373.4,128.3))]"
assert old in source
source=source.replace(old, 'nominations=[((374.0,129.0),(373.4,128.3))]')
target=here/'ao1_reference_coupled_r13.py';assert not target.exists();target.write_text(source)
py_compile.compile(str(target),doraise=True,cfile=str(here/'ao1-reference-r13-syntax-only.pyc'))
print('Fresh R13 syntax PASS; MON exact source endpoint included in bounded window.')
