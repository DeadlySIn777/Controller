"""Declare literal raw boolean-role geometry honestly before independent audit."""
import copy,hashlib,json,pickle
from pathlib import Path
from shapely import set_precision
H=Path(__file__).resolve().parent;OUT=H/'U10003-HOST-field-joint-current-exact-raw-precision-bound-r253';assert not OUT.exists();OUT.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
base=H/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262/model.pkl';before=pickle.loads(base.read_bytes());q0={z['uuid']:z for z in before[3]};priorrows={(r['new_generated_UUID'],r['role']):r for r in before[2]['generated_precision_state_ledger']}
mp=H/'U10003-HOST-shared-field-fresh-R262-sparse-current-diagnostic-r252/model.pkl';assert sha(mp)=='265810185640262c9d04f9bc7d2fd854723f4257d0ca38e1584c756b0ae52eb9';g,h,b,q,f=pickle.loads(mp.read_bytes());b=copy.deepcopy(b);ledger=[];changes=[]
for z in q:
 for role in ('shape','zone_outline_shape'):
  key=(z['uuid'],role);digest=hashlib.sha256(z[role].wkb).hexdigest();old=q0.get(z['uuid']);unchanged=old is not None and old[role].wkb==z[role].wkb
  if unchanged:row={**priorrows[key]};assert row['unchanged_WKB_SHA256']==digest
  elif old is None:row={'new_generated_UUID':z['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':digest};assert set_precision(z[role],1e-6,mode='pointwise').wkb==z[role].wkb
  else:row={'new_generated_UUID':z['uuid'],'role':role,'grid_mm':0.,'mode':'pointwise','unchanged_WKB_SHA256':digest};assert set_precision(z[role],0.,mode='pointwise').wkb==z[role].wkb
  ledger.append(row)
  if not unchanged:changes.append({**row,'before_WKB_sha256':hashlib.sha256(old[role].wkb).hexdigest()if old is not None else None,'raw_literal_boolean_cut_not_native_integer_emission':old is not None})
b['restored_generated_grid_UUIDs']=[z['uuid']for z in q];b['generated_precision_state_ledger']=ledger;b['final_new_zone_coords_integer_nm_canonical_before_audit']=False;b['explicit_raw_boolean_precision_transition']={'source_model_sha256':sha(mp),'source_ancestor_sha256':sha(base),'changed_roles':changes,'no_implicit_regrid_or_native_quantization_credit':True,'native_integer_intersection_splice_and_API_emission':'OPEN'}
out=OUT/'model.pkl';out.write_bytes(pickle.dumps((g,h,b,q,f),protocol=5));r={'verdict':'EXACT_RAW_ROLE_PRECISION_BOUND_JOINT_HOST_AUDIT_ONLY_NATIVE_INTEGER_EMISSION_OPEN','source_model_sha256':sha(mp),'ancestor_sha256':sha(base),'model_sha256':sha(out),'changed_precision_entries':changes,'g_h_q_all_coordinates_actual_filled_arrays_exact_unchanged':True,'only_binding_metadata_corrected':True,'global_canonical_native_geometry_claim':False,'native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(r,indent=1)+'\n');print('R253_BOUND_MODEL',sha(out),'RECEIPT',sha(OUT/'receipt.json'),flush=True)
