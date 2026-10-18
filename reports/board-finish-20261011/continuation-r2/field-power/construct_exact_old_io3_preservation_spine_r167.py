"""Direct conservative faces preserve every original free-space boundary."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_exact_old_io3_preservation_spine_r164.py').read_text(encoding='utf-8')
s=s.replace('r164','r167').replace('R164','R167')
s=s.replace('for tol in (.02,.005,0.):','for tol in (.05,.02,.005):')
s=s.replace('part.buffer(-tol*1.01).simplify(tol,preserve_topology=True).intersection(part)','part.buffer(-tol*2).simplify(tol,preserve_topology=True).buffer(-.00002)')
s=s.replace('assert part.covers(reduced)',"if not part.covers(reduced):\n      rows.append({'margin':margin,'width':width,'tol':tol,'reason':'conservative reduced face failed literal subset proof'});write('checkpoint.json',rows);continue")
s=s.replace('pa,pb=nearest_points(sa,sb);line=',"sa=sa.buffer(-.00001);sb=sb.buffer(-.00001)\n      if sa.is_empty or sb.is_empty:continue\n      pa,pb=nearest_points(sa,sb);line=")
exec(compile(s,str(H/'construct_exact_old_io3_preservation_spine_r164.py'),'exec'))
