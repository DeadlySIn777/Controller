"""Exact root five/one-margin delta onto native-proved CORE1V2 head.

No stale model/h replacement, no unaccepted six-feed REG or DI6/DI15 scope.
Fresh whole projection and every retained-contact/reference gate follows.
"""
from pathlib import Path
import sys,pickle,json,hashlib,copy
H=Path(__file__).resolve().parent.parent
sys.path.insert(0,str(H/'sbc-power'));sys.path.insert(0,str(H/'field-power'))
O=H/'sbc-power/safe-ROOT22-CORE1V2-composition-r148'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def main():
 assert not O.exists();O.mkdir()
 mp=H/'sbc-power/CORE1V2-source-native-outline-correction-r135/model.pkl'
 rp=H/'safe-logic-five-and-fag-margin-r22/model.pkl';rr=rp.parent/'receipt.json'
 dp=H/'sbc-power/safe-joint-exact-delta-inspection-r147/receipt.json'
 assert sha(mp)=='729c76b8ef0ec7ec8af92ca287f3e8663741e9303bc5dcf3e10fb9b4af3bceca'
 assert sha(rp)=='014b37594d378cd3e1a606cb1c06a0ad0b1b3ffea5cb836132bfaeec80d3a52a'
 assert sha(rr)=='988c0f5d7fad8966699640e8c0c74ab5a23df99ed9c29eb1f4509f2a0f6cdcbe'
 d=json.loads(dp.read_bytes());rows=next(r for r in d['rows'] if r['label']=='root-safe-R22')
 assert all(not ids for values in rows['discrete_delta'].values() for ids in values.values())
 old,h,b,z,prior=pickle.loads(mp.read_bytes());root=pickle.loads(rp.read_bytes());rz={q['uuid']:q for q in root[3]};z=copy.deepcopy(z);b=copy.deepcopy(b);by={q['uuid']:q for q in z};ledger=[]
 for row in rows['owned_zone_delta']:
  uid=row['UUID'];q=rz[uid]
  if row['operation']=='add':
   assert uid not in by and digest(q['shape'])==row['physical_sha256'] and digest(q.get('zone_outline_shape',q['shape']))==row['outline_sha256'];z.append(copy.deepcopy(q));ledger.append(row)
  else:
   assert uid=='d5e1a664-0428-5fe4-aaa9-7887f79adfe7';o=by[uid]
   assert digest(o['shape'])==row['physical_before_sha256'] and digest(o.get('zone_outline_shape',o['shape']))==row['outline_before_sha256']
   assert not q['shape'].difference(o['shape']).area and not q.get('zone_outline_shape',q['shape']).difference(o.get('zone_outline_shape',o['shape'])).area
   z=[copy.deepcopy(q) if r['uuid']==uid else r for r in z];ledger.append(row)
 assert len(ledger)==6 and len(z)==len(prior['zones'])-len(h['zones'])+5
 b.update({'SAFE_ROOT22_exact_delta_model_file':str(rp.resolve()),'SAFE_ROOT22_exact_delta_model_sha256':sha(rp),'SAFE_ROOT22_exact_delta_receipt_file':str(rr.resolve()),'SAFE_ROOT22_exact_delta_receipt_sha256':sha(rr),'SAFE_CORE1V2_native_corrected_model_file':str(mp.resolve()),'SAFE_CORE1V2_native_corrected_model_sha256':sha(mp),'SAFE_selected_native_CORE1V2_source_proof_file':str((H/'core1v2-native-diagnostic-r138/independent-selected-CORE1V2-r139.json').resolve()),'SAFE_accepted_field_later_scope':'None beyond pinned R111 baseline; six-feed R130 retained reference gate is open','SAFE_unaccepted_DI6_reference_DI15_supply_carves_excluded':True,'host_all_supply_rooted':False,'SAFE_incomplete_supply_obligations':['CORE1V2 divider and C1024','IO3 original bare pads/old branches','REG remaining bare pads and later feed reference gates'],'all_original_contact_reference_native_current_gates_required':True})
 (O/'exact-owned-root-delta.json').write_text(json.dumps(ledger,indent=1)+'\n')
 f=O/'unprojected-model.pkl';f.write_bytes(pickle.dumps((old,h,b,z,None),protocol=5))
 (O/'receipt.json').write_text(json.dumps({'verdict':'EXACT_SAFE_OWNED_ROOT_DELTA_COMPOSED_FRESH_UNION_PROJECTION_AND_ALL_GATES_REQUIRED','unprojected_model_sha256':sha(f),'CORE1V2_parent_model_sha256':sha(mp),'root_SAFE_model_sha256':sha(rp),'root_delta_sha256':sha(O/'exact-owned-root-delta.json'),'owned_zone_count':len(z),'new_root_shapes':5,'new_root_owned_margin_replacements':1,'new_Cu_holes_or_FP_changes':0,'host_all_supply_rooted':False,'full_original198b_dc936_retention_reference_analytic_native_current':'OPEN','board_written':False,'native_jobs':0},indent=1)+'\n')
 print('SAFE_ROOT22_CORE1V2_COMPOSED',len(z),sha(f),flush=True)
if __name__=='__main__':main()
