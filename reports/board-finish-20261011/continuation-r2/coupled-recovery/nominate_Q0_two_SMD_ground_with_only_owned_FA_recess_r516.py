"""Freeze ground extension geometry requiring only the named new FA recess.

Preserve R514 complete hard-mask failure. This nomination withholds only
owned7ef during search and emits exact required remove-only cutter scopes;
no model, prior role or current filled record is modified/qualified here.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'construct_Q0_both_moved_SMD_source_reference_extension_r514.py'
code=base.read_text()
replacements={
 'Q0-both-moved-SMD-source-reference-extension-r514':'Q0-two-SMD-ground-only-owned-FA-recess-nomination-r516',
 "if z['layer']!=layer or K.L.norm(z['net'])==GND or z['shape'].distance(window)>1:continue":"if z['uuid']=='7ef3cb5e-deed-5cd0-9002-7f87b3e9ac19':continue\n if z['layer']!=layer or K.L.norm(z['net'])==GND or z['shape'].distance(window)>1:continue",
 "if K.L.norm(z['net'])==GND:continue":"if z['uuid']=='7ef3cb5e-deed-5cd0-9002-7f87b3e9ac19':continue\n if K.L.norm(z['net'])==GND:continue",
 'Q0-two-exact-R10016-SMD-reference-r514|':'Q0-two-exact-R10016-SMD-reference-coupled-7ef-r516|',
 'CONCRETE_BOTH_MOVED_SMD_ACTUAL_J3_ROOTED_REFERENCE_POSITIVE_NOMINATION_ALL_INDEPENDENT_GATES_OPEN':'CONCRETE_GROUND_GEOMETRY_WITH_NAMED_OWNED_FA_CUT_REQUIRED_ALL_GATES_OPEN',
}
for old,new in replacements.items():assert old in code,old;code=code.replace(old,new)
# The original trial graph keeps all source copper but is not a legal joint
# power composition. Freeze the exact cutter before the final packet.
marker="pp=out/'only-one-new-ground-reference-positive-zone-and-filled-record.pkl';"
assert code.count(marker)==1
addition="""owned=next(z for z in q if z['uuid']=='7ef3cb5e-deed-5cd0-9002-7f87b3e9ac19');assert owned['layer']=='In1.Cu'and K.L.norm(owned['net'])=='/motherboard_power_entry/FIELD_A_24V_PROTECTED';physical_cutter=K.Z.bounded_buffer(selected['zone']['shape'],max(.25,float(owned['clearance_mm']),gap(owned['net']))+.025);intended_cutter=K.Z.bounded_buffer(selected['zone']['zone_outline_shape'],max(.25,float(owned['clearance_mm']),gap(owned['net']))+.025);selected['required_only_owned_FA_negative_operations']=[{'UUID':owned['uuid'],'role':role,'before_exact_WKB_sha256':K.C.sha(owned[role].wkb),'exact_negative_cutter':cutter,'negative_only':True,'current_native_source_all_contacts_and_full_signed_load_path_mandatory':True}for role,cutter in [('shape',physical_cutter),('zone_outline_shape',intended_cutter)]];selected['source_only_nomination_not_legal_joint_power_acceptance']=True
 """
code=code.replace(marker,addition+marker)
code=code.replace("'new_plane_intended_mm2':selected['zone']['zone_outline_shape'].area","'new_plane_intended_mm2':selected['zone']['zone_outline_shape'].area,'exactly_one_NEW_owned_FA_withdrawal_required':owned['uuid'],'all_power_source_current_direct_contacts_native_and_old_reference_gates':'OPEN_NO_COMPOSED_LEGAL_MODEL'" )
derived=H/'Q0-two-SMD-ground-only-owned-FA-recess-nomination-r516-derived-constructor.py';assert not derived.exists();derived.write_text(code)
exec(compile(code,str(derived),'exec'))
