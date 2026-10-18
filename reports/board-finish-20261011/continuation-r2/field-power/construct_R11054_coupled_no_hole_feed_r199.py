"""Preserve R198 raw lookup failure; normalize only the graph query, never output."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_R11054_coupled_no_hole_feed_r198.py').read_text(encoding='utf-8').replace('r198','r199').replace('R198','R199')
s=s.replace('groups=F.graph(c,fieldnet)','groups=F.graph(c,C.norm(fieldnet))')
exec(compile(s,str(H/'construct_R11054_coupled_no_hole_feed_r198.py'),'exec'))
