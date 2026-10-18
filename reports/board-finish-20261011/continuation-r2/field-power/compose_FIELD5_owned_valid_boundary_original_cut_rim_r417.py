"""Preserve R413 topology failure; explicitly normalize changed owned roles.

Only new/changed generated roles use valid-output 1 nm construction. Every
literal restored point is still tested against original Cu and the declared
local scope; native original arrays and all unrelated roles remain exact.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
owner=H/'compose_FIELD5_bound_original_cut_rim_restore_r413.py'
ns={'__file__':str(owner),'__name__':'_generate_rim_constructor_without_running'}
exec(compile(owner.read_text(encoding='utf-8').rsplit('\nexec(compile(s,',1)[0],str(owner),'exec'),ns)
s=ns['s'];s=s.replace('minimal-R155-bound-original-cut-rim-restoration-r413','minimal-R155-valid-owned-boundary-cut-rim-restoration-r417')
s=s.replace("a=set_precision(literal(s),1e-6,mode='pointwise');rows=[]","a=set_precision(literal(s),1e-6,mode='valid_output');rows=[]")
s=s.replace("a=set_precision(literal(a).difference(reserve),1e-6,mode='pointwise');rows.append","a=set_precision(literal(a).difference(reserve),1e-6,mode='valid_output');rows.append")
s=s.replace("'explicit_former_failed_guard_negative_rim_restoration_envelope_mm':.0005","'explicit_former_failed_guard_negative_rim_restoration_envelope_mm':.0005,'changed_owned_canonical_boundary_mode':'valid_output_only_new_or_changed_roles_no_native_snap','R413_topology_failure_preserved':True")
exec(compile(s,str(H/'compose_FIELD5_R385_minimal_current_restore_r387.py'),'exec'))
