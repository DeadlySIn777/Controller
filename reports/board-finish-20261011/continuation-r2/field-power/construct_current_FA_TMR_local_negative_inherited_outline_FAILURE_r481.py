"""R479 local cut, preserving the exact inherited remote outline mismatch."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'R155-protected-FA-TMR-declared-local-boundary-negatives-r479/exact-generated-source.txt').read_text(encoding='utf-8')
s=s.replace("O=H/'R155-protected-FA-TMR-declared-local-boundary-negatives-r479'", "O=H/'R155-protected-FA-TMR-local-negative-inherited-outline-FAIL-r481'")
s=s.replace(" assert lit(x['shape']).difference(lit(x['zone_outline_shape'])).is_empty", """ prior_q=next(y for y in q0 if y['uuid']==uid)
 inherited_before=lit(prior_q['shape']).difference(lit(prior_q['zone_outline_shape']));inherited_after=lit(x['shape']).difference(lit(x['zone_outline_shape']))
 assert inherited_before.wkb==inherited_after.wkb,('changed physical-outside-intended inherited witness')
 wf=O/'unchanged-inherited-physical-outside-intended.wkb';wf.write_bytes(inherited_after.wkb)
 put(O/'unchanged-inherited-outline-mismatch-FAIL.json',{'status':'INHERITED_FAIL_UNCHANGED_NO_REMOTE_REPAIR','before_sha256':dg(inherited_before),'after_sha256':dg(inherited_after),'empty':inherited_after.is_empty,'area_mm2':inherited_after.area,'bounds':inherited_after.bounds,'witness_sha256':sha(wf)})""")
s=s.replace("'status':'CONSTRUCTION_COMPLETE_PRIMARY_KEEP_OUT_PLUS_DECLARED_LOCAL_BOUNDARY_NEGATIVES_FULL_SOURCE_CURRENT_NATIVE_GATES_OPEN'", "'status':'CONSTRUCTION_COMPLETE_LOCAL_KEEP_OUT_REPAIR_INHERITED_OUTLINE_FAIL_UNCHANGED_FULL_SOURCE_CURRENT_NATIVE_OPEN','inherited_physical_outside_intended_FAIL':not inherited_after.is_empty")
s=s.replace("b['FA_native_TMR_keepout_explicit_boundary_negatives_r479']", "b['FA_native_TMR_keepout_explicit_boundary_negatives_r481']")
s=s.replace("print('R479 receipt'", "print('R481 receipt'")
exec(compile(s,str(H/'construct_current_FA_TMR_local_negative_inherited_outline_FAILURE_r481.py'),'exec'))
