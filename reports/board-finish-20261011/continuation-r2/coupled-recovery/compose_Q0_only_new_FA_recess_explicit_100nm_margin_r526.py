"""Keep R522 planner FAIL; enlarge only the owned FA negative cutter100nm."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'compose_Q0_two_SMD_reference_with_only_owned_FA_recess_r518.py'
code=base.read_text().replace('Q0-two-SMD-reference-only-owned-FA-recess-current-r518','Q0-only-new-FA-recess-explicit-100nm-margin-r526')
old="mask=set_precision(row['exact_negative_cutter'],0)"
assert code.count(old)==1
code=code.replace(old,"mask=set_precision(K.Z.bounded_buffer(row['exact_negative_cutter'],.0001),0)")
code=code.replace("'only_named_NEW_owned_FA_Cu_withdrawn':True","'only_named_NEW_owned_FA_Cu_withdrawn':True,'explicit_additional_outward_negative_guard_mm':.0001,'R522_native_PASS_extra_margin_FAIL_preserved':True")
code=code.replace("'all_original_raw_failures_preserved':True","'all_original_raw_failures_preserved':True,'only_owned_FA_negative_scope_additional_100nm_guard_explicit':True,'new_FG_geometry_original_native_Cu_and_all_holes_exact_R518':True")
derived=H/'Q0-only-new-FA-recess-explicit-100nm-margin-r526-derived-constructor.py';assert not derived.exists();derived.write_text(code)
exec(compile(code,str(derived),'exec'))
