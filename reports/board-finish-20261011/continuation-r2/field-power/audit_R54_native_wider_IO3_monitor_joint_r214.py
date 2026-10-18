"""Preserve R213; complete the explicit generated-UUID list from its exact role ledger."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_R54_native_wider_IO3_monitor_joint_r213.py').read_text(encoding='utf-8')
s=s.replace('R54-native-wider-IO3-monitor-joint-audit-r213','R54-native-wider-IO3-monitor-joint-audit-r214')
a="z=copy.deepcopy(z);restore_bound_generated_precision_states(b,z);base_owned="
b="z=copy.deepcopy(z);prior_tag_UUIDs=sorted(b['restored_generated_grid_UUIDs']);role_UUIDs={q['new_generated_UUID'] for q in b['generated_precision_state_ledger']};assert role_UUIDs=={q['uuid'] for q in z};b['restored_generated_grid_UUIDs']=sorted(role_UUIDs);restore_bound_generated_precision_states(b,z);write(O/'exact-bound-generated-UUID-list-completion.json',{'prior_UUID_list':prior_tag_UUIDs,'complete_UUID_list':b['restored_generated_grid_UUIDs'],'source_ledger_SHA256':sha(baseline/'derived-generated-precision-state-ledger.json'),'all_role_WKB_bindings_exact_R168_checked':True,'geometry_coordinates_and_role_ledger_unchanged':True,'R213_assertion_failure_preserved':True});base_owned="
assert a in s;s=s.replace(a,b)
s=s.replace("b['generated_precision_state_ledger']=precision;write", "b['generated_precision_state_ledger']=precision;b['restored_generated_grid_UUIDs']=sorted({q['uuid'] for q in z});write")
exec(compile(s,str(H/'audit_R54_native_wider_IO3_monitor_joint_r213.py'),'exec'))
