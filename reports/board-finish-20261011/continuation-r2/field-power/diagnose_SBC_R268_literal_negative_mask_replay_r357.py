"""Frozen failure evidence: restore bound precision and inspect literal gains."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import pickle,json,sys
from pathlib import Path
from shapely import set_precision,get_precision
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import restore_SAFE_generated_precision_states_r168 as PS
from inventory import sha
O=H/'R268-negative-mask-literal-positive-replay-diagnostic-r357'
def main():
 assert not O.exists();O.mkdir();B=H.parent/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262';S=H.parent/'sbc-power/T4-R7-exact-sparse-owned-native-and-negative-fill-recipe-r268';assert sha(B/'model.pkl')=='64a1f6e1597c9d757b187c3b6db85d79685ee376399bdd4738f915b87b1a0144';_,_,b,q,_=pickle.loads((B/'model.pkl').read_bytes());PS.restore_bound_generated_precision_states(b,q);qm={z['uuid']:z for z in q};ops=pickle.loads((S/'only-two-DOB-generated-negative-role-masks.pkl').read_bytes());rows=[]
 for op in ops:
  before=qm[op['uuid']][op['role']];mask=op['exact_negative_mask'];assert sha_bytes(before.wkb)==op['before_WKB_sha256'];after=before.difference(mask);assert sha_bytes(after.wkb)==op['after_WKB_sha256'];oldzero=set_precision(before,0);newzero=set_precision(after,0);gain=newzero.difference(oldzero);f=O/(op['uuid']+'-'+op['role']+'-literal-positive.wkb');f.write_bytes(gain.wkb);rows.append({'UUID':op['uuid'],'role':op['role'],'before_SHA256':op['before_WKB_sha256'],'after_SHA256':op['after_WKB_sha256'],'before_required_grid_mm':get_precision(before),'mask_pickle_grid_mm':get_precision(mask),'after_grid_mm':get_precision(after),'exact_bound_after_reproduced':True,'mixed_precision_difference_area_mm2':after.difference(before).area,'literal_zero_tag_positive_mm2':gain.area,'literal_positive_file':str(f.resolve()),'literal_positive_SHA256':sha(f),'strict_negative_only':gain.is_empty})
 rec={'verdict':'FROZEN_NEGATIVE_MASK_REPLAY_HAS_LITERAL_GENERATED_POSITIVE_SCOPE_REPAIR_REQUIRED','corrected_DIC_R262_model_SHA256':sha(B/'model.pkl'),'SBC_R268_receipt_SHA256':sha(S/'receipt.json'),'exact_two_generated_negative_mask_packet_SHA256':sha(S/'only-two-DOB-generated-negative-role-masks.pkl'),'rows':rows,'geometric_clearance_source_or_reference_not_waived':True,'R356_failed_before_model_emission':True,'native_jobs':0,'board_written':False,'adopted':False};(O/'receipt.json').write_text(json.dumps(rec,indent=1)+'\n',encoding='utf-8');failed=H/'REG-U25-T4-R7-corrected-DIC262-sparse-current-composition-r356';(failed/'failure.json').write_text(json.dumps({'failure':'SBC_f486_exact_after_role_replay_assertion_failed_due_deepcopy_precision_drop','original_SCRIPT_SHA256':sha(H/'compose_REG_U25_T4_R7_corrected_DIC262_sparse_r356.py'),'independent_corrected_tag_replay_diagnostic_SHA256':sha(O/'receipt.json'),'no_model_emitted':not(failed/'model.pkl').exists(),'literal_positive_mask_designation_also_rejected_not_silently_fixed':True},indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'literal_positive_mm2':[r['literal_zero_tag_positive_mm2']for r in rows]}),flush=True)
def sha_bytes(v):
 import hashlib
 return hashlib.sha256(v).hexdigest()
if __name__=='__main__':main()
