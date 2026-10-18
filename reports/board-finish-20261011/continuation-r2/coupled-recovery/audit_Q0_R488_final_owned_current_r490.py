"""Fresh independent source/contact/reference audit after exact owned cuts."""
from pathlib import Path
import builtins
H=Path(__file__).resolve().parent;base=H/'audit_Q0_R478_exact_pose_current_contacts_reference_r480.py'
def scoped_compile(source,filename,mode,*args,**kwargs):
 if isinstance(source,str):
  source=source.replace('Q0-R478-exact-pose-current-contacts-reference-r480','Q0-R488-final-owned-current-r490').replace('Q0_R480_','Q0_R490_')
  if "start=time.monotonic();out=H/"in source:
   start=source.index("candidate=H/'Q0-exact-R476-ground-contact-pose-r478'");end=source.index("pd=H/'Q0-R474-ground-contact-pose-native-r476'",start)
   replacement="""candidate=H/'Q0-owned-roles-literal-negative-canonical-r488';crp=candidate/'receipt.json';assert sha(crp)=='fd6ab6fc83f796e5455370244089b4e4daf571920b81600a6249767f7a3f6e9c';cr=json.loads(crp.read_bytes());cm=Path(cr['new_model_file']);assert sha(cm)==cr['new_model_sha256']=='1b2c6f54ab37e90c415a2e053862d8d8e35f3767b4e2130555bb307458cf075e';bm=P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(bm)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g0,h0,b0,q0,before=pickle.loads(bm.read_bytes());g,h,b,q,after=pickle.loads(cm.read_bytes());assert g==g0 and len(q)==len(q0)
allowed={(uid,role)for uid in('bde7a0cf-1ad7-5a04-b956-9f8848bb3f2a','e2fe644a-2849-5c69-8ebb-d1e94909cd4c')for role in('shape','zone_outline_shape')}
for a,z in zip(q0,q):
 assert set(a)==set(z)
 for key in a:
  if(a['uuid'],key)in allowed:
   from shapely import set_precision
   assert set_precision(z[key],0).difference(set_precision(a[key],0)).is_empty
  else:assert a[key].wkb==z[key].wkb if hasattr(a[key],'wkb')else a[key]==z[key]
restoredB=copy.deepcopy(b)
for row,old in zip(restoredB['generated_precision_state_ledger'],b0['generated_precision_state_ledger']):
 assert(row['new_generated_UUID'],row['role'])==(old['new_generated_UUID'],old['role'])
 if(row['new_generated_UUID'],row['role'])in allowed:row['unchanged_WKB_SHA256']=old['unchanged_WKB_SHA256']
assert restoredB==b0
"""
   source=source[:start]+replacement+source[end:]
   old="affected=set(json.loads((candidate/'affected-native-physical-net-list.json').read_bytes()))"
   new="affected=set(json.loads((H/'Q0-exact-R476-ground-contact-pose-r478/affected-native-physical-net-list.json').read_bytes()))"
   assert old in source;source=source.replace(old,new,1)
   source=source.replace("'generated_q_new_antipad_role_replay_current_native_pose_all6_flash_source_parity_refill_all_baselines_DRC_and_SI':'OPEN'","'generated_q_new_antipad_role_replay_current_native_pose_all6_flash_source_parity_refill_all_baselines_DRC_and_SI':'Host four-role exact canonical negative replay complete; native pose/all6/same-plane native source/fullfill/all baselines/DRC/DC/SI OPEN'")
   (H/'Q0-R488-final-owned-current-r490-derived-auditor.py').write_text(source)
 return builtins.compile(source,filename,mode,*args,**kwargs)
ns={'__file__':str(base),'__name__':'__main__','compile':scoped_compile};exec(scoped_compile(base.read_text(),str(base),'exec'),ns)
