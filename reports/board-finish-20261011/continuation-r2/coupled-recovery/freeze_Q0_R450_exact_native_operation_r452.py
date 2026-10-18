"""Freeze smaller saved-evidence Q0 recipe; no source/native acceptance."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'freeze_Q0_R426_exact_native_operation_r428.py'
code=base.read_text().replace('Q0-R426-exact-native-owned-operation-r428','Q0-R450-exact-native-owned-operation-r452').replace('Q0-SENSE-In2-Q0-In3-coupled-r426','Q0-saved-GATE-SENSE-existing-barrels-r450').replace('e95a83e0dfa2c45dcbb392c693e36ae62c28846bbfc31118c68ae5711c3af272','681b07ace4dad300c507f1992e327ab4cfc17a1c73608edf27067054599adc8b')
code=code.replace('len(nt)==20','len(nt)==22').replace("len(nom['new_vias'])==7 and len(nom['deleted_tracks'])==3","len(nom['new_vias'])==3 and len(nom['deleted_tracks'])==4")
start=code.index("pairrows=json.loads(");end=code.index("packet={",start)
code=code[:start]+"""pairrows=json.loads((nomdir/'two-Q0-actual-return-nominations.json').read_bytes());assert len(pairrows)==2 and all(.90<=x['spacing_mm']<=1.0 and x['PASS']for x in pairrows)
for row in pairrows:
 row['signal']=roles.get(row['signal'],row['signal']);row['return']=roles.get(row['return'],row['return'])
put(out/'two-exact-paired-source-return-nominations.json',pairrows)
"""+code[end:]
code=code.replace("'original_SENSE_via_UUID':'5a4b7757-ae7c-470d-81fe-abcec92e0f06',","'existing_SENSE_vias':nom['existing_SENSE_vias'],'original_SENSE_via_UUIDs':[v['uuid']for v in nom['existing_SENSE_vias']],")
code=code.replace("'new_track_count':20,'new_ordinary_via_count':7,'exact_original_track_deletes':3","'new_track_count':22,'new_ordinary_via_count':3,'exact_original_track_deletes':4").replace('ordinary7_must_native_flash_all6','ordinary3_must_native_flash_all6').replace('R426_nomination_receipt_sha256','R450_nomination_receipt_sha256')
code=code.replace("'all_current_source_contacts_ref_planner_current_r06_r07_native_pose_parity_fullfill_DRC_SI_and_new_pad_body':'OPEN'","'all_current_source_contacts_ref_planner_current_r06_r07_native_pose_parity_fullfill_DRC_SI_and_new_pad_body':'OPEN','SENSE_same_plane_In1_actual_finite_source_conductor_proof':'OPEN; inherited blanket paired-return checker FAIL preserved separately','all_old_POWER_and_FLT_native_discrete_Cu_exact_retained':True")
exec(compile(code,str(base),'exec'))
