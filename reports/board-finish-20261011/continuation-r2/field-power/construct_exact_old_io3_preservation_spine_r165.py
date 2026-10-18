"""Preserve failed R164; strictly inset reduced faces before coverage proof."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_exact_old_io3_preservation_spine_r164.py').read_text(encoding='utf-8')
s=s.replace('r164','r165').replace('R164','R165')
s=s.replace('part.buffer(-tol*1.01).simplify(tol,preserve_topology=True).intersection(part)','part.buffer(-tol*1.01).simplify(tol,preserve_topology=True).intersection(part).buffer(-.00002)')
exec(compile(s,str(H/'construct_exact_old_io3_preservation_spine_r164.py'),'exec'))
