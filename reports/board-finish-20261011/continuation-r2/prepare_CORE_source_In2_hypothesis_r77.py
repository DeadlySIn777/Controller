"""Bind an explicit existing-barrel In2 hypothesis without altering any original native via."""
import os
for n in('OMP_NUM_THREADS','OPENBLAS_NUM_THREADS','MKL_NUM_THREADS'):os.environ[n]='2'
import copy,hashlib,json,pickle,sys
from pathlib import Path
from shapely import set_precision,get_precision
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import guarded_declared_settings_projection_r58 as N
import fast_contacts as F
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,r):p.write_text(json.dumps(r,indent=1)+'\n')
def main():
 parent=H/'SAFE-old-source-ground-reference-power-scope-proposal-r74';r=json.loads((parent/'receipt.json').read_bytes());assert sha(parent/'receipt.json')=='add5e6c16ffbc1a3b8b24f80268d451c169220268e83871fb2f391b88a4b0c92'and r['verdict']=='REMOVE_ONLY_REFERENCE_REPAIR_SOURCE_LOSS_REPAIR_REQUIRED';mp=parent/'model.pkl';assert sha(mp)==r['model_sha256'];g,h,b,z,oldprojected=pickle.loads(mp.read_bytes());h=copy.deepcopy(h);b=copy.deepcopy(b)
 out=H/'CORE-source-existing-barrel-In2-hypothesis-r77';assert not out.exists();out.mkdir();ledger=[]
 for q in z:
  for role in('shape','zone_outline_shape'):
   before=q[role].wkb;restored=set_precision(q[role],1e-6,mode='pointwise');assert restored.wkb==before,'Only exact generated operation metadata replay is authorized';q[role]=restored;ledger.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':digest(restored)})
 b['generated_precision_state_ledger']=ledger;b['restored_generated_grid_UUIDs']=sorted(q['uuid']for q in z);b['final_new_zone_coords_integer_nm_canonical_before_audit']=True;b['known_CORE1V2_source_regression_unresolved']=True
 v=next(q for q in h['vias']if q['uuid']=='f6ad6a15-3a41-4605-9ad5-72f4ba7d5d92');prior=copy.deepcopy(v);assert v['net']=='/CORE_1V2'and[v['x'],v['y'],v['d'],v['drill']]==[236.212,94.61,.5,.2]and set(v['flashed'])=={'F.Cu','In3.Cu','In4.Cu'}
 v['flashed']=['F.Cu','In2.Cu','In3.Cu','In4.Cu'];v['prospective_new_flash_requires_native_refill']=['In2.Cu','In4.Cu'];assert {k:x for k,x in prior.items()if k not in('flashed','prospective_new_flash_requires_native_refill')}=={k:x for k,x in v.items()if k not in('flashed','prospective_new_flash_requires_native_refill')}
 proposal=H/'sbc-power/core1v2-source-barrel-extra-In4-proposal-r111/extra-flash-obligation.json';assert sha(proposal)=='33c16b1ed6c7d3af6e8c16b146c342b6eb54d9b08c333ad3adbd3862c7024f2e';author=json.loads(proposal.read_bytes());chunk=Path(author['original_native_via_chunk_file']);assert sha(chunk)==author['original_native_via_chunk_sha256']=='15f2ab2a05736d9fce009a383f6fea3b79927a6fe45f1e74199848b7bfe8c7d7'
 put(out/'explicit-additional-In2-hypothesis.json',{'verdict':'PROSPECTIVE_EXISTING_CORE_BARREL_EXTRA_In2_REQUIRES_NEW_EXACT_COLLECTOR_AND_ACTUAL_NATIVE_FILL','parent_model_sha256':sha(mp),'original_native_board_sha256':author['parent_native_board_sha256'],'original_native_via_chunk_file':str(chunk.resolve()),'original_native_via_chunk_sha256':sha(chunk),'same_original_serialized_UUID_rawnet_position_size_drill_span':True,'actual_original_native_F_In3_retained':True,'prior_In4_proposal_file':str(proposal.resolve()),'prior_In4_proposal_sha256':sha(proposal),'expected_prior_host_geometry':prior,'expected_prospective_host_geometry':v,'only_declared_host_changes':['flashed','prospective_new_flash_requires_native_refill'],'full_load_A':.8,'all_foreign_contacts_reference_current_barrel_drop_thermal_and_native_annuli':'OPEN','no_native_unsuppression_or_save':True,'adopted':False})
 projected,retreat=N.projected(g,h,z);put(out/'full-projection-ledger.json',retreat);groups=F.graph(projected,'/CORE_1V2');root=next(xs for xs in groups if any(q['kind']=='pad'and(q['ref'],q['pin'])==('L2001','2')for q in xs));named=len({q['uuid']for q in root if q['kind']=='pad'and q['pin']});assert named==4,'An isolated prospective annulus alone is not source restoration'
 model=out/'model.pkl';model.write_bytes(pickle.dumps((g,h,b,z,projected),protocol=5));(out/'CORE-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));put(out/'receipt.json',{'verdict':'EXPLICIT_In2_HOST_HYPOTHESIS_SOURCE4_FAIL_PRESERVED_FEED_CONSTRUCTION_REQUIRED','parent_model_sha256':sha(mp),'model_sha256':sha(model),'precision_replay_WKB_exact':True,'generated_geometry_roles':len(ledger),'old_source_pad_loss_still_unresolved':21,'source_rooted_named_pads':named,'extra_flash_proposal_sha256':sha(out/'explicit-additional-In2-hypothesis.json'),'all_original_native_Cu_holes_outlines_pads_and_FP_poses_unchanged':True,'actual_native_In2_FLASH':'UNPROVEN','host_retention_and_PDN':'OPEN','native_jobs':0,'adopted':False});print('R77_IN2_HYPOTHESIS_SOURCE',named,sha(model),sha(out/'receipt.json'),flush=True)
if __name__=='__main__':main()
