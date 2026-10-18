"""Exact ordered corrected SBC operation replay on the current field head."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'compose_only_T4_sparse_on_current_field_r361.py').read_text(encoding='utf-8')
s=s.replace('REG-U25-corrected-DIC262-plus-only-T4-current-composition-r361','REG-U25-corrected-DIC262-plus-corrected-SBC273-current-composition-r363')
s=s.replace('T4-R7-exact-sparse-owned-native-and-negative-fill-recipe-r268','T4-R7-exact-sparse-owned-native-and-negative-fill-recipe-r273')
s=s.replace("T=H.parent/'sbc-power/T4-duplicate-CORE5-fullwidth-detour-nominee-r256'","T=S")
s=s.replace('a89ae74f70f1798d4fa3b5e831a5140829850b5b7d58abec65fa80a8eba5f467','97bc789fb90e688dc2b78c6f24a4877d4b7497055023a1748935c55a4a274692')
s=s.replace("T/'proposed-discrete.pkl'","T/'only-owned-new-discrete-and-four-exact-deletes.pkl'")
s=s.replace('9b8150b8daa7bff3b51e3381a1654d0629294dcdef41d2919555f63313fb9c8d','c612d423566e2af6af4a204f8a2afdbfeb049091de337428f598c397777abb40')
s=s.replace("==(7,0,2)","==(10,1,4)").replace('assert len(rows)==2','assert len(rows)==4')
s=s.replace("for t in td['tracks']:assert t['uuid'] not in old and native.raw(L.norm(t['net']))==t['net']","for t in td['tracks']+td['vias']:assert t['uuid'] not in old and native.raw(L.norm(t['net']))==t['net']")
s=s.replace(" h['tracks']=[t for t in h['tracks']if t['uuid']not in td['removed']]+td['tracks']"," h['tracks']=[t for t in h['tracks']if t['uuid']not in td['removed']]+td['tracks'];h['vias']+=td['vias']")
s=s.replace("SB.cutters(td['tracks'],oldbody","SB.cutters(td['tracks']+td['vias'],oldbody")
s=s.replace(" for q in z:\n  for role in ('shape','zone_outline_shape'):\n   prior=", " for q in z:\n  if q['uuid']=='f4863c44-a057-598a-aef7-adca7cfb15f1':continue\n  for role in ('shape','zone_outline_shape'):\n   prior=",1)
needle=' actual=[];fills=[]'
addition="""
 from shapely import from_wkb
 manifest=json.loads((S/'required-exact-current-filled-cut-and-local-negative-ledger-manifest.json').read_text())
 for path,digest in manifest.items():assert sha(Path(path))==digest
 assert sha(S/'only-two-DOB-generated-negative-role-masks.pkl')=='1f3376665b4d4b294f2fbaa12d0e0f03bcfa4d05a4c968880b8757251e75400b'
 for op in json.loads((S/'ordered-exact-DOB-normal-antipad-plus-local-negative-replay.json').read_text()):
  q=zm[op['UUID']];role=op['role'];prior=q[role];assert dg(prior)==op['exact_before_WKB_sha256']
  nf=Path(op['normal_antipad_file']);assert sha(nf)==op['normal_antipad_sha256'];normal=from_wkb(nf.read_bytes())
  after=prior.difference(normal);assert dg(after)==op['rejected_after_first_mask_WKB_sha256']
  steps=[]
  for step in op['ordered_local_negative_reserve_steps']:
   file=next(Path(f)for f,sh in manifest.items()if sh==step['explicit_local_reserve_sha256'] and 'explicit100nm-local-role-negative-mask' in f)
   cc=from_wkb(file.read_bytes());w=cc.wkb;cc=set_precision(cc,1e-6,mode='pointwise');assert cc.wkb==w
   after=after.difference(cc);steps.append({'file':str(file),'sha256':sha(file)})
  assert dg(after)==op['exact_repaired_after_WKB_sha256'];assert set_precision(after,0).difference(set_precision(prior,0)).is_empty
  q[role]=after;role_rows.append({'UUID':q['uuid'],'role':role,'before_sha256':dg(prior),'after_sha256':dg(after),'literal_gain_empty':True,'ordered_normal_antipad':str(nf),'ordered_local_negative_steps':steps,'R273_exact_after_and_zero_grid_proved':True})
 actual=[];fills=[]"""
assert s.count(needle)==1;s=s.replace(needle,addition)
s=s.replace("'only_T4_sparse_owned_current_replay'","'corrected_SBC273_sparse_owned_current_replay'")
s=s.replace("'R7_excluded':True","'R7_corrected_R273_included':True")
s=s.replace('EXPLORATORY_ONLY_FROZEN_T4_SPARSE_REPLAY_FULL_CURRENT_JOINT_GATES_OPEN','EXPLORATORY_CORRECTED_SBC273_SPARSE_REPLAY_FULL_CURRENT_JOINT_GATES_OPEN')
s=s.replace("'new_tracks':7,'new_vias':0,'exact_before_deletes':2","'new_tracks':10,'new_vias':1,'exact_before_deletes':4")
s=s.replace("'R7_role_masks_not_appended':True","'R7_role_masks_corrected_literal_no_gain':True")
s=s.replace('only-T4','corrected-SBC273')
exec(compile(s,str(H/'compose_only_T4_sparse_on_current_field_r361.py'),'exec'))
