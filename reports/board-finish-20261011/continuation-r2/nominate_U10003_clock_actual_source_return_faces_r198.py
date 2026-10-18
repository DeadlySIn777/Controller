"""Finite ordinary clock-return nomination with the complete current pitch rule."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'diagnose_U10003_exact_paired_return_faces_r164.py';code=source.read_text()
code=code.replace('return-legal-faces-r164','clock-current-source-pitch-bound-return-faces-r198')
code=code.replace('U10003-sparse-current-ground-fault-construction-r153/model.pkl','U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl').replace('2d7b4c1ff29121e909602f9d76c89c02b4f7d8e5bb6d8a3f3bf5fad7fa1fd1d8','dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5')
old="def polys(s):return [s]if s.geom_type=='Polygon'else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon']";new="def polys(s):return [s]if s.geom_type=='Polygon'and not s.is_empty else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon'and not p.is_empty]";assert code.count(old)==1;code=code.replace(old,new)
needle=" print('R164_BUILD_ACTUAL_HARD_CU',flush=True);records,trees=F.build({**h,'zones':[]})";assert code.count(needle)==1;code=code.replace(needle," ports=[next(v for v in h['vias']if v['uuid']=='1f45e002-4f40-4087-bbed-3be260272d8f')];print('R198_BUILD_ACTUAL_CANDIDATE_HARD_CU',flush=True);records,trees=F.build({**h,'zones':[]})")
needle="for v in h['vias']:add(Point(v['x'],v['y']),(.2+v['drill'])/2+.275+.000020,'ACTUAL_EVERY_DRILL_PITCH',v['uuid'])";assert code.count(needle)==1;code=code.replace(needle,"for v in h['vias']:add(Point(v['x'],v['y']),max((.2+v['drill'])/2+.275+.000020,.825),'ACTUAL_EVERY_DRILL_AND_GLOBAL_PITCH',v['uuid'])")
code=code.replace('near=legal.intersection(pt.buffer(.95,quad_segs=256))','near=legal.intersection(pt.buffer(1.0,quad_segs=256)).difference(pt.buffer(.90,quad_segs=256))').replace("'paired_candidate_max_radius_mm':.95","'saved_operator_return_window_mm':[.90,1.0]")
code=code.replace("'original_or_new_Cu_deleted':False","'original_or_new_Cu_deleted':False,'global_new_via_pitch_guard_mm':.825,'prospective_current_source_graph_only_actual_native_after_fill_open':True")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
