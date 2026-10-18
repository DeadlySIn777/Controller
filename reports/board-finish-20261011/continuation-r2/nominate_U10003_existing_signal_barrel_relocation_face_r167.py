"""Finite .6/.3 signal-barrel relocation screen near the real new ground port."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'diagnose_U10003_exact_paired_return_faces_r164.py';code=source.read_text()
code=code.replace('return-legal-faces-r164','signal-barrel-relocation-legal-faces-r167')
code=code.replace("NET='/motherboard_motors/FIELD_GND'","NET='/motherboard_do/DOA_FLT_N_FIELD'")
old="def polys(s):return [s]if s.geom_type=='Polygon'else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon']"
new="def polys(s):return [s]if s.geom_type=='Polygon'and not s.is_empty else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon'and not p.is_empty]"
assert code.count(old)==1;code=code.replace(old,new)
# Keep the source-ground contact proof as a ground proof; candidate net is the
# signal. The centre is the exact measured ground barrel, not an invented port.
code=code.replace("K.physical(full,NET,K.hole_context(full))","K.physical(full,'/motherboard_motors/FIELD_GND',K.hole_context(full))")
needle="rows=[];allcandidates=[]";assert code.count(needle)==1
code=code.replace(needle,"ports=[{'uuid':'EXACT_NEW_GROUND_PORT_CENTRE','x':216.04,'y':142.95}];rows=[];allcandidates=[]")
code=code.replace('pt.buffer(.95,quad_segs=256)','pt.buffer(1.25,quad_segs=256)')
code=code.replace('paired_candidate_max_radius_mm\':.95','paired_candidate_max_radius_mm\':1.25')
code=code.replace('.25+gap','.30+gap').replace('.1+.275','.15+.275').replace("(.2+v['drill'])/2","(.3+v['drill'])/2").replace('.25+.025','.30+.025').replace('.25+max','.30+max')
code=code.replace('site.buffer(.25,quad_segs=256).difference(site.buffer(.1,quad_segs=256))','site.buffer(.30,quad_segs=256).difference(site.buffer(.15,quad_segs=256))')
needle="if other==NET:continue\n   gap=max";assert code.count(needle)==1
code=code.replace(needle,"if other==NET:continue\n   if q['uuid'] in ('9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9'):continue # Only isolated new ground bands may receive an explicitly qualified local negative cut.\n   gap=max")
code=code.replace("'FINITE_EXACT_TRUE_CU_PAIRED_RETURN_FACE_NOMINATION_ONLY'","'FINITE_EXACT_EXISTING_SIGNAL_BARREL_RELOCATION_AXIS_NOMINATION_ONLY'")
code=code.replace("'original_or_new_Cu_deleted':False","'existing_barrel_UUID_proposed_to_move_only_after_complete_old_B_In3_contact_restoration':'1dfba07d-0355-46e7-abf9-ae2e8d1c9843','legacy_retained_barrel_diameter_drill_mm':[.6,.3],'exact_new_ground_two_band_local_negative_withdrawal_qualification':'OPEN','original_or_new_Cu_deleted':False")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
