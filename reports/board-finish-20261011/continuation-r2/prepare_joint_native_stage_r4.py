"""Preserve R3 and support KiCad's implicit zero root angle exactly."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
helper=H/'native_translation_owned_contract_r1.py';nexthelper=H/'native_translation_owned_contract_r2.py'
prior=H/'stage_joint_power_native_r3.py';out=H/'stage_joint_power_native_r4.py';r=H/'joint-native-stage-r4-derivation.json'
assert not nexthelper.exists() and not out.exists() and not r.exists()
s=helper.read_text();needle="  assert len(prior)==len(later)==3 and prior[2]==later[2]==0";assert s.count(needle)==1
s=s.replace(needle,"  if len(prior)==2:prior.append(0.)\n  if len(later)==2:later.append(0.)\n"+needle)
compile(s,str(nexthelper),'exec');nexthelper.write_text(s)
s=prior.read_text();needle='import native_translation_owned_contract_r1 as FP';assert s.count(needle)==1;s=s.replace(needle,'import native_translation_owned_contract_r2 as FP')
needle="        pose=read(command[7]);mask=read(command[6])";assert s.count(needle)==1
s=s.replace(needle,"        for arg in(command[6],command[7]):\n            path=Path(arg);pins[str(path.resolve())]=sha(path)\n"+needle)
compile(s,str(out),'exec');out.write_text(s)
r.write_text(json.dumps({'prior_stager_sha256':sha(prior),'derived_stager_sha256':sha(out),'prior_translation_helper_sha256':sha(helper),'derived_translation_helper_sha256':sha(nexthelper),'missing_KiCad_root_angle_interpreted_as_zero_only_for_pose_comparison':True,'original_footprint_chunk_bytes_hash_and_all_non_root_at_AST_nodes_still_exact':True,'both_original_and_extended_native_pose_mask_contract_files_hash_bound':True,'only_explicit_R17031_F_zero_angle_translation_supported':True,'accepted_authorizer_and_complete_contact_audit_required':True,'native_source_current_refill_DRC':'OPEN','native_jobs':0,'board_written':False},indent=1)+'\n')
print(json.dumps({'stager_sha256':sha(out),'translation_helper_sha256':sha(nexthelper)}))
