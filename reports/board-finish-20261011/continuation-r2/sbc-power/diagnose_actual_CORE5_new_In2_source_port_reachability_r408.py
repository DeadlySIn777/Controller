"""Use continuation-root imports for the saved closed-source reachability audit."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'diagnose_actual_CORE5_new_In2_source_port_reachability_r406.py').read_text(encoding='utf-8').replace('r406','r408').replace('R406','R408')
old='old="if sh.intersects(roi):obstacles.append(sh.buffer(.905005,quad_segs=64))"\nnew="if sh.intersects(roi):\\n     expanded=sh.buffer(.905005,quad_segs=64);obstacles.append(expanded);allFixed.append(expanded)"'
new='old="if s.intersects(roi):obstacles.append(s.buffer(.905005,quad_segs=64))"\nnew="if s.intersects(roi):\\n     expanded=s.buffer(.905005,quad_segs=64);obstacles.append(expanded);allFixed.append(expanded)"'
assert s.count(old)==1;s=s.replace(old,new)
needle='s=s[:start]+replacement+s[end:]';assert s.count(needle)==1;s=s.replace(needle,needle+'\ns=s.replace("H=Path(__file__).resolve().parent\\n","H=Path(__file__).resolve().parent.parent\\n")')
exec(compile(s,str(__file__),'exec'),{'__name__':'__main__','__file__':str(__file__)})
