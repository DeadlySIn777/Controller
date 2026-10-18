"""Preserve R219 reader failure; use the exact inventory record field names."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'inspect_REG_loss_geometry_r219.py').read_text(encoding='utf-8')
s=s.replace('REG-exact-discrete-and-IO3-interaction-r219','REG-exact-discrete-and-IO3-interaction-r220')
s=s.replace("Point(x['at']).buffer(x['size']/2,quad_segs=128)","P.bounded_disk(x,x['d']/2)")
s=s.replace("x['start']","x['a']").replace("x['end']","x['b']").replace("x['width']","x['w']")
s=s.replace("x.get('at',x.get('start'))","[x['x'],x['y']] if kind=='via' else x['a']")
s=s.replace("Point(x['at'])","Point(x['x'],x['y'])")
s=s.replace("'In1.Cu' not in orig['fills']","q['layer'] not in orig['fills']").replace("orig['fills']['In1.Cu']","unary_union(C.poly(orig['fills'][q['layer']]))")
s=s.replace("'In1.Cu'","q['layer']") if False else s
exec(compile(s,str(H/'inspect_REG_loss_geometry_r219.py'),'exec'))
