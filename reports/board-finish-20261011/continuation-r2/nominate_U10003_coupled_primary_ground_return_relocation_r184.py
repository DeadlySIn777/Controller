"""Screen relocation of the exact unadopted primary ground barrel and stub."""
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'diagnose_U10003_exact_paired_return_faces_r164.py';code=source.read_text()
code=code.replace('return-legal-faces-r164','new-signal-port-coupled-primary-ground-relocation-faces-r184')
code=code.replace('U10003-sparse-current-ground-fault-construction-r153/model.pkl','U10003-preserved-branch-exact-two-port-reference-construction-r176/model.pkl').replace('2d7b4c1ff29121e909602f9d76c89c02b4f7d8e5bb6d8a3f3bf5fad7fa1fd1d8','c13b478b0cea7b09a510c221913d3a4d0774fcc74042605c17d69b35b37a9d20')
old="def polys(s):return [s]if s.geom_type=='Polygon'else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon']"
new="def polys(s):return [s]if s.geom_type=='Polygon'and not s.is_empty else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon'and not p.is_empty]"
assert code.count(old)==1;code=code.replace(old,new)
needle=" print('R164_BUILD_ACTUAL_HARD_CU',flush=True);records,trees=F.build({**h,'zones':[]})"
assert code.count(needle)==1
replacement="""
 import uuid
 own_via=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-U10003-field-ground-r149/barrel'));own_stub=str(uuid.uuid5(uuid.NAMESPACE_URL,'controller-U10003-field-ground-r149/Bstub'))
 assert len([v for v in h['vias']if v['uuid']==own_via])==1
 assert len([t for t in h['tracks']if t['uuid']==own_stub])==1
 roles={'9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9'}
 h={**h,'tracks':[t for t in h['tracks']if t['uuid']!=own_stub],'vias':[v for v in h['vias']if v['uuid']!=own_via]}
 full={**full,'tracks':[t for t in full['tracks']if t['uuid']!=own_stub],'vias':[v for v in full['vias']if v['uuid']!=own_via],'zones':[q for q in full['zones']if q['uuid']not in roles]}
 z=[q for q in z if q['uuid']not in roles]
 signal=next(v for v in h['vias']if v['uuid']=='7f2431b3-4dcd-5b17-88ce-8aae4c3d66d4');ports=[signal]
 print('R184_BUILD_EXACT_UNADOPTED_GROUND_WITHDRAWAL_SCENE',own_via,own_stub,flush=True);records,trees=F.build({**h,'zones':[]})
"""
code=code.replace(needle,replacement)
code=code.replace('near=legal.intersection(pt.buffer(.95,quad_segs=256))','near=legal.intersection(pt.buffer(1.0,quad_segs=256)).difference(pt.buffer(.90,quad_segs=256))')
code=code.replace("'paired_candidate_max_radius_mm':.95","'saved_operator_return_window_mm':[.90,1.0]")
code=code.replace("'original_or_new_Cu_deleted':False","'withdrawal_is_nomination_scene_only':True,'exact_unadopted_ground_barrel':own_via,'exact_unadopted_ground_stub':own_stub,'exact_two_unadopted_reference_roles':sorted(roles),'all_original_native_Cu_untouched':True,'new_source_plane_and_actual_ground_stub_reconnection_gates':'OPEN'")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
