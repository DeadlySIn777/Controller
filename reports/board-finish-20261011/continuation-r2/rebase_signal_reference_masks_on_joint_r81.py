"""Rebase only frozen remove-only signal shadows on the latest positive joint host state."""
import os
for n in('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import copy,hashlib,json,pickle,sys
from pathlib import Path
from shapely import set_precision
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import guarded_declared_settings_projection_r58 as N
import fast_contacts as F
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def root(gs,ref):return next(xs for xs in gs if any(q['kind']=='pad'and(q['ref'],q['pin'])==(ref,'2')for q in xs))
def main():
 parent=H/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214';assert sha(parent/'receipt.json')=='e8eaa4704155b733da2bf32b241a5dcca98d08b5d24d8e7b1ecf4e9b4df73d9e';mp=parent/'model.pkl';assert sha(mp)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';g,h,b,z,before=pickle.loads(mp.read_bytes());b=copy.deepcopy(b)
 masks=H/'SAFE-old-source-ground-reference-power-scope-proposal-r74';assert sha(masks/'receipt.json')=='add5e6c16ffbc1a3b8b24f80268d451c169220268e83871fb2f391b88a4b0c92';mr=json.loads((masks/'receipt.json').read_bytes());assert not mr['host_retained_relationships_pass']and mr['literal_power_scope104_pending_PDN']
 oldmp=H/'SAFE-monitor-real-source-reference-patch-r73/model.pkl';assert sha(oldmp)=='719da50c88dc6e2c64b988f81c850875f5f228e9f7407eab5c3cd17e8a44f011';oldz={q['uuid']:q for q in pickle.loads(oldmp.read_bytes())[3]};updates=pickle.loads((masks/'owned-new-zone-updates.pkl').read_bytes());rows=json.loads((masks/'remove-only-ledger.json').read_bytes());assert len(updates)==len(rows)==8;by={q['uuid']:q for q in z};changes=[]
 for q,row in zip(updates,rows):
  uid=q['uuid'];assert uid==row['UUID']and uid in oldz and uid in by;old=oldz[uid];actual=by[uid];assert (actual['net'],actual['layer'])==(q['net'],q['layer'])==(old['net'],old['layer']);assert digest(old['shape'])==row['before_WKB_sha256']and digest(q['shape'])==row['after_WKB_sha256']
  for role in('shape','zone_outline_shape'):
   assert q[role].difference(old[role]).is_empty,'Frozen masks may only remove from their exact old authority';cut=old[role].difference(q[role]);prior=actual[role];result=prior.difference(cut);assert result.difference(prior).is_empty and not result.is_empty;actual[role]=result;changes.append({'UUID':uid,'role':role,'exact_frozen_mask_WKB_sha256':digest(cut),'joint_prior_WKB_sha256':digest(prior),'joint_result_WKB_sha256':digest(result),'joint_removed_mm2':prior.difference(result).area,'joint_added_mm2':0.})
 f6=next(v for v in h['vias']if v['uuid']=='f6ad6a15-3a41-4605-9ad5-72f4ba7d5d92');assert f6['flashed']==['F.Cu','In3.Cu','In4.Cu']and f6['prospective_new_flash_requires_native_refill']=='In4.Cu','This In3 investigation may not inherit unproven new In2 copper'
 out=H/'joint-positive-head-signal-reference-mask-proposal-r81';assert not out.exists();out.mkdir();put(out/'remove-only-geometry-rebase-ledger.json',changes);ledger=[]
 for q in z:
  for role in('shape','zone_outline_shape'):
   beforewkb=q[role].wkb;restored=set_precision(q[role],1e-6,mode='pointwise');assert restored.wkb==beforewkb;q[role]=restored;ledger.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':digest(restored)})
 b['generated_precision_state_ledger']=ledger;b['restored_generated_grid_UUIDs']=sorted(q['uuid']for q in z);b['final_new_zone_coords_integer_nm_canonical_before_audit']=True;b['known_CORE1V2_source_regression_unresolved']=True
 current,retreat=N.projected(g,h,z);put(out/'full-projection-ledger.json',retreat);sources=[];groups={}
 for net,ref in[('/LOGIC_GND','J11001'),('/motherboard_motors/FIELD_GND','J11003'),('/motherboard_do/FIELD_B_0V','J11005'),('/IO_3V3','R18001'),('/CORE_1V2','L2001'),('/mc_local_power/CORE_5V','R11022')]:
  prior=root(F.graph(before,net),ref);after=F.graph(current,net);groups[net]=after;rr=root(after,ref);lost=F.discrete_keys(prior)-F.discrete_keys(rr);sources.append({'net':net,'source':ref+'.2','before_named_pads':len({q['uuid']for q in prior if q['kind']=='pad'and q['pin']}),'after_named_pads':len({q['uuid']for q in rr if q['kind']=='pad'and q['pin']}),'prior_source_keys_lost':[list(k)for k in sorted(lost)]});put(out/'source-checkpoint.json',sources);print('R81_SOURCE',net,sources[-1]['after_named_pads'],len(lost),flush=True)
 model=out/'model.pkl';model.write_bytes(pickle.dumps((g,h,b,z,current),protocol=5));(out/'source-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));put(out/'receipt.json',{'verdict':'EXACT_REMOVE_ONLY_MASKS_REBASED_SOURCE_REPAIR_REQUIRED_NOT_ACCEPTED','model_sha256':sha(model),'positive_joint_parent_sha256':sha(mp),'frozen_mask_receipt_sha256':sha(masks/'receipt.json'),'remove_only_delta_ledger_sha256':sha(out/'remove-only-geometry-rebase-ledger.json'),'sources':sources,'all104_power_candidates_separate_PDN_OPEN_and130real_signal_shadows_hard':True,'new_In2_flash_hypothesis_EXCLUDED':True,'all_existing_discrete_pads_FP_and_original_native_outlines_unchanged_from_positive_joint_head':True,'current_return_reference_all77_native_thermal_fault_transient':'OPEN','host_retention_and_adoption_flags':False,'native_jobs':0,'adopted':False});print('R81_FROZEN',sha(model),sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
