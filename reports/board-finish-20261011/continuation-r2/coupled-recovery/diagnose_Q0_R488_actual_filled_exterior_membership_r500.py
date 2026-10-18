"""Keep raw R498 intersection FAIL; inspect literal new-role exterior."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'audit_Q0_R488_owned_roles_and_direct_contacts_r498.py'
code=base.read_text().replace('Q0-R488-owned-roles-and-direct-contacts-r498','Q0-R488-actual-filled-exterior-membership-r500')
old="residue=fills.intersection(lost)"
assert code.count(old)==1
code=code.replace(old,"residue=fills.intersection(lost).difference(set_precision(z['shape'],0))")
code=code.replace("'actual_filled_Cu_still_in_new_physical_withdrawal_empty'","'actual_filled_Cu_inside_new_withdrawal_and_literal_exterior_to_after_role_empty'")
code=code.replace("'every_raw_nonempty_failure_retained_no_threshold':True","'every_raw_nonempty_failure_retained_no_threshold':True,'R498_closed_boundary_intersection_raw_FAIL_preserved':True,'strict_exterior_probe_excludes_only_exact_after_role_membership_not_area_or_buffer':True")
derived=H/'Q0-R488-actual-filled-exterior-membership-r500-derived-auditor.py';assert not derived.exists();derived.write_text(code)
exec(compile(code,str(derived),'exec'))
