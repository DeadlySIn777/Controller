"""Remove only NEW FIELD5 Cu for its measured original IO3-fill margin.

The existing IO3 split remains an explicit failed gate. No original native
outline, source, pad, track, via or unrelated generated role is changed.
"""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,time,copy,traceback
from pathlib import Path
from shapely import set_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import audit_aux_exact_raw as A
import guarded_declared_settings_projection_r58 as N
import immutable_local_fill_subtraction_r254 as IM
import restore_field_current_mixed_precision_states_r366 as MS
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from inventory import sha
B=H/'FIELD5-R385-minimal-R155-strict-filled-restoration-composition-r393'
O=H/'FIELD5-R393-only-new-plane-actual-IO3-margin-correction-r405'
UID='8d0d8533-168b-59d0-b231-cdd89cb7bd4e';FOREIGN='54921f4b-0308-4821-9549-ff9360bf05ca'
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def dg(s):return A.C.sha(s.wkb)
def literal(s):
 x=set_precision(s,0);assert x.wkb==s.wkb;return x
def main():
 assert not O.exists();O.mkdir();started=time.monotonic()
 assert sha(B/'model.pkl')=='df3e75059ea013087ddd8481e1f5bfe79e7915c2c3b4f34e2eaf1de9864acc13'
 g,h,b,z,c=pickle.loads((B/'model.pkl').read_bytes());MS.restore_bound_field_current_precision_states(b,z);b=copy.deepcopy(b)
 q=next(q for q in z if q['uuid']==UID);old={r:q[r]for r in('shape','zone_outline_shape')};foreign=next(r for r in c['zones']if r['uuid']==FOREIGN)
 # Regional selection never modifies the foreign floating coordinates.
 nearby=[s for s in L.poly(foreign['fills']['In2.Cu'])if s.intersects(old['zone_outline_shape'].buffer(.626))]
 shape=literal(unary_union(nearby));mask=literal(N.bounded_buffer(shape,.6251));f=O/'exact-current-native-IO3-.6251-cut.wkb';f.write_bytes(mask.wkb);rows=[]
 for role in ('shape','zone_outline_shape'):
  prior=literal(old[role]);after=set_precision(prior.difference(mask),1e-6,mode='pointwise');reserves=[]
  for i in range(32):
   gain=literal(after).difference(prior)
   if gain.is_empty:break
   gf=O/(role+'-'+str(i)+'-literal-gain.wkb');gf.write_bytes(gain.wkb);reserve=literal(N.bounded_buffer(gain,.0001));rf=O/(role+'-'+str(i)+'-explicit-100nm-negative.wkb');rf.write_bytes(reserve.wkb)
   after=set_precision(literal(after).difference(reserve),1e-6,mode='pointwise');reserves.append({'gain_file':str(gf.resolve()),'gain_sha256':sha(gf),'reserve_file':str(rf.resolve()),'reserve_sha256':sha(rf)})
  else:raise AssertionError('new FIELD5 canonical subset did not converge')
  assert literal(after).difference(prior).is_empty
  q[role]=after;rows.append({'UUID':UID,'role':role,'operation':'only_new_FIELD5_actual_foreign_native_fill_margin_remove_only','before_sha256':dg(prior),'after_sha256':dg(after),'removed_mm2':prior.difference(literal(after)).area,'literal_gain_empty':True,'required_mm':.625,'explicit_construction_mm':.6251,'foreign_literal_WKB_sha256':dg(shape),'mask_file':str(f.resolve()),'mask_sha256':sha(f),'canonical_negative_reserves':reserves})
 assert literal(q['shape']).difference(literal(q['zone_outline_shape'])).is_empty
 actual=[];fillrows=[]
 for x in c['zones']:
  if x['uuid']!=UID:actual.append(x);continue
  before=unary_union(L.poly(x['fills']['In2.Cu']));recs=IM.records(literal(q['shape']));after=unary_union(L.poly(recs));assert after.difference(before).is_empty
  actual.append({**x,'fills':{'In2.Cu':recs}});fillrows.append({'UUID':UID,'layer':'In2.Cu','before_sha256':dg(before),'after_sha256':dg(after),'literal_gain_empty':True,'removed_mm2':before.difference(after).area})
 final={**c,'zones':actual};states=[]
 for qq in z:
  for role in ('shape','zone_outline_shape'):
   states.append({'new_generated_UUID':qq['uuid'],'role':role,'grid_mm':0 if qq['uuid']in('ed7b6af5-93e5-5f20-8977-d10ca721564d','d8d8bdad-3845-5659-b172-4d0e231cdadc')and role=='shape' else 1e-6,'mode':'pointwise','unchanged_WKB_SHA256':dg(qq[role]),'exact_WKB_unchanged':True})
 b['generated_precision_state_ledger']=states;b['restored_generated_grid_UUIDs']=sorted(q['uuid']for q in z);b['FIELD5_R405_only_new_actual_margin_repair']={'parent_model_sha256':sha(B/'model.pkl'),'only_owned_UUID':UID,'original_IO3_fill_unchanged':True,'IO3_383_key_split':'REPAIR_REQUIRED_NOT_WAIVED'};MS.restore_bound_field_current_precision_states(b,z)
 put(O/'only-new-owned-role-margin-ledger.json',rows);put(O/'only-new-own-filled-record-ledger.json',fillrows);(O/'only-new-FIELD5-q-replacement.pkl').write_bytes(pickle.dumps(q,protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,final),protocol=5))
 # Qualify source geometry only for this narrow negative edit; retain all
 # IO3/source/reference/current/full-rule gates as separate outstanding work.
 _,groups=K.physical(final,L.norm(q['net']),K.hole_context(final));root=K.root(groups,'L11003','2');present={(r['ref'],str(r['pin']))for r in root if r['kind']=='pad'};need=[('U11017','8'),('U11017','5'),('R11071','1'),('C11064','1'),('R9039','1'),('C11080','1'),('U11013','1'),('U11013','3'),('R11051','1')];missing=[x for x in need if x not in present]
 gap=literal(q['shape']).distance(shape);assert gap>=.625,('new FIELD5 actual gap',gap)
 rec={'verdict':'NEW_FIELD5_MARGIN_REMOVE_ONLY_AND_NINE_SOURCE_TARGETS_PASS_IO3_SPLIT_REPAIR_REQUIRED'if not missing else'NEW_FIELD5_MARGIN_REMOVE_ONLY_SOURCE_TARGET_REPAIR_REQUIRED','parent_R393_model_sha256':sha(B/'model.pkl'),'model_sha256':sha(O/'model.pkl'),'only_q_UUID':UID,'no_discrete_original_native_definition_or_other_owned_role_changes':True,'actual_true_original_IO3_fill_gap_mm':gap,'required_mm':.625,'required_source_targets_missing':missing,'IO3_383_retained_keys_58_pads_split':'FAIL_REPAIR_REQUIRED','old_contact_source_reference_current_native_full_gates':'OPEN_SEPARATE','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started};put(O/'receipt.json',rec);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'model_sha256':rec['model_sha256'],'gap':gap,'source_targets_missing':missing}),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc()})
  raise
