"""Append only exact eight IO3 source-positive deltas to immutable SAFE R160."""
from pathlib import Path
import hashlib,json,pickle,copy
from shapely import set_precision
import restore_SAFE_generated_precision_states_r168 as PS
P=Path(__file__).resolve().parent;O=P/'original-IO3-full-unprojected-composition-r175'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
assert not O.exists();O.mkdir()
mp=P/'SAFE-repaired-owned-zone-normalization-r160/model.pkl';assert sha(mp)=='d7e0fe77a8ee25fef4e45538da29aa72809c102192879330c7a5b32a200e711b'
g,h,b,z,c=pickle.loads(mp.read_bytes());restore=PS.restore_bound_generated_precision_states(b,z)
qf=P/'original-IO3-r172-positive-snapshot-8/proposed-zones.pkl';assert sha(qf)=='d576613bad70e94d04e47822b0b7c42f30e7f1a72e91d4a4a9cf1f8335eac16c';new=pickle.loads(qf.read_bytes());assert len(new)==8
rf=P/'original-IO3-physical-port-bridges-r172/receipt.json';r=json.loads(rf.read_bytes());assert r['parent_model_sha256']==sha(mp) and not r['still_unrooted_original_IO3_keys']
assert not {q['uuid'] for q in z}&{q['uuid'] for q in new}
precision=[]
for q in new:
 assert q['net']=='/IO_3V3' and q['layer'] in ('In2.Cu','In3.Cu')
 for role in ('shape','zone_outline_shape'):
  sh=q[role];before=sh.wkb;fixed=set_precision(sh,1e-6,mode='pointwise');assert fixed.wkb==before;q[role]=fixed
  precision.append({'new_generated_UUID':q['uuid'],'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':hashlib.sha256(before).hexdigest(),'exact_authorizing_constructor_file':str((P/'construct_original_IO3_physical_port_bridges_r172.py').resolve()),'exact_authorizing_constructor_sha256':sha(P/'construct_original_IO3_physical_port_bridges_r172.py')})
pf=O/'added-IO3-generated-precision-state-ledger.json';pf.write_text(json.dumps(precision,indent=1)+'\n')
b=copy.deepcopy(b);b['generated_precision_state_ledger']+=precision;b['restored_generated_grid_UUIDs']+=[q['uuid'] for q in new]
b.update({'original_IO3_eight_source_join_delta_file':str(qf.resolve()),'original_IO3_eight_source_join_delta_sha256':sha(qf),'original_IO3_source_scope_receipt_file':str(rf.resolve()),'original_IO3_source_scope_receipt_sha256':sha(rf),'original_IO3_eight_join_precision_state_file':str(pf.resolve()),'original_IO3_eight_join_precision_state_sha256':sha(pf),'original_IO3_predecessor_source_keys':2839,'original_IO3_scope_source_keys':3687,'original_IO3_originally_connected_pad_track_via_groups_rejoined_in_selected_projection':True,'original_IO3_pad_free_old_branch_and23_original_isolated_named_pad_gates':'OPEN','all_full_foreign_contact_reference_native_current_after_append':'REQUIRED','root_R55_actual_return_preserved_as_hard_only_not_appended':True})
out=O/'unprojected-model.pkl';out.write_bytes(pickle.dumps((g,h,b,z+new,None),protocol=5))
(O/'receipt.json').write_text(json.dumps({'verdict':'EXACT_EIGHT_IO3_SOURCE_POSITIVE_ADDITIVE_DELTA_FULL_GATES_REQUIRED','parent_model_sha256':sha(mp),'new_IO3_delta_sha256':sha(qf),'new_model_sha256':sha(out),'old_discrete_native_source_or_zone_definition_changes':0,'owned_new_zone_count':len(z)+len(new),'appended_zone_UUIDs':[q['uuid'] for q in new],'appended_precision_state_sha256':sha(pf),'existing_precision_replay':restore,'board_written':False,'native_jobs':0,'script_sha256':sha(Path(__file__))},indent=1)+'\n')
print('ORIGINAL_IO3_FULL_UNPROJECTED',len(z)+len(new),sha(out))
