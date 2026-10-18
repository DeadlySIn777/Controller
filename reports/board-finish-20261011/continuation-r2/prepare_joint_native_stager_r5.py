"""Derive same-UUID Cu replacement support without changing frozen R4."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=H/'stage_joint_power_native_r4.py';out=H/'stage_joint_power_native_r5.py'
assert not out.exists()
s=p.read_text()
def sub(a,b):
 global s
 assert s.count(a)==1,a
 s=s.replace(a,b)
sub('import native_translation_owned_contract_r2 as FP','import native_translation_owned_contract_r2 as FP\nimport native_same_uuid_cu_contract_r1 as CR')
sub('    replaced,fp_pins,fp_poses,fp_masks=FP.collect(fp_rows,inv)','    fp_replaced,fp_pins,fp_poses,fp_masks=FP.collect(fp_rows,inv)\n    cu_rows=r.get("native_existing_owned_Cu_replacement_rows",[])\n    cu_replaced,cu_pins,cu_flashes=CR.collect(cu_rows,inv)\n    assert not set(fp_replaced)&set(cu_replaced)\n    replaced={**fp_replaced,**cu_replaced}')
sub("    pins.update(fp_pins);pins[str(Path(FP.__file__).resolve())]=sha(FP.__file__)","    pins.update(fp_pins);pins[str(Path(FP.__file__).resolve())]=sha(FP.__file__)\n    pins.update(cu_pins);pins[str(Path(CR.__file__).resolve())]=sha(CR.__file__)")
sub("via['added_vias']=[row for row in via['added_vias'] if row['uuid'] not in removed]","via['added_vias']=[row for row in via['added_vias'] if row['uuid'] not in removed and row['uuid'] not in cu_replaced]")
sub("    via_path = out/'native-via-spec.json'; write(via_path,via)","    via_path = out/'native-via-spec.json'; write(via_path,via)\n    postfill=out/'native-postfill-via-obligations.json'\n    write(postfill,{'candidate_sha256':sha(board),'same_UUID_existing_replacement_vias':cu_flashes,'new_ordinary_via_UUIDs':[uid for uid in ids if copper[uid]['kind']=='via'],'all_Cu_expected_ledger_file':str(expected.resolve()),'all_Cu_expected_ledger_sha256':sha(expected),'required_after_actual_all_zone_native_fill':True,'no_old_remove_unused_via_is_credited_as_new_ordinary':True})")
sub('zone_spec,zone_origin,zone_helper): pins', 'zone_spec,zone_origin,zone_helper,postfill): pins')
sub("'exact_owned_footprint_translation_UUIDs':sorted(replaced)","'exact_owned_footprint_translation_UUIDs':sorted(fp_replaced),'exact_same_UUID_owned_Cu_replacement_UUIDs':sorted(cu_replaced),'owned_Cu_replacement_rows':cu_rows,'native_postfill_via_obligations_sha256':sha(postfill),'native_postfill_via_obligations_file':str(postfill.resolve())")
sub("'native_zone_count':zr.get('native_zones_checked')", "'native_postfill_via_obligations_file':str(postfill.resolve()),'native_postfill_via_obligations_sha256':sha(postfill),'same_UUID_owned_Cu_replacements':len(cu_replaced),'native_zone_count':zr.get('native_zones_checked')")
compile(s,str(out),'exec');out.write_text(s)
(H/'joint-native-stager-r5-derivation.json').write_text(json.dumps({'source_stager_file':str(p.resolve()),'source_stager_sha256':sha(p),'derived_stager_file':str(out.resolve()),'derived_stager_sha256':sha(out),'same_UUID_Cu_helper_file':str((H/'native_same_uuid_cu_contract_r1.py').resolve()),'same_UUID_Cu_helper_sha256':sha(H/'native_same_uuid_cu_contract_r1.py'),'exact_old_native_byte_and_AST_contract_plus_authorized_two_U19008_neighbour_changes':True,'same_UUID_old_via_fresh_F_In1_In4_obligation_separate_from_new_ordinary_all6':True,'original_source_FP_zone_rule_and_all_Cu_gates_preserved':True,'native_jobs':0,'board_written':False,'adopted':False},indent=1)+'\n')
print(json.dumps({'stager':str(out),'sha256':sha(out)}))
