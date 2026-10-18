"""Direct independent original-current comparison of coupled SMD shielding."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'Q0-R504-explicit-final-current-r506-derived-auditor.py'
code=base.read_text();start=code.index("candidate=H/'Q0-owned-actual-fill-strict-local-negative-successor-r504'");end=code.index("pd=H/'Q0-R474-ground-contact-pose-native-r476'",start)
binding="""candidate=H/'Q0-two-SMD-reference-only-owned-FA-recess-current-r518';crp=candidate/'receipt.json';assert sha(crp)=='5c8dca541b0774ca8fba7161f34a39277c8d740d379452c6249de2ac8bd7a90f';cr=json.loads(crp.read_bytes());cm=Path(cr['model_file']);assert sha(cm)==cr['model_sha256']=='6a042063ca93b82533b30dcefed2366b5f80efaab6e5e06e1c862314d3193d50';bm=P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(bm)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g0,h0,b0,q0,before=pickle.loads(bm.read_bytes());g,h,b,q,after=pickle.loads(cm.read_bytes());assert g==g0 and len(q)==len(q0)+1
from shapely import set_precision
import restore_field_current_mixed_precision_states_r366 as M
allowed={(uid,role)for uid in('bde7a0cf-1ad7-5a04-b956-9f8848bb3f2a','e2fe644a-2849-5c69-8ebb-d1e94909cd4c','7ef3cb5e-deed-5cd0-9002-7f87b3e9ac19')for role in('shape','zone_outline_shape')}
newuid='637c65c4-b144-5c66-8c11-42e9f8bf96bc';by={z['uuid']:z for z in q};assert set(by)=={z['uuid']for z in q0}|{newuid}
for a in q0:
 z=by[a['uuid']];assert set(a)==set(z)
 for key in a:
  if(a['uuid'],key)in allowed:assert set_precision(z[key],0).difference(set_precision(a[key],0)).is_empty
  else:assert a[key].wkb==z[key].wkb if hasattr(a[key],'wkb')else a[key]==z[key]
np=candidate/'only-new-FG-positive-and-named-owned-FA-negative-current-delta.pkl';assert sha(np)=='cbe45e63e980bf95da3b3310019c79cbeb2d931262315a440c9f2a7c3dd70069';nom=pickle.loads(np.read_bytes());assert by[newuid].keys()==nom['new_zone'].keys()
for key in by[newuid]:assert by[newuid][key].wkb==nom['new_zone'][key].wkb if hasattr(by[newuid][key],'wkb')else by[newuid][key]==nom['new_zone'][key]
restoredB=copy.deepcopy(b);restoredB['restored_generated_grid_UUIDs'].remove(newuid);restoredB['generated_precision_state_ledger']=[r for r in restoredB['generated_precision_state_ledger']if r['new_generated_UUID']!=newuid]
for row,old in zip(restoredB['generated_precision_state_ledger'],b0['generated_precision_state_ledger']):
 assert(row['new_generated_UUID'],row['role'])==(old['new_generated_UUID'],old['role'])
 if(row['new_generated_UUID'],row['role'])in allowed:row['unchanged_WKB_SHA256']=old['unchanged_WKB_SHA256']
assert restoredB==b0
precision_attestation=M.restore_bound_field_current_precision_states(b,q)
put(out/'exact-R518-input-only-three-old-negative-roles-one-new-ground-zone.json',{'model_file':str(cm),'model_sha256':sha(cm),'baseline_file':str(bm),'baseline_sha256':sha(bm),'constructor_receipt_file':str(crp),'constructor_receipt_sha256':sha(crp),'exhaustive_current_mixed_precision_binding':precision_attestation,'only_three_old_subtractive_role_UUIDs':sorted({x[0]for x in allowed}),'only_new_ground_UUID':newuid,'source_native_and_unrelated_power_contact_current_flags_preserved':True})
"""
code=code[:start]+binding+code[end:]
code=code.replace('Q0-R504-explicit-final-current-r506','Q0-R518-full-current-contacts-source-reference-r520').replace('Q0_R506_','Q0_R520_')
old="affected=set(json.loads((H/'Q0-exact-R476-ground-contact-pose-r478/affected-native-physical-net-list.json').read_bytes()))"
assert code.count(old)==1;code=code.replace(old,old+"|{'/motherboard_power_entry/FIELD_A_24V_PROTECTED'}")
code=code.replace("'generated_q_new_antipad_role_replay_current_native_pose_all6_flash_source_parity_refill_all_baselines_DRC_and_SI':'OPEN'","'generated_q_new_antipad_role_replay_current_native_pose_all6_flash_source_parity_refill_all_baselines_DRC_and_SI':'Scoped host shielding/source/current-role checks separate; full power current/native/SI OPEN'")
derived=H/'Q0-R518-full-current-contacts-source-reference-r520-derived-auditor.py';assert not derived.exists();derived.write_text(code)
exec(compile(code,str(derived),'exec'))
