"""Exact R523 positive plus new-owned FAG In2 negative; no original overlay.

Withdraw only failed61cb, preserve all original IO3/copper/holes/outlines.
Source/contact/direct reference/current/native and positive union stay open.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy,time,hashlib,traceback
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
from shapely.geometry import Point
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import guarded_declared_settings_projection_r58 as N
import immutable_local_fill_subtraction_r254 as IM
import restore_field_current_mixed_precision_states_r366 as MS
from inventory import sha
M=H/'FA-IO3-native-TMR-minimal-current-two-owned-zone-packet-r515/model.pkl'
A=H/'FIELD5-all-source-finite-annulus-old-reference-hard-nomination-r523'
O=H/'FIELD5-R523-positive-only-owned-FG-local-negative-current-r525'
OLD='61cb8179-7754-5031-bbea-0da464bf816f';FG='e2fe644a-2849-5c69-8ebb-d1e94909cd4c'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def lit(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def summary(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds':None if s.is_empty else s.bounds,'sha256':dg(s)}
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();assert sha(M)=='4f70c8271d57724e41005d19c178ba597059085e7192955d7605cf20d501f862';assert sha(A/'only-one-new-FIELD5-actual-source-port-nominee.pkl')=='784b798040ba7d1f4586fd156a666453c82c44d006eaed134674475d31cd945b'
 g,h,b,q,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,q);b=copy.deepcopy(b);nominee=pickle.loads((A/'only-one-new-FIELD5-actual-source-port-nominee.pkl').read_bytes());new=copy.deepcopy(nominee['q']);uid=new['uuid'];layer='In2.Cu';raw=new['net'];canonical=[]
 from shapely import from_wkb
 free=from_wkb((A/'In2.Cu-80.0-exact-hard-body-free.wkb').read_bytes())
 for role in ('shape','zone_outline_shape'):
  before=new[role];new[role]=set_precision(before,1e-6,mode='valid_output');assert free.covers(lit(new[role]));canonical.append({'role':role,'before_sha256':dg(before),'after_sha256':dg(new[role]),'only_new_positive_canonicalization':True})
 v=nominee['existing_target_via'];assert new['zone_outline_shape'].covers(Point(v['x'],v['y']))
 old=next(z for z in q if z['uuid']==OLD);assert old['net']==raw and old['layer']=='In4.Cu';ground=next(z for z in q if z['uuid']==FG);assert ground['layer']==layer and L.norm(ground['net'])=='/motherboard_motors/FIELD_GND'
 cut=lit(N.bounded_buffer(new['zone_outline_shape'],.1751));cf=O/'only-owned-new-FG-normal-175-plus100nm-guard-cut.wkb';cf.write_bytes(cut.wkb);locality=lit(N.bounded_buffer(cut,2.0));role_rows=[];scopes=[];local_fail=[];changed=copy.deepcopy(ground)
 for role in ('shape','zone_outline_shape'):
  before=lit(ground[role]);after=set_precision(before.difference(cut),1e-6,mode='valid_output');negatives=[]
  for it in range(32):
   gain=lit(after).difference(before)
   if gain.is_empty:break
   assert gain.difference(locality).is_empty,('new FG gain remote from actual positive corridor',role,summary(gain))
   gf=O/(role+'-'+str(it)+'-raw-canonical-gain.wkb');gf.write_bytes(gain.wkb);reserve=lit(N.bounded_buffer(gain,.0001));rf=O/(role+'-'+str(it)+'-explicit100nm-new-owned-negative.wkb');rf.write_bytes(reserve.wkb);after=set_precision(lit(after).difference(reserve),1e-6,mode='valid_output');negatives.append({'raw_gain_file':str(gf.resolve()),'raw_gain_sha256':sha(gf),'negative_file':str(rf.resolve()),'negative_sha256':sha(rf)})
  else:raise AssertionError('new FG negative subset did not converge')
  removed=before.difference(lit(after));extra=removed.difference(cut);ef=O/(role+'-actual-extra-negative-outside-normal-cut.wkb');ef.write_bytes(extra.wkb)
  outside_local=extra.difference(locality)
  if not outside_local.is_empty:
   of=O/(role+'-raw-extra-negative-outside-corridor-locality.wkb');of.write_bytes(outside_local.wkb);local_fail.append({'role':role,'outside':summary(outside_local),'witness_file':str(of.resolve()),'not_waived':True})
  scope=[cut];witnesses=[];remaining=removed.difference(cut)
  for it in range(16):
   if remaining.is_empty:break
   wf=O/(role+'-'+str(it)+'-actual-negative-outside-declared-scope.wkb');wf.write_bytes(remaining.wkb);reserve=lit(N.bounded_buffer(remaining,.0001));rf=O/(role+'-'+str(it)+'-explicit-individual-100nm-scope.wkb');rf.write_bytes(reserve.wkb);scope.append(reserve);witnesses.append({'raw_negative':summary(remaining),'witness_file':str(wf.resolve()),'witness_sha256':sha(wf),'scope_file':str(rf.resolve()),'scope_sha256':sha(rf),'reserve_mm':.0001,'geometry_unchanged_by_scope_binding':True,'no_size_waiver':True});remaining=removed.difference(unary_union(scope))
  assert gain.is_empty and remaining.is_empty
  changed[role]=after;scopes+=scope;role_rows.append({'UUID':FG,'role':role,'before_sha256':dg(before),'after_sha256':dg(after),'removed_mm2':removed.area,'literal_gain_EMPTY':True,'all_removal_inside_individually_declared_scopes':True,'outside_corridor_locality_EMPTY':outside_local.is_empty,'canonical_gain_negative_operations':negatives,'individual_actual_negative_scope_witnesses':witnesses})
 actual=copy.deepcopy(c);fill_rows=[]
 for z in actual['zones']:
  if z['uuid']==OLD:continue
  if layer not in z['fills']or z['net']==raw:continue
  poly=unary_union(L.poly(z['fills'][layer]));req=max(float(z['clearance_mm']),.15 if h['domains_normalized'][L.norm(z['net'])]==h['domains_normalized'][L.norm(raw)]else .6)+.0251;mask=lit(N.bounded_buffer(new['zone_outline_shape'],req))
  if not poly.intersects(mask):continue
  assert z['uuid']==FG,('nominee unexpected foreign filled scope',z['uuid'],z['net']);before_records=copy.deepcopy(z['fills'][layer]);after_records,proof=IM.subtract(before_records,[mask],O,z['uuid']+'-only-new-FIELD5-local-withdrawal');after=unary_union(L.poly(after_records));gain=after.difference(poly);assert gain.is_empty
  removed=poly.difference(after);out=removed.difference(lit(N.bounded_buffer(mask,2.)));scope=[mask];witnesses=[];remaining=removed.difference(mask)
  if not out.is_empty:
   of=O/'actual-filled-raw-loss-outside-actual-corridor-locality.wkb';of.write_bytes(out.wkb);local_fail.append({'role':'actual-filled','outside':summary(out),'witness_file':str(of.resolve()),'not_waived':True})
  for it in range(16):
   if remaining.is_empty:break
   wf=O/('filled-'+str(it)+'-raw-negative-outside-prior-scope.wkb');wf.write_bytes(remaining.wkb);reserve=lit(N.bounded_buffer(remaining,.0001));rf=O/('filled-'+str(it)+'-individual100nm-negative-scope.wkb');rf.write_bytes(reserve.wkb);scope.append(reserve);witnesses.append({'raw_actual_negative':summary(remaining),'raw_file':str(wf.resolve()),'raw_sha256':sha(wf),'scope_file':str(rf.resolve()),'scope_sha256':sha(rf),'reserve_mm':.0001,'actual_geometry_unchanged_by_scope_binding':True,'not_waived':True});remaining=removed.difference(unary_union(scope))
  assert remaining.is_empty;z['fills'][layer]=after_records;fill_rows.append({'UUID':z['uuid'],'layer':layer,'raw_net':z['net'],'before_records':before_records,'after_records':after_records,'normal_mask':mask,'per_record_proof':proof,'individual_negative_scope_witnesses':witnesses,'before_sha256':dg(poly),'after_sha256':dg(after),'removed_mm2':removed.area,'literal_gain_EMPTY':True})
 assert len(fill_rows)==1
 native={k:new[k]for k in ('uuid','net','priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')};native['prospective_not_native']=True;native['fills']={layer:IM.records(lit(new['shape']))}
 actual['zones']=[z for z in actual['zones']if z['uuid']!=OLD]+[native];newq=[changed if z['uuid']==FG else z for z in q if z['uuid']!=OLD]+[new]
 for field in ('integer_nm_physical_rings','integer_nm_native_outline_rings'):changed.pop(field,None)
 assert{k:v for k,v in actual.items()if k!='zones'}=={k:v for k,v in c.items()if k!='zones'}
 for z in actual['zones']:
  if z['uuid']in(FG,uid):continue
  assert z==next(x for x in c['zones']if x['uuid']==z['uuid'])
 for z in newq:
  if z['uuid']in(FG,uid):continue
  assert z==next(x for x in q if x['uuid']==z['uuid'])
 b['restored_generated_grid_UUIDs']=sorted(x['uuid']for x in newq);states=[r for r in b['generated_precision_state_ledger']if r['new_generated_UUID']!=OLD]
 for row in states:
  if row['new_generated_UUID']==FG:row['unchanged_WKB_SHA256']=dg(changed[row['role']])
 states+=[{'new_generated_UUID':uid,'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':dg(new[role])}for role in ('shape','zone_outline_shape')];b['generated_precision_state_ledger']=states;b['FIELD5_all_source_IO3hard_actual_R525']={'exact_parent_sha256':sha(M),'only_failed_new_In4_withdrawn':OLD,'only_new_positive_added':uid,'only_new_owned_FG_cut':FG,'normal_cut_sha256':sha(cf),'original_IO3_all_roles_filled_arrays_exact':True,'former_In4_halo_restoration':'NOT_APPLIED_RAW_REFERENCE_FAILURES_REMAIN_BOUND','new_positive_same_raw_same_settings_union':'OPEN','full_current_A':.341130981,'routing_reserve_A':.36,'host_all_supply_or_production_acceptance':False}
 MS.restore_bound_field_current_precision_states(b,newq)
 put(O/'owned-FG-two-role-local-negative-ledger.json',role_rows);put(O/'raw-outside-corridor-locality-failures.json',local_fail);put(O/'only-new-positive-canonicalization.json',canonical)
 (O/'only-new-FIELD5-one-FG-negative-and-withdraw-old-preview.pkl').write_bytes(pickle.dumps({'exact_parent_model_sha256':sha(M),'only_new_positive_q':new,'only_new_actual_zone':native,'only_owned_FG_role_replacement':{'before_q':ground,'after_q':changed,'normal_mask':cut},'only_owned_FG_actual_fill_operations':fill_rows,'withdraw_only_old_q':old,'withdraw_only_old_actual_zone':next(z for z in c['zones']if z['uuid']==OLD),'new_tracks':[],'new_vias':[],'native_old_Cu_deletes':[]},protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,newq,actual),protocol=5))
 put(O/'receipt.json',{'status':'SPARSE_NEW_FIELD5_CAUSE_REPAIR_AND_OWNED_FG_NEGATIVE_CONSTRUCTED_ALL_DIRECT_SOURCE_REFERENCE_CURRENT_NATIVE_OPEN'if not local_fail else'KNOWN_LITERAL_LOCALITY_FAILURE_DIAGNOSTIC_ALL_GATES_OPEN','model_sha256':sha(O/'model.pkl'),'parent_sha256':sha(M),'R523_nominee_sha256':sha(A/'only-one-new-FIELD5-actual-source-port-nominee.pkl'),'new_positive_UUID':uid,'owned_FG_cut_UUID':FG,'withdraw_only_old_failed_In4_UUID':OLD,'role_rows':role_rows,'actual_filled_scopes':len(fill_rows),'raw_outside_corridor_locality_failures':local_fail,'original_IO3_all_filled_arrays_Cu_holes_and_all_unrelated_q_WKB_exact':True,'full_FA_source_return_current_A':4.58442937244,'full_FIELD5_A':.341130981,'routing_FIELD5_reservation_A':.36,'new_body_length_mm':nominee['length_mm'],'new_body_core_mm':nominee['core_width_mm'],'loop_drop_barrel_temperature_native_fill_cpp_all_contacts_sources_refs':'OPEN','all_original_design_source_rules_Cu_holes_unchanged':True,'R515_TMR_packet_independently_frozen_not_whole_overlay_for_integration':True,'R46513directrefs_383IO3_and_R15528refs_CORE_ROOT42_planner_FAIL_OPEN_retained':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start});print('R525 receipt',sha(O/'receipt.json'),'model',sha(O/'model.pkl'),'localfails',len(local_fail),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'no_model_native_or_source_acceptance':True})
  raise
