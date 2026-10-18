"""Cut only two new REG proposals against exact current native foreign Cu."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,copy,sys,time
from pathlib import Path
from shapely import set_precision
from shapely.geometry import box
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for x in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/x))
import audit_aux_exact_raw as A
import contact_layout as L
import guarded_declared_settings_projection_r58 as N
import immutable_local_fill_subtraction_r254 as IM
from inventory import sha
B=H/'REG-U25-corrected-DIC262-plus-corrected-SBC273-current-composition-r363'
O=H/'REG-U25-DIC-SBC273-two-new-REG-actual-fill-margin-repair-r364'
PAIRS=[('3af3a84a-f6ab-5839-87b7-a1335b6b7de1','54921f4b-0308-4821-9549-ff9360bf05ca','In2.Cu'),('61cb8179-7754-5031-bbea-0da464bf816f','c1d27fa1-452b-4e27-985d-5ad23644d800','In4.Cu')]
def dg(x):return A.C.sha(x.wkb)
def write(f,v):f.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def restore(b,z):
 zm={q['uuid']:q for q in z}
 for row in b['generated_precision_state_ledger']:
  q=zm[row['new_generated_UUID']];role=row['role'];assert dg(q[role])==row['unchanged_WKB_SHA256'];w=q[role].wkb;q[role]=set_precision(q[role],row['grid_mm'],mode=row['mode']);assert w==q[role].wkb
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();br=json.loads((B/'receipt.json').read_text());assert sha(B/'model.pkl')==br['model_sha256'];assert br['parent_sha256']=='52076bd44490e66b73dbd06994eea58a13f80152abdb7643cf2c3ae05e055739'
 g,h,b,z,c=pickle.loads((B/'model.pkl').read_bytes());restore(b,z);b=copy.deepcopy(b);zm={q['uuid']:q for q in z};fm={q['uuid']:q for q in c['zones']};rows=[];cutters={}
 for uid,foreign,layer in PAIRS:
  q=zm[uid];actual_foreign=unary_union(L.poly(fm[foreign]['fills'][layer]));assert set_precision(actual_foreign,0).wkb==actual_foreign.wkb
  oldshape=q['shape'];oldoutline=q['zone_outline_shape'];bounds=oldoutline.bounds;window=box(bounds[0]-1,bounds[1]-1,bounds[2]+1,bounds[3]+1);local_foreign=actual_foreign.intersection(window)
  # The 1 mm outer window exceeds the full .6251 mm guard, so omitted
  # foreign Cu cannot affect any old proposal point. No native point snaps.
  cut=N.bounded_buffer(local_foreign,.6251);cut=set_precision(cut,0);cf=O/(uid+'-exact-native-local-.6251-outward-guard.wkb');cf.write_bytes(cut.wkb);cutters[uid]=cut
  for role in ('shape','zone_outline_shape'):
   prior=q[role];literal=set_precision(prior,0);after=set_precision(literal.difference(cut),1e-6,mode='pointwise');reserve_rows=[]
   for k in range(32):
    gain=set_precision(after,0).difference(literal)
    if gain.is_empty:break
    reserve=set_precision(N.bounded_buffer(gain,.0001),0);rf=O/(uid+'-'+role+'-'+str(k)+'-explicit-local-negative-reserve.wkb');rf.write_bytes(reserve.wkb);gf=O/(uid+'-'+role+'-'+str(k)+'-literal-gain.wkb');gf.write_bytes(gain.wkb)
    after=set_precision(set_precision(after,0).difference(reserve),1e-6,mode='pointwise');reserve_rows.append({'literal_gain_sha256':sha(gf),'literal_gain_mm2':gain.area,'explicit_negative_reserve_sha256':sha(rf)})
   else:raise AssertionError('local remove-only generated boundary did not converge')
   assert set_precision(after,0).difference(literal).is_empty;q[role]=after
   removed=literal.difference(set_precision(after,0));df=O/(uid+'-'+role+'-exact-removed.wkb');df.write_bytes(removed.wkb)
   rows.append({'UUID':uid,'role':role,'foreign_native_UUID':foreign,'layer':layer,'before_sha256':dg(prior),'after_sha256':dg(after),'foreign_current_literal_WKB_sha256':dg(actual_foreign),'literal_gain_empty':True,'exact_removed_mm2':removed.area,'exact_removed_sha256':sha(df),'required_planner_gap_mm':.625,'declared_native_gap_mm':.6,'explicit_constructor_reserve_mm':.0001,'after_actual_native_full_Cu_gap_mm':set_precision(after,0).distance(actual_foreign),'local_outward_cutter_sha256':sha(cf),'local_integer_negative_reserves':reserve_rows})
  assert set_precision(q['shape'],0).difference(set_precision(q['zone_outline_shape'],0)).is_empty
 actual=[];filled=[]
 for old in c['zones']:
  qq=copy.deepcopy(old)
  if old['uuid']in cutters:
   for layer,rs in old['fills'].items():
    literal_current=unary_union(L.poly(rs));withdrawn=literal_current.difference(set_precision(zm[old['uuid']]['shape'],0))
    wf=O/(old['uuid']+'-'+layer+'-only-actual-current-vs-corrected-new-role-withdrawal.wkb');wf.write_bytes(withdrawn.wkb)
    rr,proof=IM.subtract(rs,[withdrawn],O,old['uuid']+'-'+layer+'-only-new-REG-margin');qq['fills'][layer]=rr;filled.append({'UUID':old['uuid'],'layer':layer,'exact_literal_current_role_withdrawal_sha256':sha(wf),'per_current_record_strict_subset_proof':proof})
  actual.append(qq)
 current={**h,'zones':actual};states=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   grid=0 if q['uuid']in('ed7b6af5-93e5-5f20-8977-d10ca721564d','d8d8bdad-3845-5659-b172-4d0e231cdadc')and role=='shape'else 1e-6;w=q[role].wkb;q[role]=set_precision(q[role],grid,mode='pointwise');assert w==q[role].wkb;states.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':grid,'mode':'pointwise','unchanged_WKB_SHA256':dg(q[role]),'exact_WKB_unchanged':True})
 b['generated_precision_state_ledger']=states;b['restored_generated_grid_UUIDs']=sorted(q['uuid']for q in z)
 assert len(states)==2*len(z) and {(r['new_generated_UUID'],r['role'])for r in states}=={(q['uuid'],role)for q in z for role in ('shape','zone_outline_shape')}
 for r in states:assert r['unchanged_WKB_SHA256']==dg(zm[r['new_generated_UUID']][r['role']])
 b['field_current_generated_geometry_precision_profile']='LITERAL_ZERO_ED_D8_PHYSICAL_AND_NM_ALL_OTHER_ROLES_R366'
 b['final_native_intended_zone_coords_integer_nm_canonical_before_audit']=True
 b['final_new_zone_coords_integer_nm_canonical_before_audit']=False
 b['mixed_precision_metadata_binding_explicit_no_geometry_change']=True
 b['REG_two_actual_native_foreign_margin_remove_only_repair']={'parent_sha256':sha(B/'model.pkl'),'only_NEW_owned_UUIDs':[p[0]for p in PAIRS],'no_original_native_geometry_changed':True,'required_planner_mm':.625,'native_mm':.6,'explicit_constructor_reserve_mm':.0001}
 write(O/'only-two-new-REG-local-margin-role-operation-ledger.json',rows);write(O/'only-two-new-REG-current-filled-subtraction-ledger.json',filled);write(O/'generated-precision-state-ledger.json',states);(O/'only-two-new-REG-replacement-objects.pkl').write_bytes(pickle.dumps([zm[p[0]]for p in PAIRS],protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,z,current),protocol=5))
 rec={'verdict':'LOCAL_REMOVE_ONLY_NEW_REG_ACTUAL_NATIVE_MARGIN_REPAIR_CONSTRUCTOR_COMPLETE_FULL_SOURCE_REFERENCE_GATES_OPEN','parent_sha256':sha(B/'model.pkl'),'only_new_REG_UUIDs':[p[0]for p in PAIRS],'all_other_owned_roles_and_all_discrete_native_rules_source_exact':True,'new_owned_original_definition_changes':0,'native_jobs':0,'board_written':False,'adopted':False,'new_full_source_reference_current_native':'OPEN','inherited_CORE93_041959_and_SBC_six_planner_failures_retained':True,'model_sha256':sha(O/'model.pkl'),'elapsed_seconds':time.monotonic()-start}
 write(O/'receipt.json',rec);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'model_sha256':rec['model_sha256'],'roles':rows}),flush=True)
if __name__=='__main__':main()
