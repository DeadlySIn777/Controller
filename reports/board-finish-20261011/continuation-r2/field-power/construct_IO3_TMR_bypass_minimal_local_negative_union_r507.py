"""Only two matching IO3 members; explicit local union-gain negatives.

The raw R505 gain remains rejected evidence. All original/generic profiles,
discrete geometry, ground arrays and unrelated new roles stay unchanged.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy,time,hashlib,traceback
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import guarded_declared_settings_projection_r58 as N
import immutable_local_fill_subtraction_r254 as IM
import restore_field_current_mixed_precision_states_r366 as MS
from inventory import sha
M=H/'IO3-R14045-new-only-existing-barrel-TMR-materialization-r501/model.pkl'
A=H/'IO3-TMR-bypass-minimal-two-member-native-union-diagnostic-r505'
O=H/'IO3-TMR-bypass-only-two-role-union-local-negative-r507'
UID='4f297f78-8d11-5be4-910e-9245f73fa249';ADD='a7168f4b-192a-52fe-a025-456a10753a51'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def lit(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def summary(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds':None if s.is_empty else s.bounds,'sha256':dg(s)}
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();assert sha(M)=='4085476528750a14f77b9d9c78a75c10914522a82932b38991f35241b7c77bd3';assert sha(A/'receipt.json')=='27a92a492f68f1f6308cc4eecd9d87427f4bf360fd76ab0ec0998c088349308f'
 g,h,b,qs,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,qs);old=next(x for x in qs if x['uuid']==UID);add=next(x for x in qs if x['uuid']==ADD);new=copy.deepcopy(old);b=copy.deepcopy(b)
 areas=[a for a in h['rule_areas']if a.get('name')=='TMR4WI_KEEPOUT_U14619'];assert len(areas)==1;nativearea=unary_union(L.poly(areas[0]['outline']));locality=lit(N.bounded_buffer(nativearea,2.0))
 candidate=pickle.loads((A/'only-two-role-union-candidate.pkl').read_bytes());rows=[];allreserves=[]
 for role in ('shape','zone_outline_shape'):
  before=lit(old[role]);addition=lit(add[role]);after=candidate[role];reserves=[]
  for it in range(32):
   gain=lit(after).difference(before).difference(addition)
   if gain.is_empty:break
   assert gain.difference(locality).is_empty,('union gain not at actual converter source join',role,it,summary(gain))
   gf=O/(role+'-'+str(it)+'-raw-union-gain.wkb');gf.write_bytes(gain.wkb);mask=lit(N.bounded_buffer(gain,.0001));mf=O/(role+'-'+str(it)+'-explicit-local-100nm-negative.wkb');mf.write_bytes(mask.wkb)
   assert mask.difference(locality).is_empty;after=set_precision(lit(after).difference(mask),1e-6,mode='valid_output');reserves.append({'iteration':it,'raw_gain_file':str(gf.resolve()),'raw_gain_sha256':sha(gf),'raw_gain':summary(gain),'negative_mask_file':str(mf.resolve()),'negative_mask_sha256':sha(mf),'reserve_mm':.0001,'no_size_waiver':True});allreserves.append(mask)
  else:raise AssertionError('minimal union gain reserves did not converge')
  loss=before.difference(lit(after));additional_loss=addition.difference(lit(after));scope=unary_union(allreserves);outside=loss.difference(scope)
  for label,sh in [('before',before),('after',after),('old_local_negative_loss',loss),('addition_local_negative_loss',additional_loss),('old_loss_outside_declared_scope',outside)]:(O/(role+'-'+label+'.wkb')).write_bytes(sh.wkb)
  assert gain.is_empty and outside.is_empty,('minimal union undeclared gain/loss',role,summary(gain),summary(outside))
  assert lit(after).intersection(nativearea).is_empty
  new[role]=after;rows.append({'role':role,'before_sha256':dg(before),'addition_sha256':dg(addition),'after_sha256':dg(after),'old_local_negative_loss':summary(loss),'addition_local_negative_loss':summary(additional_loss),'gained_outside_owned_addition_EMPTY':True,'old_loss_outside_explicit_local_negative_EMPTY':True,'native_forbidden_area_EMPTY':True,'explicit_negatives':reserves})
 q=[new if x['uuid']==UID else x for x in qs if x['uuid']!=ADD]
 # Retain old record arrays outside these exact local negatives. Append only
 # the addition after the same negatives; never re-union all old fill arrays.
 scope=unary_union(allreserves);actual=copy.deepcopy(c);by={z['uuid']:z for z in actual['zones']};z=by[UID];a=by[ADD];layer='In2.Cu';oldrecords=copy.deepcopy(z['fills'][layer]);newrecords=copy.deepcopy(a['fills'][layer]);ops=[]
 for label,rs in [('retained-old-IO3-records',oldrecords),('new-addition-records',newrecords)]:
  rr,proof=IM.subtract(rs,[scope],O,label);prior=unary_union(L.poly(rs));final=unary_union(L.poly(rr));gain=final.difference(prior);removed=prior.difference(final);outside=removed.difference(lit(N.bounded_buffer(scope,.0001)))
  assert gain.is_empty and outside.is_empty,('actual union local negative filled proof',label,summary(gain),summary(outside))
  ops.append({'label':label,'before_records':rs,'after_records':rr,'per_record_negative_proof':proof,'literal_gain_EMPTY':True,'extra_loss_outside_declared_local_scope_plus100nm_EMPTY':True})
 z['fills'][layer]=ops[0]['after_records']+ops[1]['after_records'];actual['zones']=[x for x in actual['zones']if x['uuid']!=ADD]
 assert{k:v for k,v in actual.items()if k!='zones'}=={k:v for k,v in c.items()if k!='zones'}
 for x in q:
  if x['uuid']==UID:continue
  prior=next(y for y in qs if y['uuid']==x['uuid']);assert x==prior
 new['constituent_proposal_UUIDs']=old.get('constituent_proposal_UUIDs',[])+[ADD]
 new.pop('integer_nm_physical_rings',None);new.pop('integer_nm_outline_rings',None)
 b['restored_generated_grid_UUIDs']=sorted(x['uuid']for x in q);b['generated_precision_state_ledger']=[r for r in b['generated_precision_state_ledger']if r['new_generated_UUID']!=ADD]
 for row in b['generated_precision_state_ledger']:
  if row['new_generated_UUID']==UID:row['unchanged_WKB_SHA256']=dg(new[row['role']])
 b['IO3_native_TMR_local_same_settings_union_r507']={'parent_sha256':sha(M),'only_members':[UID,ADD],'retained_UUID':UID,'withdraw_only_new_ADD_UUID':ADD,'local_negative_mask_WKB_sha256':dg(scope),'native_same_raw_equal_settings_overlap_resolved_by_union':True,'all_other_q_WKB_profiles_arrays_exact':True,'inherited_R155_current_reference_CORE_ROOT42_FAIL_OPEN_preserved':True,'fresh_source_geometry_oldref_current_native':'OPEN'}
 MS.restore_bound_field_current_precision_states(b,q)
 put(O/'only-two-role-local-union-negative-ledger.json',rows);(O/'only-two-member-role-and-local-fill-union-operation.pkl').write_bytes(pickle.dumps({'retained_UUID':UID,'withdraw_new_UUID':ADD,'prior_q':old,'prior_new_add_q':add,'new_q':new,'actual_local_record_operations':ops,'new_actual_zone':z,'explicit_negative_mask':scope},protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,q,actual),protocol=5))
 put(O/'receipt.json',{'status':'MINIMAL_MATCHED_UNION_CONSTRUCTED_LOCAL_NEGATIVES_SOURCE_NATIVE_CURRENT_OPEN','model_sha256':sha(O/'model.pkl'),'parent_sha256':sha(M),'same_all_nine_settings_exact':True,'only_two_member_roles_changed':True,'raw_R505_gain_failure_receipt_bound':sha(A/'receipt.json'),'role_rows':rows,'all_native_discrete_Cu_original_design_outlines_holes_rules_exact':True,'all_ground_current_record_arrays_source_reference_roles_exact':True,'only_native_equal_setting_conflict_removed':ADD,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start});print('R507 receipt',sha(O/'receipt.json'),'model',sha(O/'model.pkl'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'no_native_or_source_acceptance':True})
  raise
