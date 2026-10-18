"""Audit R488 directly; preserve misbound R490/R492 receipts unchanged."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'Q0-R488-final-owned-exact-wrapper-r492-derived-auditor.py'
code=base.read_text()
assert "candidate=H/'Q0-exact-R476-ground-contact-pose-r478'" in code
start=code.index("candidate=H/'Q0-exact-R476-ground-contact-pose-r478'")
end=code.index("pd=H/'Q0-R474-ground-contact-pose-native-r476'",start)
binding="""candidate=H/'Q0-owned-roles-literal-negative-canonical-r488';crp=candidate/'receipt.json';assert sha(crp)=='fd6ab6fc83f796e5455370244089b4e4daf571920b81600a6249767f7a3f6e9c';cr=json.loads(crp.read_bytes());cm=Path(cr['new_model_file']);assert sha(cm)==cr['new_model_sha256']=='1b2c6f54ab37e90c415a2e053862d8d8e35f3767b4e2130555bb307458cf075e';bm=P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(bm)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g0,h0,b0,q0,before=pickle.loads(bm.read_bytes());g,h,b,q,after=pickle.loads(cm.read_bytes());assert g==g0 and len(q)==len(q0)
from shapely import set_precision
import restore_field_current_mixed_precision_states_r366 as M
allowed={(uid,role)for uid in('bde7a0cf-1ad7-5a04-b956-9f8848bb3f2a','e2fe644a-2849-5c69-8ebb-d1e94909cd4c')for role in('shape','zone_outline_shape')}
for a,z in zip(q0,q):
 assert set(a)==set(z)
 for key in a:
  if(a['uuid'],key)in allowed:assert set_precision(z[key],0).difference(set_precision(a[key],0)).is_empty
  else:assert a[key].wkb==z[key].wkb if hasattr(a[key],'wkb')else a[key]==z[key]
restoredB=copy.deepcopy(b)
for row,old in zip(restoredB['generated_precision_state_ledger'],b0['generated_precision_state_ledger']):
 assert(row['new_generated_UUID'],row['role'])==(old['new_generated_UUID'],old['role'])
 if(row['new_generated_UUID'],row['role'])in allowed:row['unchanged_WKB_SHA256']=old['unchanged_WKB_SHA256']
assert restoredB==b0
precision_attestation=M.restore_bound_field_current_precision_states(b,q)
put(out/'exact-final-R488-current-input-and-four-negative-roles.json',{'model_file':str(cm),'model_sha256':sha(cm),'baseline_file':str(bm),'baseline_sha256':sha(bm),'constructor_receipt_file':str(crp),'constructor_receipt_sha256':sha(crp),'exhaustive_current_mixed_precision_binding':precision_attestation,'exactly_four_subtractive_roles':[list(x)for x in sorted(allowed)],'prior_misbound_R492_credited_only_for_R478':True})
"""
code=code[:start]+binding+code[end:]
code=code.replace('Q0-R488-final-owned-exact-wrapper-r492','Q0-R488-explicit-final-current-r496').replace('Q0_R492_','Q0_R496_')
old="affected=set(json.loads((candidate/'affected-native-physical-net-list.json').read_bytes()))"
assert code.count(old)==1
code=code.replace(old,"affected=set(json.loads((H/'Q0-exact-R476-ground-contact-pose-r478/affected-native-physical-net-list.json').read_bytes()))")
code=code.replace("'actual_filled_only_model_sha256':sha(cm)","'actual_final_owned_roles_and_filled_model_sha256':sha(cm),'exact_R155_baseline_model_sha256':sha(bm)")
derived=H/'Q0-R488-explicit-final-current-r496-derived-auditor.py'
assert not derived.exists()
derived.write_text(code)
exec(compile(code,str(derived),'exec'))
