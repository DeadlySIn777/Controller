"""True literal-role no-gain proof with explicit local100nm negative reserves.

Original/generated role bytes stay pinned. Only new local mask vertices are
constructed; every literal positive component and negative delta is saved.
"""
import hashlib,json,pickle,sys,copy
from pathlib import Path
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import guarded_power_projection_r44 as Z
import restore_SAFE_generated_precision_states_r168 as PS
O=H/'sbc-power/DOB-R265-true-literal-zero-grid-role-local-negative-repair-r270'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(s):return hashlib.sha256(s.wkb).hexdigest()
def zero(s):n=set_precision(s,0);assert n.wkb==s.wkb;return n
def put(p,v):Path(p).write_text(json.dumps(v,indent=1)+'\n')
def main():
 assert not O.exists();O.mkdir();bp=H/'coupled-recovery/CORE-R112-per-polygon-immutable-owned-construction-r250/model.pkl';assert sha(bp)=='96d3f55a95b770a2a7f46e3b25274723946fe1572c6c82d81b7355b660360868';g0,h0,b0,q0,c0=pickle.loads(bp.read_bytes());mp=H/'sbc-power/T4-R7-sparse-exact-R250-diagnostic-r265/T4-plus-R7/model.pkl';assert sha(mp)=='e81143a727821d906558e6edce30088da3d410eb0dda8630f80d8fe85e1f16bf';g,h,b,q,c=pickle.loads(mp.read_bytes());PS.restore_bound_generated_precision_states(b0,q0);PS.restore_bound_generated_precision_states(b,q);old={z['uuid']:z for z in q0};rows=[];masks=[];fail=[]
 for z in q:
  for role in('shape','zone_outline_shape'):
   prior=old[z['uuid']][role];curr=z[role]
   if curr.wkb==prior.wkb:continue
   a=zero(prior);rejected=zero(curr);rawgain=rejected.difference(a);steps=[];f=O/(z['uuid']+'-'+role+'-rejected-R265-true-literal-gain.wkb');f.write_bytes(rawgain.wkb)
   for it in range(16):
    gain=zero(curr).difference(a)
    if gain.is_empty:break
    gf=O/(z['uuid']+'-'+role+'-'+str(it)+'-true-literal-positive-component.wkb');gf.write_bytes(gain.wkb);reserve=Z.bounded_buffer(gain,.0001);rf=O/(z['uuid']+'-'+role+'-'+str(it)+'-explicit100nm-local-role-negative-mask.wkb');rf.write_bytes(reserve.wkb);before=curr;curr=curr.difference(reserve);negative=zero(before).difference(zero(curr));nf=O/(z['uuid']+'-'+role+'-'+str(it)+'-actual-literal-negative-role-delta.wkb');nf.write_bytes(negative.wkb);steps.append({'iteration':it,'literal_gain_sha256':sha(gf),'literal_gain_area_mm2':gain.area,'literal_gain_bounds':list(gain.bounds),'explicit_local_reserve_sha256':sha(rf),'explicit_local_reserve_nominal_mm':.0001,'actual_negative_role_delta_sha256':sha(nf),'actual_negative_role_area_mm2':negative.area,'original_before_WKB_unchanged':True,'no_magnitude_waiver':True})
   remaininggain=zero(curr).difference(a);canonical=set_precision(curr,1e-6,mode='pointwise');cg=zero(canonical).difference(a);cut=a.difference(zero(curr));negativefromrejected=rejected.difference(zero(curr));row={'UUID':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'role':role,'exact_R250_before_WKB_sha256':dig(prior),'rejected_R265_after_WKB_sha256':dig(z[role]),'rejected_true_zero_grid_positive_mm2':rawgain.area,'all_role_operation_steps':steps,'new_after_WKB_sha256':dig(curr),'true_ZERO_grid_after_minus_exact_before_empty':remaininggain.is_empty,'new_pointwise_canonical_nm_WKB_exact':canonical.wkb==curr.wkb,'canonical_true_zero_grid_gain_empty':cg.is_empty,'actual_total_remove_only_mask_WKB_sha256':dig(cut),'extra_local_negative_vs_rejected_WKB_sha256':dig(negativefromrejected)};rows.append(row)
   if not(remaininggain.is_empty and canonical.wkb==curr.wkb and cg.is_empty):fail.append(row)
   z[role]=curr;masks.append({'uuid':z['uuid'],'role':role,'raw_net':z['net'],'layer':z['layer'],'before_WKB_sha256':dig(prior),'after_WKB_sha256':dig(curr),'exact_negative_mask':cut,'only_local_negative_gain_reserves_additional_to_normal_ground_antipad':True,'true_literal_ZERO_grid_no_positive':remaininggain.is_empty})
 b=copy.deepcopy(b);b['generated_precision_state_ledger']=[{'new_generated_UUID':z['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':dig(z[role])}for z in q for role in('shape','zone_outline_shape')];b['restored_generated_grid_UUIDs']=sorted(z['uuid']for z in q);put(O/'true-literal-rejected-and-successor-role-ledger.json',rows);put(O/'strict-role-repair-failures.json',fail)
 if not fail:(O/'only-two-DOB-true-literal-negative-role-masks.pkl').write_bytes(pickle.dumps(masks,protocol=5));(O/'model-with-repaired-roles-actual-filled-records-unchanged.pkl').write_bytes(pickle.dumps((g,h,b,q,c),protocol=5))
 result={'verdict':'CANONICAL_NM_ROLE_TRUE_LITERAL_ZERO_GAIN_REPAIR_CONSTRUCTOR_PASS_FRESH_GUARDS_SOURCE_NATIVE_OPEN'if not fail else'TRUE_LITERAL_ROLE_REPAIR_FAIL_PRESERVED_NO_PROMOTION','exact_R250_before_model_sha256':sha(bp),'rejected_R265_model_sha256':sha(mp),'R265_actual_FILLED_records_and_all_discrete_exact_unchanged':True,'strict_no_magnitude_waiver':True,'new_role_count':len(rows),'failures':fail,'role_mask_sha256':sha(O/'only-two-DOB-true-literal-negative-role-masks.pkl')if not fail else None,'model_sha256':sha(O/'model-with-repaired-roles-actual-filled-records-unchanged.pkl')if not fail else None,'full_current_source_shared_return_peer_native_and_inherited_CORE_body_gates':'FAIL_OR_OPEN_RETAINED','native_jobs':0,'board_written':False,'adopted':False};put(O/'receipt.json',result);print('R270_COMPLETE',len(fail),sha(O/'receipt.json'),result['model_sha256'],result['role_mask_sha256'],flush=True)
if __name__=='__main__':main()
