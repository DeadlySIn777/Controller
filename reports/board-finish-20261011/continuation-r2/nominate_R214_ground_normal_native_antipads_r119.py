"""Normal foreign native plane repour nomination, never a clearance waiver.

Original plane definitions and all old discrete copper remain unchanged. A
nominee still needs explicit local-only new-primitive filled-Cu subtraction,
all contact and ZERO old-reference proofs before native full measurement.
"""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_R214_two_bare_field_ground_pads_r115.py';code=source.read_text()
needle="OUT=H/'R214-two-bare-field-ground-ordinary-fanout-nominees-r115'";assert code.count(needle)==1
code=code.replace(needle,"OUT=H/'R214-ground-normal-native-antipad-nominees-r119'")
needle="    domain=h['domains_normalized'][NET]\n";assert code.count(needle)==1
code=code.replace(needle,"    native_zone_ids={q['uuid'] for q in h['zones']}\n"+needle)
needle="                    if C.norm(q['net'])==NET:continue\n";assert code.count(needle)==1
code=code.replace(needle,needle+"                    if q['kind']=='fill' and q['uuid'] in native_zone_ids:continue # normal prospective repour; never old track/barrel/pad or owned Cu exemption\n")
needle="'all_native_filled_foreign_Cu_hard':True";assert code.count(needle)==1
code=code.replace(needle,"'original_native_foreign_fill_only_normal_antipads_prospective':True,'old_discrete_and_all_held_new_roles_hard':True,'original_all_relationships_direct_layer_contacts_and_ZERO_old_references_still_mandatory':True")
exec(compile(code,str(source),'exec'))
