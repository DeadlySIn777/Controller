"""Joint clock return sites with only the three unadopted detour legs withdrawn."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_U10003_clock_actual_source_return_faces_r198.py';code=source.read_text().replace('r198','r200')
anchor="compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))";assert code.count(anchor)==1
extra="""
needle="ports=[next(v for v in h['vias']if v['uuid']=='1f45e002-4f40-4087-bbed-3be260272d8f')];print('R198_BUILD_ACTUAL_CANDIDATE_HARD_CU',flush=True);records,trees=F.build({**h,'zones':[]})"
assert code.count(needle)==1
replacement="old_native_track_UUIDs={t['uuid']for t in g['tracks']};unaccepted_CLK={t['uuid']for t in h['tracks']if t['uuid']not in old_native_track_UUIDs and C.norm(t['net'])=='/motherboard_do/DOA_SCLK_FIELD' and t['layer']=='F.Cu' and t.get('prospective_not_native')};assert len(unaccepted_CLK)==3;h={**h,'tracks':[t for t in h['tracks']if t['uuid']not in unaccepted_CLK]};full={**full,'tracks':h['tracks']};ports=[next(v for v in h['vias']if v['uuid']=='1f45e002-4f40-4087-bbed-3be260272d8f')];print('R200_BUILD_EXACT_NEW_CLOCK_WITHDRAWAL_SCENE',flush=True);records,trees=F.build({**h,'zones':[]})"
code=code.replace(needle,replacement)
code=code.replace("'original_or_new_Cu_deleted':False","'unadopted_three_clock_detour_segments_withdrawn_only_in_nomination_scene':sorted(unaccepted_CLK),'all_original_native_Cu_unchanged':True,'new_actual_clock_detour_source_reference_contact_geometry_reconstruction_required':True")
"""
code=code.replace(anchor,extra+'\n'+anchor)
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
