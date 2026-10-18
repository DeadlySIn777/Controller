"""Authorize explicit local negative filled Cu; never waive positive gains."""
from pathlib import Path
import hashlib
H=Path(__file__).resolve().parent
src=H/'construct_CORE_R112_per_polygon_immutable_owned_r244.py'
dst=H/'construct_CORE_R112_local_reserve_immutable_owned_r246.py'
assert not dst.exists()
t=src.read_text().replace('construction-r244','construction-r246').replace('R244_','R246_')
t=t.replace('import restore_SAFE_generated_precision_states_r168 as PS','import restore_SAFE_generated_precision_states_r168 as PS\nimport guarded_power_projection_r44 as Z')
start=t.index('   remaining=pzero.difference(cut);clip=[]')
end=t.index('   gain=remaining.difference(pzero);outside_withdrawal=',start+20)
# Skip the inside-loop occurrence; replace through the post-loop line.
end=t.index('   gain=remaining.difference(pzero);outside_withdrawal=',end+1)
replacement="""   remaining=pzero.difference(cut);clip=[]
   for iteration in range(16):
    gain=remaining.difference(pzero)
    if gain.is_empty:break
    seed=O/(uid+'-'+str(i)+'-'+str(iteration)+'-raw-positive-filled-gain.wkb');seed.write_bytes(gain.wkb)
    reserve=Z.bounded_buffer(gain,.0001);reserve_zero=set_precision(reserve,0);assert reserve_zero.wkb==reserve.wkb
    rf=O/(uid+'-'+str(i)+'-'+str(iteration)+'-explicit-100nm-local-filled-reserve.wkb');rf.write_bytes(reserve.wkb)
    previous=remaining;remaining=remaining.difference(reserve_zero).intersection(pzero)
    removed=previous.difference(remaining);negative=O/(uid+'-'+str(i)+'-'+str(iteration)+'-actual-local-filled-withdrawal.wkb');negative.write_bytes(removed.wkb)
    clip.append({'iteration':iteration,'actual_raw_gain_WKB_file':str(seed),'actual_raw_gain_WKB_sha256':C.sha(gain.wkb),'actual_raw_gain_mm2':gain.area,'local_reserve_cutter_file':str(rf),'local_reserve_WKB_sha256':C.sha(reserve.wkb),'reserve_nominal_mm':.0001,'only_local_new_generated_outward_bound_not_original_coordinate_snap':True,'actual_negative_filled_delta_file':str(negative),'actual_negative_delta_WKB_sha256':C.sha(removed.wkb),'actual_removed_mm2':removed.area,'bounded_to_exact_original_record_after_negative_cut':True})
"""
t=t[:start]+replacement+t[end:]
t=t.replace("ok=gain.is_empty and outside_withdrawal.is_empty and serialized_equal","ok=gain.is_empty and serialized_equal")
t=t.replace("'strict_no_removal_outside_actual_role_withdrawal':outside_withdrawal.is_empty","'raw_original_role_only_scope_pass':outside_withdrawal.is_empty,'explicit_additional_negative_filled_withdrawal_WKB_sha256':C.sha(outside_withdrawal.wkb),'new_local_negative_withdrawals_authorized_separately_by_root_2026_10_12':True")
a="steps.append(row)"
assert t.count(a)==1
t=t.replace(a,"steps.append(row);(O/(uid+'-'+str(i)+'-explicit-final-additional-negative-filled-withdrawal.wkb')).write_bytes(outside_withdrawal.wkb)")
t=t.replace("'entire_filled_only_actual_role_withdrawals':extra.is_empty","'raw_original_role_only_scope_pass':extra.is_empty,'entire_explicit_additional_negative_delta_WKB_sha256':C.sha(extra.wkb),'root_authorized_local_negative_filled_scope_native_current_and_all_source_reference_still_OPEN':True")
t=t.replace("if not gain.is_empty or not extra.is_empty or(local is not None and not local.is_empty)","if not gain.is_empty or(local is not None and not local.is_empty)")
t=t.replace("ledger.append(row);outmap[uid]['fills']=finalfills","ledger.append(row);outmap[uid]['fills']=finalfills;(O/(uid+'-entire-explicit-additional-negative-filled-withdrawal.wkb')).write_bytes(extra.wkb)")
t=t.replace("'all_exact_empty_gain_and_only_actual_withdrawal_required':True","'all_exact_empty_gain_required_no_tolerance':True,'actual_role_withdrawals_plus_explicit_root_authorized_local_negative_filled_delta':True")
t=t.replace("'no_native_or_global_projection_no_global_snap_no_tolerance':True","'no_native_or_global_projection_no_global_snap_no_tolerance':True,'local_negative_reserve_scope_authority':'Root 2026-10-12: explicit LOCAL remove-only reserves around literal gains on actual FILLED Cu only; all q physical/intended/settings stay exact; source/contact/reference/current/native requalification mandatory.'")
t=t.replace('EXACT_R112_PER_POLYGON_IMMUTABLE_OWNED_FILL_CONSTRUCTOR_PASS_FULL_GATES_OPEN','EXACT_R112_IMMUTABLE_OWNED_LOCAL_NEGATIVE_FILLED_RESERVE_CONSTRUCTOR_PASS_FULL_GATES_OPEN')
dst.write_text(t);compile(t,str(dst),'exec')
print(hashlib.sha256(dst.read_bytes()).hexdigest())
