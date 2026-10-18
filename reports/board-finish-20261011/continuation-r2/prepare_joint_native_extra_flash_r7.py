"""Preserve previous helpers and propagate explicit old-barrel flash proofs."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def derive(origin,target,changes):
 assert not target.exists();s=origin.read_text()
 for old,new in changes:
  assert s.count(old)==1,old;s=s.replace(old,new)
 compile(s,str(target),'exec');target.write_text(s);return {'source':str(origin),'source_sha256':sha(origin),'derived':str(target),'derived_sha256':sha(target),'changes':changes}
def main():
 r=[]
 r.append(derive(H/'stage_joint_power_native_r6.py',H/'stage_joint_power_native_r7.py',[
 ('import native_same_uuid_cu_contract_r1 as CR','import native_same_uuid_cu_contract_r1 as CR\nimport native_existing_extra_flash_contract_r1 as EF'),
 ("    postfill=out/'native-postfill-via-obligations.json'","    existing_extra,pins_extra=EF.collect(r['existing_via_prospective_new_flashes'],inv[4],after[4],copper,removed,cu_replaced)\n    pins.update(pins_extra);pins[str(Path(EF.__file__).resolve())]=sha(EF.__file__)\n    postfill=out/'native-postfill-via-obligations.json'"),
 ("'same_UUID_existing_replacement_vias':cu_flashes,'new_ordinary_via_UUIDs'","'same_UUID_existing_replacement_vias':cu_flashes,'same_serialized_existing_extra_layer_vias':existing_extra,'new_ordinary_via_UUIDs'")]))
 r.append(derive(H/'native_final_partitions_contract_r1.py',H/'native_final_partitions_contract_r2.py',[
 ("for r in o['same_UUID_existing_replacement_vias']:","for r in o['same_UUID_existing_replacement_vias']+o['same_serialized_existing_extra_layer_vias']:"),
 ("'required_existing_replacement_vias':o['same_UUID_existing_replacement_vias'],'new_ordinary_via_UUIDs'","'required_existing_replacement_vias':o['same_UUID_existing_replacement_vias'],'same_serialized_existing_extra_layer_vias':o['same_serialized_existing_extra_layer_vias'],'new_ordinary_via_UUIDs'")]))
 r.append(derive(H/'measure_joint_power_native_r2.py',H/'measure_joint_power_native_r3.py',[
 ("measure_joint_power_backend_r2_","measure_joint_power_backend_r3_"),
 ("native_final_partitions_contract_r1.py","native_final_partitions_contract_r2.py"),
 ("step_measure_all_native_r2.sh","step_measure_all_native_r3.sh")]))
 (H/'joint-native-extra-flash-r7-derivation.json').write_text(json.dumps({'verdict':'PREPARED_PREVIOUS_HELPERS_PRESERVED','derivations':r,'extra_flash_collector_sha256':sha(H/'native_existing_extra_flash_contract_r1.py'),'native_jobs':0,'board_written':False},indent=1)+'\n')
 print('R7_PREPARED',[(Path(q['derived']).name,q['derived_sha256'])for q in r])
if __name__=='__main__':main()
