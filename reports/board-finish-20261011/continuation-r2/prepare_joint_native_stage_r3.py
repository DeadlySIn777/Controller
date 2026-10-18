"""Derive explicit root-translation support while retaining the frozen R2 stager."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'stage_joint_power_native_r2.py';out=H/'stage_joint_power_native_r3.py';receipt=H/'joint-native-stage-r3-derivation.json'
assert not out.exists() and not receipt.exists();s=p.read_text()
needle='import native_pose_signal_contract as NC';assert s.count(needle)==1;s=s.replace(needle,needle+'\nimport native_translation_owned_contract_r1 as FP')
needle="    inv = NC.C.inventory(parent.read_bytes()); added = []; ids = set();removed={}";assert s.count(needle)==1
s=s.replace(needle,needle+"\n    fp_rows=r.get('native_existing_owned_footprint_replacement_rows',[])\n    replaced,fp_pins,fp_poses,fp_masks=FP.collect(fp_rows,inv)")
needle="    pins[str(declared_parent.resolve())]=sha(declared_parent)";assert s.count(needle)==1
s=s.replace(needle,needle+"\n    pins.update(fp_pins);pins[str(Path(FP.__file__).resolve())]=sha(FP.__file__)")
needle="b''.join(ch for ch in inv[1] if NC.C.pcbtext.chunk_uuid(ch) not in removed)";assert s.count(needle)==1
s=s.replace(needle,"b''.join(replaced.get(NC.C.pcbtext.chunk_uuid(ch),ch) for ch in inv[1] if NC.C.pcbtext.chunk_uuid(ch) not in removed)")
needle="if uid not in removed)";assert s.count(needle)==1
s=s.replace(needle,"if uid not in removed and uid not in replaced)")
needle="    assert not set(removed)&set(after[3])";assert s.count(needle)==1
s=s.replace(needle,needle+"\n    assert all(after[3][uid]==chunk for uid,chunk in replaced.items()) and not set(removed)&set(replaced)")
needle="    command[9] = str(via_path); command[10] = str(board); command[-1] = str(out/'native-parity.json')";assert s.count(needle)==1
block="""    # Extend both native pose and exact SMD/text contracts before helper wrapping.
    if fp_rows:
        pose=read(command[7]);mask=read(command[6])
        assert not {x['ref']for x in fp_poses}&{x['ref']for x in pose['rows']}
        assert not {x['ref']for x in fp_masks}&{x['ref']for x in mask['footprints']}
        pose['rows'].extend(fp_poses);mask['footprints'].extend(fp_masks)
        pose['explicit_additional_owned_translation_rows']=len(fp_poses)
        mask['explicit_additional_owned_translation_rows']=len(fp_masks)
        pose_path=out/'native-owned-pose-ledger.json';mask_path=out/'native-owned-mask-text-ledger.json'
        write(pose_path,pose);write(mask_path,mask)
        for path in(pose_path,mask_path):pins[str(path.resolve())]=sha(path)
        command[7]=str(pose_path);command[6]=str(mask_path)
"""
s=s.replace(needle,block+needle)
needle="'exact_owned_existing_Cu_deleted':sorted(removed),";assert s.count(needle)==1
s=s.replace(needle,needle+"'exact_owned_footprint_translation_UUIDs':sorted(replaced),'owned_footprint_translation_rows':fp_rows,")
compile(s,str(out),'exec');compile((H/'native_translation_owned_contract_r1.py').read_text(),str(H/'native_translation_owned_contract_r1.py'),'exec');out.write_text(s)
receipt.write_text(json.dumps({'prior_script_sha256':sha(p),'derived_script_sha256':sha(out),'translation_contract_sha256':sha(H/'native_translation_owned_contract_r1.py'),'only_explicit_R17031_F_zero_angle_root_translation_supported':True,'root_at_is_only_permitted_footprint_AST_change':True,'all_original_local_pad_mask_net_UUID_geometry_text_fields_courtyard_BOM_and_source_path_nodes_exact':True,'native_pose_and_exact_pad_text_contracts_extended_explicitly':True,'all_unlisted_parent_entities_and_rules_preserved':True,'requires_accepted_authorizer_and_complete_frozen_host_contact_gates_before_execution':True,'native_source_current_reference_refill_DRC':'OPEN','board_written':False,'native_jobs':0},indent=1)+'\n')
print(json.dumps({'script':str(out),'sha256':sha(out),'translation_helper_sha256':sha(H/'native_translation_owned_contract_r1.py')}))
