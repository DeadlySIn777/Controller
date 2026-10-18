"""Nominate compliant A return on the exact R187 coupled Cu scene."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'diagnose_U10003_exact_paired_return_faces_r164.py';code=source.read_text()
code=code.replace('return-legal-faces-r164','old-A-return-after-coupled-clock-ground-faces-r188')
code=code.replace('U10003-sparse-current-ground-fault-construction-r153/model.pkl','U10003-preserved-branch-exact-two-port-reference-construction-r176/model.pkl').replace('2d7b4c1ff29121e909602f9d76c89c02b4f7d8e5bb6d8a3f3bf5fad7fa1fd1d8','c13b478b0cea7b09a510c221913d3a4d0774fcc74042605c17d69b35b37a9d20')
old="def polys(s):return [s]if s.geom_type=='Polygon'else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon']";new="def polys(s):return [s]if s.geom_type=='Polygon'and not s.is_empty else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon'and not p.is_empty]";assert code.count(old)==1;code=code.replace(old,new)
needle=" print('R164_BUILD_ACTUAL_HARD_CU',flush=True);records,trees=F.build({**h,'zones':[]})";assert code.count(needle)==1
replacement="""
 dp=H/'U10003-exact-clock-fault-coupled-ground-return-nomination-r187/proposed-sparse-delta.pkl';d=pickle.loads(dp.read_bytes());rr=H/'U10003-exact-clock-fault-coupled-ground-return-nomination-r187/receipt.json';assert sha(rr)=='47aa48549ef51e3543d32caa2f2c045f155793c94488c27f1716f9ac16434ba0'
 delete={t['uuid']for t in d['delete_original_tracks']}|{d['replace_only_unadopted_ground_stub']};via=d['replace_only_unadopted_ground_barrel'];roles=set(d['withdraw_only_unadopted_reference_roles'])
 h={**h,'tracks':[t for t in h['tracks']if t['uuid']not in delete]+d['new_tracks'],'vias':[v for v in h['vias']if v['uuid']!=via['uuid']]+[via]}
 full={**full,'tracks':h['tracks'],'vias':h['vias'],'zones':[q for q in full['zones']if q['uuid']not in roles]};z=[q for q in z if q['uuid']not in roles]
 ports=[next(v for v in h['vias']if v['uuid']=='2938cbdd-1d38-4238-9455-504b30f06e5e')]
 print('R188_BUILD_EXACT_R187_CU_SCENE',flush=True);records,trees=F.build({**h,'zones':[]})
"""
code=code.replace(needle,replacement)
code=code.replace('near=legal.intersection(pt.buffer(.95,quad_segs=256))','near=legal.intersection(pt.buffer(1.0,quad_segs=256)).difference(pt.buffer(.90,quad_segs=256))')
code=code.replace("'paired_candidate_max_radius_mm':.95","'saved_operator_return_window_mm':[.90,1.0]")
code=code.replace("'original_or_new_Cu_deleted':False","'exact_R187_clock_fault_ground_delta_sha256':sha(dp),'scene_is_nomination_only_not_an_emitted_board':True,'full_new_ground_source_reference_current_native_gates':'OPEN'")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
