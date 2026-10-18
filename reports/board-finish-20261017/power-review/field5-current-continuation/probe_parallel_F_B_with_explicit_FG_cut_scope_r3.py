"""A materially wider direct parallel path, permitting only explicit FG fill cuts."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
SOURCE=HERE/'probe_parallel_existing_barrel_corridors_r2.py'
s=SOURCE.read_text().replace("OUT=HERE/'parallel-fixed-native-copper-probe-r2'","OUT=HERE/'parallel-F-B-explicit-FG-cut-probe-r3'")
s=s.replace("roi=box(268,138,316,184)","roi=box(265,135,322,190)")
s=s.replace("for layer,width in(('F.Cu',.5),('B.Cu',.35),('In2.Cu',.5),('In3.Cu',.5)):","for layer,width in(('F.Cu',.5),('B.Cu',.5)):")
s=s.replace("if K.L.norm(q['net'])==net:continue", "if K.L.norm(q['net'])==net or(q['kind']=='fill'and K.L.norm(q['net'])=='/motherboard_motors/FIELD_GND'):continue")
s=s.replace("gap=.15 if q['domain']==domain else.6", "if q['kind']=='pad'or(q['kind']=='track'and q['source'].get('m')is not None):body=body.buffer(.005,quad_segs=128)\n            if q['kind']=='track'and q['source'].get('m')is None:\n                t=q['source'];body=LineString([t['a'],t['b']]).buffer((t['w']/2+1e-8)/math.cos(math.pi/512),quad_segs=128)\n            gap=.15 if q['domain']==domain else.6")
s=s.replace("'fixed_native_foreign_copper':True", "'fixed_all_native_discrete_and_non_FG_Cu':True,'only_FG_filled_Cu_may_need_explicit_negative_source_edits':True")
s=s.replace("'no_foreign_native_fill_cuts_proposed':True", "'only_explicit_FG_native_fill_cuts_permitted_but_not_yet_qualified':True")
s=s.replace("'roi_mm':[268,138,316,184]", "'roi_mm':[265,135,322,190]")
exec(compile(s,str(SOURCE),'exec'),globals())
