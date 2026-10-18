"""Separate current FA+IO3 repair; R481 and all frozen native jobs unchanged."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'R155-protected-FA-TMR-declared-local-boundary-negatives-r479/exact-generated-source.txt').read_text(encoding='utf-8')
s=s.replace("M=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'", "M=H/'R155-protected-FA-TMR-local-negative-inherited-outline-FAIL-r481/model.pkl'")
s=s.replace('ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4','206031df3e638b08ff3356239f2ff83efde810944c9a0630ee06c8a9672df1ff')
s=s.replace("O=H/'R155-protected-FA-TMR-declared-local-boundary-negatives-r479'", "O=H/'R155-FA-plus-IO3-TMR-owned-local-negative-r487'")
s=s.replace("startswith('7ef3cb5e')", "startswith('4f297f78')").replace("x['layer']=='In1.Cu'and L.norm(x['net'])=='/motherboard_power_entry/FIELD_A_24V_PROTECTED'", "x['layer']=='In2.Cu'and L.norm(x['net'])=='/IO_3V3'")
s=s.replace(" assert lit(x['shape']).difference(lit(x['zone_outline_shape'])).is_empty", """ prior_q=next(y for y in q0 if y['uuid']==uid)
 inherited_before=lit(prior_q['shape']).difference(lit(prior_q['zone_outline_shape']));inherited_after=lit(x['shape']).difference(lit(x['zone_outline_shape']))
 assert inherited_before.wkb==inherited_after.wkb,('changed physical-outside-intended inherited witness')
 wf=O/'unchanged-inherited-IO3-physical-outside-intended.wkb';wf.write_bytes(inherited_after.wkb)
 put(O/'unchanged-inherited-IO3-outline-mismatch.json',{'status':'EXACT_BEFORE_AFTER_WITNESS_UNCHANGED','before_sha256':dg(inherited_before),'after_sha256':dg(inherited_after),'empty':inherited_after.is_empty,'area_mm2':inherited_after.area,'bounds':None if inherited_after.is_empty else inherited_after.bounds,'witness_sha256':sha(wf)})""")
s=s.replace("set(z['fills'])=={'In1.Cu'}", "set(z['fills'])=={'In2.Cu'}").replace("z['fills']['In1.Cu']", "z['fills']['In2.Cu']").replace("uid+'-In1-only", "uid+'-In2-only").replace("'layer':'In1.Cu'", "'layer':'In2.Cu'")
s=s.replace("b['FA_native_TMR_keepout_explicit_boundary_negatives_r479']", "b['IO3_native_TMR_keepout_explicit_boundary_negatives_r487']")
s=s.replace("'status':'CONSTRUCTION_COMPLETE_PRIMARY_KEEP_OUT_PLUS_DECLARED_LOCAL_BOUNDARY_NEGATIVES_FULL_SOURCE_CURRENT_NATIVE_GATES_OPEN'", "'status':'CONSTRUCTION_COMPLETE_FA_PLUS_IO3_KEEP_OUT_SOURCE_CONTACT_CURRENT_NATIVE_GATES_OPEN','prior_FA_R481_inherited_failure_and_repairs_exact':True")
s=s.replace("print('R479 receipt'", "print('R487 receipt'")
exec(compile(s,str(H/'construct_current_FA_plus_IO3_TMR_local_negative_r487.py'),'exec'))
