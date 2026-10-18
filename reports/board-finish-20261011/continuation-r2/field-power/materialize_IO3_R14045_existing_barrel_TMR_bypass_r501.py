"""New-only R499 bypass and normal per-record original foreign-fill cuts.

No old source/geometry overlay, native original outline change, or claimed
current/native qualification. Same-net native union is a later exact scope.
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
M=H/'R155-FA-plus-IO3-TMR-individual-local-scope-witnesses-r491/model.pkl'
A=H/'IO3-R14045-conservative-true-cap-existing-barrel-TMR-bypass-r499'
O=H/'IO3-R14045-new-only-existing-barrel-TMR-materialization-r501'
def dg(s):return hashlib.sha256(s.wkb).hexdigest()
def lit(s):
 a=set_precision(s,0);assert a.wkb==s.wkb;return a
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def summary(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'length_mm':s.length,'bounds':None if s.is_empty else s.bounds,'WKB_SHA256':dg(s)}
def main():
 assert not O.exists();O.mkdir();started=time.monotonic()
 assert sha(M)=='c41d00e4c79e6374fbdc5a8167de451fbd4c84f8350cb41935cea3e0ae4a6abf'
 assert sha(A/'only-new-IO3-bypass-q-nominee.pkl')=='08f5a5dbff473f809e3a5b564b563467f93ba21f8a33b99737b18353cf7e17e8'
 g,h,b,qs,c=pickle.loads(M.read_bytes());MS.restore_bound_field_current_precision_states(b,qs)
 nominee=pickle.loads((A/'only-new-IO3-bypass-q-nominee.pkl').read_bytes());new=copy.deepcopy(nominee['q']);uid=new['uuid'];net=new['net'];layer=new['layer'];assert net=='/IO_3V3'and layer=='In2.Cu'
 freefile=A/'In2.Cu-20.0-exact-hard-body-free.wkb'
 from shapely import from_wkb
 free=from_wkb(freefile.read_bytes());canonical=[]
 for role in ('shape','zone_outline_shape'):
  before=new[role];after=set_precision(before,1e-6,mode='valid_output')
  assert free.covers(lit(after)),('canonical new body leaves unchanged R499 hard free',role)
  new[role]=after;canonical.append({'role':role,'nominee_sha256':dg(before),'integer_nm_sha256':dg(after),'only_new_role_canonicalization':True,'WKB_coordinate_change_explicit':before.wkb!=after.wkb})
 assert lit(new['shape']).difference(lit(new['zone_outline_shape'])).is_empty,('new physical outside native intent')
 from shapely.geometry import Point
 v=nominee['existing_target_via'];assert new['zone_outline_shape'].covers(Point(v['x'],v['y']))
 oldids={q['uuid']for q in qs};assert uid not in oldids
 actual=copy.deepcopy(c);dom=h['domains_normalized'];affected=[];operations=[];raw_locality=[]
 for z in actual['zones']:
  if layer not in z['fills']or L.norm(z['net'])==net:continue
  oldpoly=unary_union(L.poly(z['fills'][layer]));req=max(.15,float(z.get('clearance_mm',.15)),.15 if dom[L.norm(z['net'])]==dom[net]else .6)+.025
  cut=lit(N.bounded_buffer(new['zone_outline_shape'],req))
  if not oldpoly.intersects(cut):continue
  assert z['uuid']not in oldids,('R499 foreign owned body was supposed hard',z['uuid'])
  cutf=O/(z['uuid']+'-normal-new-plane-foreign-fill-mask.wkb');cutf.write_bytes(cut.wkb)
  oldrecords=copy.deepcopy(z['fills'][layer]);rr,proof=IM.subtract(oldrecords,[cut],O,z['uuid']+'-'+layer+'-normal-new-only-withdrawal')
  after=unary_union(L.poly(rr));gain=after.difference(oldpoly);assert gain.is_empty,('literal original record copper gain',z['uuid'],summary(gain))
  removed=oldpoly.difference(after);extra=removed.difference(cut);ef=O/(z['uuid']+'-raw-additional-negative-outside-normal-mask.wkb');ef.write_bytes(extra.wkb)
  local=lit(N.bounded_buffer(cut,.0001));outside=extra.difference(local);of=O/(z['uuid']+'-raw-negative-outside-normal-mask-plus-100nm.wkb');of.write_bytes(outside.wkb)
  if not outside.is_empty:raw_locality.append({'UUID':z['uuid'],'outside':summary(outside),'witness_file':str(of.resolve()),'not_waived':True})
  z['fills'][layer]=rr;operations.append({'UUID':z['uuid'],'raw_net':z['net'],'layer':layer,'original_zone_outline_settings_exact':True,'before_records':oldrecords,'after_records':rr,'normal_mask':cut,'per_record_proof':proof})
  affected.append({'UUID':z['uuid'],'raw_net':z['net'],'layer':layer,'before_sha256':dg(oldpoly),'after_sha256':dg(after),'removed_mm2':removed.area,'required_guard_mm':req,'normal_mask_file':str(cutf.resolve()),'normal_mask_sha256':sha(cutf),'literal_gain_EMPTY':True,'raw_extra_negative':summary(extra),'extra_outside_local_100nm_EMPTY':outside.is_empty})
  print('R501 fill',z['uuid'],z['net'],removed.area,'local',outside.is_empty,flush=True)
 native={k:new[k]for k in ('uuid','net','priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')}
 native['prospective_not_native']=True;native['fills']={layer:IM.records(lit(new['shape']))};actual['zones'].append(native)
 assert{k:v for k,v in actual.items()if k!='zones'}=={k:v for k,v in c.items()if k!='zones'}
 operation_by={row['UUID']:row for row in operations}
 for old,z in zip(c['zones'],actual['zones']):
  if z['uuid']not in operation_by:assert old==z
  else:assert{k:v for k,v in old.items()if k!='fills'}=={k:v for k,v in z.items()if k!='fills'};assert set(old['fills'])==set(z['fills'])
 qs.append(new);b=copy.deepcopy(b);b['restored_generated_grid_UUIDs']=sorted(q['uuid']for q in qs)
 b['generated_precision_state_ledger']+=[{'new_generated_UUID':uid,'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':dg(new[role])}for role in ('shape','zone_outline_shape')]
 b['IO3_native_TMR_retained_branch_bypass_r501']={'base_model_sha256':sha(M),'nominee_sha256':sha(A/'only-new-IO3-bypass-q-nominee.pkl'),'new_only_UUID':uid,'old_physical_native_via_unchanged':v['uuid'],'foreign_native_original_fill_only_scopes':len(operations),'same_net_equal_setting_native_overlap_union':'OPEN_PENDING_EXACT_MINIMAL_NORMALIZATION','raw_locality_failure_count':len(raw_locality),'all_inherited_R155_failures_retained':True,'R491_actual_branch_loss_not_yet_proved_restored':True}
 MS.restore_bound_field_current_precision_states(b,qs)
 put(O/'only-new-role-canonicalization.json',canonical);put(O/'original-foreign-filled-scope-ledger.json',affected);put(O/'raw-locality-failures.json',raw_locality)
 (O/'only-new-q-and-local-original-foreign-fill-operations.pkl').write_bytes(pickle.dumps({'new_q':new,'new_actual_zone':native,'fill_operations':operations},protocol=5))
 (O/'model.pkl').write_bytes(pickle.dumps((g,h,b,qs,actual),protocol=5))
 put(O/'receipt.json',{'status':'CONSTRUCTED_NEW_ONLY_BYPASS_SOURCE_CONTACT_REFERENCE_NATIVE_CURRENT_OPEN'if not raw_locality else'KNOWN_LOCALITY_FAILURE_DIAGNOSTIC_NO_ADOPTION','model_sha256':sha(O/'model.pkl'),'base_sha256':sha(M),'new_q_UUID':uid,'new_native_own_target_barrel_center_inside_intended':True,'new_native_own_drill_void_physical_only':True,'foreign_original_fill_scopes':affected,'raw_locality_failure_count':len(raw_locality),'all_original_h_g_discrete_holes_outlines_rules_exact':True,'all_unrelated_q_roles_and_current_record_arrays_exact':True,'new_discrete_or_holes':0,'native_equal_settings_same_raw_overlap_union':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started})
 print('R501 receipt',sha(O/'receipt.json'),'model',sha(O/'model.pkl'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'no_native_or_source_acceptance':True})
  raise
