"""Correct the pad-hole local variable in the frozen read-only R406 derivation."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'diagnose_actual_CORE5_new_In2_source_port_reachability_r406.py').read_text(encoding='utf-8').replace('r406','r407').replace('R406','R407')
old='old="if sh.intersects(roi):obstacles.append(sh.buffer(.905005,quad_segs=64))"\nnew="if sh.intersects(roi):\\n     expanded=sh.buffer(.905005,quad_segs=64);obstacles.append(expanded);allFixed.append(expanded)"'
new='old="if s.intersects(roi):obstacles.append(s.buffer(.905005,quad_segs=64))"\nnew="if s.intersects(roi):\\n     expanded=s.buffer(.905005,quad_segs=64);obstacles.append(expanded);allFixed.append(expanded)"'
assert s.count(old)==1;s=s.replace(old,new);exec(compile(s,str(__file__),'exec'),{'__name__':'__main__','__file__':str(__file__)})
