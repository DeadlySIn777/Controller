"""Preserved R261 successor: finite receipt encoding and actual drilled Cu."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'construct_T4_R7_sparse_R250_diagnostic_r261.py').read_text()
assert s.count("'novel_body_gap_mm':novgap,")==1
s=s.replace("'novel_body_gap_mm':novgap,","'novel_body_gap_mm':novgap if novgap != float('inf') else None,")
old="body=Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2);gap=body.difference(sr[t['layer']]);"
new="body=Z.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2); nativeholes,nativetree=newctx; body=body.difference(unary_union([nativeholes[int(i)]for i in nativetree.query(body,predicate='intersects')]+[Z.bounded_disk(v,v['drill']/2+.00000002)for v in d['vias']if Z.bounded_disk(v,v['drill']/2+.00000002).intersects(body)]));gap=body.difference(sr[t['layer']]);"
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('r261','r262').replace('R261','R262')
exec(compile(s,str(__file__),'exec'))
