"""Expanded half-mm physical search at the real upstream source pad ports."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'probe_parallel_F_B_with_explicit_FG_cut_scope_r3.py').read_text().replace("'parallel-F-B-explicit-FG-cut-probe-r3'","'parallel-F-B-actual-source-pad-probe-r5'")
s=s.replace('roi=box(265,135,322,190)','roi=box(250,120,350,210)')
s=s.replace("put('status.json',{'phase':'HOST_FIXED_COPPER_CORRIDOR_PROBE'", "port=('L11003','2')if layer=='F.Cu'else('C11081','1');pad=next(p for p in g['pads']if(p['ref'],p['num'])==port);source_pad=unary_union(K.L.poly(pad['layers'][layer]));start=tuple(source_pad.centroid.coords)[0]\n        put('status.json',{'phase':'HOST_FIXED_COPPER_CORRIDOR_PROBE'")
s=s.replace("'existing_source_barrel':T.T2", "'actual_upstream_source_pad_port':'.'.join(port),'source_position_mm':list(start),'existing_source_barrel':T.T2")
s=s.replace("'roi_mm':[265,135,322,190]","'roi_mm':[250,120,350,210]")
exec(compile(s,str(HERE/'probe_parallel_F_B_with_explicit_FG_cut_scope_r3.py'),'exec'),globals())
