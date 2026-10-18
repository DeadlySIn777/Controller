"""Derive a separate fresh ROOT R11 plus owned-DI6 projection binder."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
p=HERE/'di15_current_base_r13.py';s=p.read_text()
s=s.replace('Bind R78, exact owned DI6 additions and hard-only ground snapshot4.','Bind actual ROOT R11, exact owned DI6 additions and all latest hard Cu.')
s=s.replace("HERE.parent/'sbc-power/r17031-translated-source-composition-r78/model.pkl'","HERE.parent/'corrected-joint-ground-base-r11/model.pkl'")
s=s.replace('128a21a83ccc8e1029f4b97e27930f82de743e00ef45fb1fc2041f0967b8a821','24de27f569c8f4ae56b4172e6fc1af374c4f86c12d56215a2989eb793d2a55a8')
s=s.replace('DI15_R78_OWN_DI6_DELTA_PROJECTED_SOURCE_ROOT_BEGIN','DI15_JOINT_R11_OWN_DI6_DELTA_PROJECTED_DRILLED_SOURCE_ROOT_BEGIN')
old=""" hardpath=HERE.parent/'protected-field-return-r4-snapshot-4/proposed-zones.pkl';hard=pickle.loads(A.read(hardpath));assert C.sha(A.read(hardpath))=='213182e7ec8439cccb0087bf99b362e6e149a3f21843d103b7b50ddceb428239';hardids={z['uuid'] for z in hard};zones=[z for z in zones if z['uuid'] not in hardids]+hard
 result={'h':h,'old':old,'binding':binding,'before':before,'after':after,'zones':zones,'refs':refs,'groups':groups,'root':root,'R78_model_sha256':C.sha(A.read(path)),'R11_only_owned_additions_sha256':r11['saved_model_sha256'],'ground_snapshot4_hard_only_sha256':C.sha(A.read(hardpath)),'exact_DI6_incremental_projection_ledger':fillrows,'ground_snapshot4_no_reference_credit':True}
 cache=HERE/'di15-current-r78-projection-r13.pkl';"""
new=""" receiptpath=path.with_name('receipt.json');receipt=__import__('json').loads(A.read(receiptpath));assert receipt['model_sha256']==C.sha(A.read(path));assert receipt['R10_source_spine_exact'] and receipt['all_other_R106_h_and_owned_planes_exact']
 for p,pin in receipt['input_sha256'].items():assert C.sha(A.read(p))==pin,p
 result={'h':h,'old':old,'binding':binding,'before':before,'after':after,'zones':zones,'refs':refs,'groups':groups,'root':root,'joint_R11_model_sha256':C.sha(A.read(path)),'joint_R11_receipt_sha256':C.sha(A.read(receiptpath)),'R11_only_owned_additions_sha256':r11['saved_model_sha256'],'R10_spine_exact_sha256':receipt['R10_proposed_zones_sha256'],'exact_DI6_incremental_projection_ledger':fillrows,'all_source_roots_recomputed_after_actual_drills':True,'new_power_and_ground_planes_have_no_native_or_current_qualification':True}
 cache=HERE/'di15-current-joint-r11-projection-r34.pkl';"""
assert old in s;s=s.replace(old,new).replace('DI15_R78_EXACT_CURRENT_CHECKPOINT','DI15_JOINT_R11_EXACT_CURRENT_CHECKPOINT')
target=HERE/'di15_current_joint_base_r34.py';assert not target.exists();target.write_text(s)

p=HERE/'construct_di15_reference_escape_r28.py';s=p.read_text();s=s.replace('Frozen R78 power/protected model; newer reservations are hard only','Fresh actual ROOT R11 power/protected/field/ground model')
s=s.replace('import di15_reuse_base_r17 as BIND','import di15_current_joint_base_r34 as BIND')
s=s.replace("'di15-partial-annulus-reference-In3-nomination-r28.json'","'di15-joint-r11-In3-nomination-r35.json'")
s=s.replace("'current_R78_model_sha256':current['R78_model_sha256']","'current_joint_R11_model_sha256':current['joint_R11_model_sha256']")
s=s.replace("'latest_ground_snapshot4_hard_only_sha256':current['ground_snapshot4_hard_only_sha256'],'latest_ground_snapshot4_no_reference_credit':True,","'current_joint_R11_receipt_sha256':current['joint_R11_receipt_sha256'],'R10_spine_exact_sha256':current['R10_spine_exact_sha256'],'native_current_qualification_of_power_and_ground_planes':False,")
s=s.replace("'DI6_host_reference_remains_OPEN':True,","'DI6_matched_native_reference_R27_three_remote_native_slivers_remain_OPEN':True,")
s=s.replace("json.dumps(result,indent=1)","json.dumps(result,indent=1,allow_nan=False)")
target=HERE/'construct_di15_reference_escape_r35.py';assert not target.exists();target.write_text(s)
