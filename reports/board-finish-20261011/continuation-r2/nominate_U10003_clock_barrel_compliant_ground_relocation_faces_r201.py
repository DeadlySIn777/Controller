"""Ordinary existing clock barrel relocation around its actual source return."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'diagnose_U10003_exact_paired_return_faces_r164.py';code=source.read_text()
code=code.replace('return-legal-faces-r164','clock-barrel-compliant-ground-relocation-faces-r201')
code=code.replace("NET='/motherboard_motors/FIELD_GND'","NET='/motherboard_do/DOA_SCLK_FIELD'")
code=code.replace('U10003-sparse-current-ground-fault-construction-r153/model.pkl','U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl').replace('2d7b4c1ff29121e909602f9d76c89c02b4f7d8e5bb6d8a3f3bf5fad7fa1fd1d8','dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5')
old="def polys(s):return [s]if s.geom_type=='Polygon'else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon']";new="def polys(s):return [s]if s.geom_type=='Polygon'and not s.is_empty else[p for p in getattr(s,'geoms',[])if p.geom_type=='Polygon'and not p.is_empty]";assert code.count(old)==1;code=code.replace(old,new)
needle=" print('R164_BUILD_ACTUAL_HARD_CU',flush=True);records,trees=F.build({**h,'zones':[]})";assert code.count(needle)==1
replacement="""
 exact_old_clock=next(v for v in h['vias']if v['uuid']=='1f45e002-4f40-4087-bbed-3be260272d8f');assert(exact_old_clock['d'],exact_old_clock['drill'])==(.5,.2)
 h={**h,'vias':[v for v in h['vias']if v['uuid']!=exact_old_clock['uuid']]};full={**full,'vias':h['vias']}
 paired_ground=next(v for v in h['vias']if v['uuid']=='ef759308-e664-5253-b016-ff17794eac74');ports=[paired_ground]
 print('R201_BUILD_EXACT_CLOCK_RELOCATION_NOMINATION_SCENE',flush=True);records,trees=F.build({**h,'zones':[]})
""";code=code.replace(needle,replacement)
code=code.replace('K.physical(full,NET,K.hole_context(full))',"K.physical(full,'/motherboard_motors/FIELD_GND',K.hole_context(full))")
needle="if other==NET:continue\n   gap=max";assert code.count(needle)==1
code=code.replace(needle,"if other==NET:continue\n   if q['uuid']in('bde7a0cf-1ad7-5a04-b956-9f8848bb3f2a','9fe010df-73cf-5bfb-9f7a-bd227b701c3e','ee0efe05-1705-587c-ac86-49b1a7885ef9'):assert other=='/motherboard_motors/FIELD_GND';continue # only explicit old/new FG role negative ledger may follow\n   gap=max")
needle="for v in h['vias']:add(Point(v['x'],v['y']),(.2+v['drill'])/2+.275+.000020,'ACTUAL_EVERY_DRILL_PITCH',v['uuid'])";assert code.count(needle)==1;code=code.replace(needle,"for v in h['vias']:add(Point(v['x'],v['y']),max((.2+v['drill'])/2+.275+.000020,.825),'ACTUAL_EVERY_DRILL_AND_GLOBAL_PITCH',v['uuid'])")
code=code.replace('near=legal.intersection(pt.buffer(.95,quad_segs=256))','near=legal.intersection(pt.buffer(1.0,quad_segs=256)).difference(pt.buffer(.90,quad_segs=256))').replace("'paired_candidate_max_radius_mm':.95","'saved_operator_return_window_mm':[.90,1.0]")
code=code.replace("'original_or_new_Cu_deleted':False","'original_or_new_Cu_deleted':False,'exact_existing_clock_barrel_to_relocate':exact_old_clock,'exact_actual_ground_pair_UUID':paired_ground['uuid'],'all_old_native_clock_F_B_contacts_raw_names_dimensions_masks_and_every_source_require_fresh_reconstruction':True,'bound_FG_only_local_negative_profiles_require_full_source_reference_gates':True,'global_new_pitch_guard_mm':.825")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
