"""Keep exact required guard; do not erode fixed retained Point endpoints."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_R11054_coupled_no_hole_feed_r198.py').read_text(encoding='utf-8').replace('r198','r200').replace('R198','R200').replace('groups=F.graph(c,fieldnet)','groups=F.graph(c,C.norm(fieldnet))')
s=s.replace("st=part.buffer(-.000002).intersection(start);en=part.buffer(-.000002).intersection(end)","st=(part if start.geom_type=='Point' else part.buffer(-.000002)).intersection(start);en=(part if end.geom_type=='Point' else part.buffer(-.000002)).intersection(end)")
s=s.replace("if not options:return None","if net==aux:print('R200 AUX_FREE',margin,free.covers(start),free.covers(end),len(options),flush=True)\n  if not options:return None")
exec(compile(s,str(H/'construct_R11054_coupled_no_hole_feed_r198.py'),'exec'))
