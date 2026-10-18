"""Test exact supply obligations of the failed NEW In4 feed before rebuilding."""
import os,psutil
for task_env in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[task_env]='2'
task_process=psutil.Process();task_process.cpu_affinity(list(range(16,28)));task_process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json
from pathlib import Path
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from inventory import sha
M=H.parent/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
R=H/'REG-U25-DIC-SBC273-corrected-current-independent-full-audit-r368'
O=H/'FIELD5-failing-new-In4-feed-exact-withdrawal-obligations-r382'
UID='61cb8179-7754-5031-bbea-0da464bf816f';NET='/motherboard_power_entry/FIELD_5V'
def main():
 assert not O.exists();O.mkdir();g,h,b,q,actual=pickle.loads(M.read_bytes());prior=pickle.loads((R/'actual-drilled-current-groups.pkl').read_bytes())[NET];after={**actual,'zones':[z for z in actual['zones']if z['uuid']!=UID]};_,now=K.physical(after,NET,K.hole_context(after));a=K.root(prior,'L11003','2');n=K.root(now,'L11003','2');missing=K.keys(a)-K.keys(n);relations,loss=K.contact_losses(prior,now);pads=sorted({(r['ref'],str(r['pin']),r['uuid'])for r in a if r['kind']=='pad'and r['uuid']not in{r['uuid']for r in n if r['kind']=='pad'}});ports=[]
 for xs in now:
  named=sorted({(r.get('ref'),str(r.get('pin')))for r in xs if r['kind']=='pad'});barrels=sorted({r['uuid']for r in xs if r['kind']=='via'});ports.append({'physical_keys':len(K.keys(xs)),'named_pads':named,'barrel_UUIDs':barrels,'source_rooted':xs is n})
 result={'verdict':'FAILED_NEW_FIELD5_IN4_PLANE_WITHDRAWAL_SCOPE_ONLY_NOT_ADOPTION','current_model_sha256':sha(M),'failed_NEW_UUID':UID,'source_physical_keys_lost':[list(k)for k in sorted(missing)],'source_named_pads_lost':pads,'old_physical_relationship_losses':loss,'all_after_groups':ports,'changed_ground_fills_not_restored_in_this_probe':True,'no_actual_source_or_geometry_edit':True,'native_jobs':0,'adopted':False}
 (O/'receipt.json').write_text(json.dumps(result,indent=1,allow_nan=False)+'\n',encoding='utf-8');(O/'withdrawal-only-FIELD5-groups.pkl').write_bytes(pickle.dumps(now,protocol=5));print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'source_keys_lost':len(missing),'named_pads_lost':pads,'relationships_lost':len(loss),'groups':ports}),flush=True)
if __name__=='__main__':main()
