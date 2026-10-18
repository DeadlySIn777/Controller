from pathlib import Path
H=Path(__file__).resolve().parent
dst=H/'audit_R155_detached_native_serialization_r310.py';assert not dst.exists()
s=(H/'audit_R155_detached_native_serialization_r308.py').read_text()
s=s.replace("tracks={x['uuid']:x for x in h['tracks']};vias={x['uuid']:x for x in h['vias']};cuchecks=[]","tracks={x['uuid']:x for x in h['tracks']};vias={x['uuid']:x for x in h['vias']};cuchecks=[];lock_authority_rows=[]\nmanifest=read(r['explicit_current_emit_manifest_file']);frozen_locks={x['uuid']:x for x in manifest['frozen_new_discrete_addition_rows']}")
needle="assert bool(children(a,'locked'))==bool(t.get('locked',False))"
assert s.count(needle)==1
s=s.replace(needle,"actual_lock=bool(children(a,'locked'))\n  if 'locked'in t or not actual_lock:assert actual_lock==bool(t.get('locked',False))\n  else:\n   owner=frozen_locks[row['uuid']];assert sha(owner['chunk_path'])==owner['chunk_sha256']==row['chunk_sha256']and sha(owner['authorizing_packet_file'])==owner['authorizing_packet_sha256'];assert value(a,'locked')=='yes'\n   lock_authority_rows.append({'uuid':row['uuid'],'current_electrical_record_lock_key':'ABSENT','exact_frozen_serialized_attribute':'locked yes','authorizing_packet_file':owner['authorizing_packet_file'],'authorizing_packet_sha256':owner['authorizing_packet_sha256'],'exact_frozen_chunk_sha256':owner['chunk_sha256']})")
s=s.replace("'literal_native_raw_IU_locked_geometry_matches_current':True","'literal_native_raw_IU_geometry_matches_current_and_frozen_lock_authority':True")
s=s.replace("out=H/'R155-detached-native-serialization-independent-r308'","assert {x['uuid']for x in lock_authority_rows}=={'850312b1-ae93-5823-854f-c84ea4ced609','94924525-1f04-547b-ab6a-265f2b23a698','c4ce50dd-a8c7-515d-84eb-f58071550c38'}\nout=H/'R155-detached-native-serialization-independent-r310'")
s=s.replace("'literal_nm_AST_raw_net_locked_settings_roundtrip':True","'literal_nm_AST_raw_net_settings_roundtrip':True,'all_present_model_lock_fields_and_exact_frozen_DIC_lock_authority_preserved':True,'three_frozen_DIC_locked_attribute_authorities':lock_authority_rows")
dst.write_text(s,encoding='utf-8',newline='\n')
