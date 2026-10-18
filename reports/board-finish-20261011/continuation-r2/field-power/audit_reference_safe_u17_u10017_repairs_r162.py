"""Scoped normalization and reference-safe bypass successor, failures retained."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_u17_u10017_coupled_power_repairs_r155.py').read_text(encoding='utf-8')
s=s.replace('u17-u10017-coupled-incremental-audit-r155','u17-u10017-reference-safe-incremental-audit-r162')
s=s.replace("r154=H/'u10017-protected-source-via-bypass-nominee-r154'", "r154=H/'u10017-reference-safe-source-bypass-nominee-r160'")
old="z=[updates.get(q['uuid'],q) for q in z]+newq;z,viafix=P.normalize_owned_via_guards(h,z);z,trackfix,geoms=TG.normalize_owned_track_guards(h,z);"
new="z=[updates.get(q['uuid'],q) for q in z];z,viafix=P.normalize_owned_via_guards({**h,'vias':d['vias']},z);z,trackfix,geoms=TG.normalize_owned_track_guards({**h,'tracks':adds},z);newq,nvg=P.normalize_owned_via_guards(h,newq);newq,ntg,ng=TG.normalize_owned_track_guards(h,newq);viafix+=nvg;trackfix+=ntg;geoms.update(ng);z+=newq;"
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace('R155','R162').replace('U10017_coupled_source_bypass_r154','U10017_reference_safe_source_bypass_r160')
s=s.replace("'baseline_grid_primitive_R153_review_separate':True", "'baseline_grid_primitive_R153_review_separate':True,'old_owned_planes_normalized_only_for_current_new_via_and_tracks':True,'failed_R155_reference_result_preserved':True")
exec(compile(s,str(H/'audit_u17_u10017_coupled_power_repairs_r155.py'),'exec'))
