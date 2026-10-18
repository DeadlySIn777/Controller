"""Exact current FA-only native TMR no-zone removal with local proof.

Preserve source, original Cu, holes, all other q roles/settings/fills. No
ground refill, reference recovery, native staging, or acceptance is implied.
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
M=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
O=H/'R155-protected-FA-only-TMR-U14619-local-negative-construction-r477'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def lit(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();assert sha(M)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4'
 g,h,b,q,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,q);q0=copy.deepcopy(q);MS.restore_bound_field_current_precision_states(b,q0);b=copy.deepcopy(b);areas=[a for a in h['rule_areas']if a.get('name')=='TMR4WI_KEEPOUT_U14619'];assert len(areas)==1;area=unary_union(L.poly(areas[0]['outline']));uid=next(x['uuid']for x in q if x['uuid'].startswith('7ef3cb5e'));x=next(x for x in q if x['uuid']==uid);assert x['layer']=='In1.Cu'and L.norm(x['net'])=='/motherboard_power_entry/FIELD_A_24V_PROTECTED'
 mask=lit(N.bounded_buffer(area,.0251));f=O/'exact-native-area-plus-normal025-and-explicit100nm-reserve.wkb';f.write_bytes(mask.wkb);put(O/'native-rule-area-authority.json',{'native_area_record':areas[0],'actual_area_sha256':dg(area),'negative_mask_sha256':sha(f),'planner_margin_mm':.025,'explicit_construction_reserve_mm':.0001,'exact_area_only_no_exemption':True,'R473_receipt_sha256':sha(H/'R155-protected-FA-TMR4WI-U14619-native-rule-attribution-r473/receipt.json'),'R475_literal_receipt_sha256':sha(H/'R155-R9-protected-FA-native-TMR-exact-overlap-comparison-r475/receipt.json')})
 rows=[]
 for role in ('shape','zone_outline_shape'):
  before=x[role];after=set_precision(lit(before).difference(mask),1e-6,mode='valid_output');reserves=[]
  for it in range(32):
   gained=lit(after).difference(lit(before))
   if gained.is_empty:break
   gf=O/(role+'-'+str(it)+'-raw-canonical-gain.wkb');gf.write_bytes(gained.wkb);reserve=lit(N.bounded_buffer(gained,.0001));rf=O/(role+'-'+str(it)+'-explicit-only-owned-role-negative.wkb');rf.write_bytes(reserve.wkb)
   assert reserve.difference(lit(N.bounded_buffer(mask,.0005))).is_empty,('canonical negative outside local keepout scope',role,it)
   after=set_precision(lit(after).difference(reserve),1e-6,mode='valid_output');reserves.append({'raw_gain_file':str(gf.resolve()),'raw_gain_sha256':sha(gf),'negative_file':str(rf.resolve()),'negative_sha256':sha(rf)})
  else:raise AssertionError(('canonical subset failed',role))
  removed=lit(before).difference(lit(after));outside=removed.difference(lit(N.bounded_buffer(mask,.0005)));hit=lit(after).intersection(area)
  for name,sh in(('before',lit(before)),('after',lit(after)),('removed',removed),('outside-local-cut',outside),('native-area-remaining',hit)):(O/(role+'-'+name+'.wkb')).write_bytes(sh.wkb)
  assert gained.is_empty and outside.is_empty and hit.is_empty,('exact local role proof failed',role,gained.geom_type,outside.geom_type,hit.geom_type)
  x[role]=after;rows.append({'UUID':uid,'role':role,'before_sha256':dg(before),'after_sha256':dg(after),'removed_mm2':removed.area,'literal_after_minus_before_EMPTY':True,'removed_outside_declared_local_mask_plus500nm_EMPTY':True,'native_rule_area_overlap_EMPTY':True,'explicit_canonical_negative_reserves':reserves})
 assert lit(x['shape']).difference(lit(x['zone_outline_shape'])).is_empty
 actual=copy.deepcopy(c);fillrows=[]
 for z in actual['zones']:
  if z['uuid']!=uid:continue
  assert z['net']==x['net']and set(z['fills'])=={'In1.Cu'}
  recs=z['fills']['In1.Cu'];rr,proof=IM.subtract(recs,[mask],O,uid+'-In1-only-actual-keepout-negative');before=unary_union(L.poly(recs));after=unary_union(L.poly(rr));gained=after.difference(before);outside=before.difference(after).difference(lit(N.bounded_buffer(mask,.0005)))
  (O/'filled-aggregate-raw-gain.wkb').write_bytes(gained.wkb);(O/'filled-aggregate-raw-outside-local-loss.wkb').write_bytes(outside.wkb)
  assert gained.is_empty and outside.is_empty,('actual fill local proof failed',gained.geom_type,gained.area,outside.geom_type,outside.area)
  z['fills']['In1.Cu']=rr;fillrows.append({'UUID':uid,'layer':'In1.Cu','before_sha256':dg(before),'after_sha256':dg(after),'removed_mm2':before.difference(after).area,'per_record_negative_proof':proof,'literal_gain_EMPTY':True,'outside_local_loss_EMPTY':True})
 assert len(fillrows)==1
 for old,new in zip(q0,q):
  if old['uuid']==uid:assert{k:v for k,v in old.items()if k not in('shape','zone_outline_shape')}=={k:v for k,v in new.items()if k not in('shape','zone_outline_shape')};continue
  assert old['uuid']==new['uuid']and all(old[r].wkb==new[r].wkb for r in('shape','zone_outline_shape'))
 for old,new in zip(c['zones'],actual['zones']):
  if old['uuid']!=uid:assert old==new
 states=copy.deepcopy(b['generated_precision_state_ledger'])
 for row in states:
  if row['new_generated_UUID']==uid:row['unchanged_WKB_SHA256']=dg(x[row['role']]);assert row['grid_mm']==1e-6
 b['generated_precision_state_ledger']=states;b['FA_native_TMR_keepout_local_negative_r477']={'parent_sha256':sha(M),'owned_only_UUID':uid,'native_forbidden_area_name':areas[0]['name'],'exact_negative_mask_sha256':sha(f),'all_other_roles_and_current_arrays_exact':True,'existing_ground_planes_and_source_reference_not_reprojected':True,'full_FA_source_contact_current_all_native_nozone_gates':'OPEN','R155_raw28_refs_CORE_ROOT42_planner_FAIL_OPEN_retained':True,'R465_13refs_and_IO3_383split_not_overlaid':True};MS.restore_bound_field_current_precision_states(b,q)
 put(O/'exact-two-role-local-negative-ledger.json',rows);put(O/'exact-one-actual-fill-local-negative-ledger.json',fillrows);(O/'only-two-role-and-one-actual-fill-operation.pkl').write_bytes(pickle.dumps({'UUID':uid,'negative_mask':mask,'new_q':x,'new_actual_zone':next(z for z in actual['zones']if z['uuid']==uid),'prior_roles':next(z for z in q0 if z['uuid']==uid)},protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,q,actual),protocol=5));put(O/'receipt.json',{'status':'CONSTRUCTION_COMPLETE_LOCAL_NEGATIVE_ONLY_FULL_SOURCE_CURRENT_NATIVE_GATES_OPEN','model_sha256':sha(O/'model.pkl'),'parent_sha256':sha(M),'UUID':uid,'raw_net':x['net'],'roles':rows,'filled_scopes':1,'all_other_role_settings_discrete_holes_original_outlines_rules_exact':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start});print('R477 receipt',sha(O/'receipt.json'),'model',sha(O/'model.pkl'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'no_model_or_native_acceptance':True})
  raise
