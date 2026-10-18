"""Bind exact generated-only R62 GEOS operation metadata, retaining its failed source gate."""
import copy,hashlib,json,pickle
from pathlib import Path
from shapely import set_precision,get_precision
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def main():
 parent=H/'SAFE-old-source-ground-reference-remove-only-masks-r62';mp=parent/'model.pkl';r=json.loads((parent/'receipt.json').read_bytes());assert sha(mp)==r['model_sha256']=='c74d3eec9b440d9bb7eaf483937fb4599bbf889e8db872e6a97704ab6bd7baa9'and r['verdict']=='REMOVE_ONLY_REFERENCE_REPAIR_SOURCE_LOSS_REPAIR_REQUIRED'
 out=H/'SAFE-R62-exact-generated-precision-binding-r63';assert not out.exists();out.mkdir();g,h,b,z,current=pickle.loads(mp.read_bytes());b=copy.deepcopy(b);ledger=[];replay=[]
 for q in z:
  for role in ('shape','zone_outline_shape'):
   shape=q[role];before=shape.wkb;tag=get_precision(shape);result=set_precision(shape,1e-6,mode='pointwise');assert result.wkb==before,'Reject every changed coordinate/ring; only generated operation metadata may change';q[role]=result
   ledger.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':digest(result)});replay.append({'UUID':q['uuid'],'role':role,'loaded_grid_mm':tag,'restored_grid_mm':get_precision(result),'WKB_exact':digest(result)})
 b['generated_precision_state_ledger']=ledger;b['restored_generated_grid_UUIDs']=sorted(q['uuid']for q in z);b['final_new_zone_coords_integer_nm_canonical_before_audit']=True;b['reference_remove_only_parent_model_sha256']=sha(mp);b['known_CORE1V2_source_regression_unresolved']=True
 target=out/'model.pkl';target.write_bytes(pickle.dumps((g,h,b,z,current),protocol=5));(out/'generated-precision-replay.json').write_text(json.dumps(replay,indent=1)+'\n')
 (out/'receipt.json').write_text(json.dumps({'verdict':'EXACT_GENERATED_METADATA_BOUND_R62_SOURCE_FAIL_UNCHANGED','model_sha256':sha(target),'parent_model_sha256':sha(mp),'failed_parent_receipt_sha256':sha(parent/'receipt.json'),'all_physical_intended_WKB_old_native_Cu_holes_outlines_pads_and_poses_unchanged':True,'new_ground_ref_masks_source_CORE1V2_FAIL':'346oldkeys21previouslyjoinedpadsdetached','generated_precision_ledger_sha256':sha(out/'generated-precision-replay.json'),'adopted':False,'native_jobs':0,'board_written':False},indent=1)+'\n');print('R63_BIND',sha(target),flush=True)
if __name__=='__main__':main()
