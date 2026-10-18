"""Preserve R203; skip empty regions before reading a representative point."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_B3_exact_cross_layer_pair_r203.py').read_text(encoding='utf-8')
s=s.replace('B3-exact-cross-layer-pair-r203','B3-exact-cross-layer-pair-r206')
s=s.replace("for cp in sorted(polys(legal),key=lambda q:q.distance(source[ls])+q.distance(target[lt]))[:40]:\n     pts=","for cp in sorted([q for q in polys(legal) if not q.is_empty and q.area>1e-9],key=lambda q:q.distance(source[ls])+q.distance(target[lt]))[:40]:\n     pts=")
s=s.replace("for pt in pts:\n      xy=","for pt in pts:\n      if pt.is_empty:continue\n      xy=")
exec(compile(s,str(H/'construct_B3_exact_cross_layer_pair_r203.py'),'exec'))
