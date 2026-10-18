"""Fresh exact source/reference gate for the local original-rim restoration."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,time
from pathlib import Path
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import contact_layout as L
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import physical_reference_losses_r3_zero_r208 as RF
from inventory import sha
R=H/'FIELD5-R385-minimal-R155-strict-aggregate-boundary-cut-rim-restoration-r423'
G=H/'FIELD5-R393-current-independent-all-contact-source-reference-audit-r395'
B=H.parent/'coupled-recovery/DIC-C1022-exact-R250-original-guard-construction-r262'
O=H/'FIELD5-R423-original-rim-fresh-drilled-source-reference-gate-r429'
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();started=time.monotonic();assert sha(R/'model.pkl')=='b2f5b0c2becbc538fb53ba292298f5beb2e29da7bdd9ddd779073a739f35d250'
 g,h,b,q,c=pickle.loads((R/'model.pkl').read_bytes());_,bh,_,_,before=pickle.loads((B/'model.pkl').read_bytes());old=pickle.loads((G/'actual-drilled-before-groups.pkl').read_bytes());removed={t['uuid']for t in bh['tracks']}-{t['uuid']for t in h['tracks']};ctx=K.hole_context(c);groups={};rows=[]
 for net,ref,pin in K.ROOTS[:3]:
  _,n=K.physical(c,net,ctx);groups[net]=n;a=old[net];_,contactbad=K.contact_losses(a,n,removed);ar=K.root(a,ref,pin);nr=K.root(n,ref,pin);lost=K.keys(ar)-{('track',u,ly)for u in removed for ly in K.LAYERS}-K.keys(nr);bad,proof=RF.audit(before,K.source_refs(ar),K.source_refs(nr),net,removed)
  rows.append({'net':net,'source':ref+'.'+pin,'old_contact_losses':contactbad,'prior_source_keys_lost':[list(k)for k in sorted(lost)],'old_strict_zero_reference_losses':bad,'reference_proof':proof,'actual_named_source_pad_count':len({r['uuid']for r in nr if r['kind']=='pad'and str(r['pin'])})});put(O/'checkpoint.json',rows);print('R429 bank',net,'contacts',len(contactbad),'source',len(lost),'refs',len(bad),flush=True)
 net='/motherboard_power_entry/FIELD_5V';_,n=K.physical(c,net,ctx);groups[net]=n;nr=K.root(n,'L11003','2');present={(r['ref'],str(r['pin']))for r in nr if r['kind']=='pad'};need=[('U11017','8'),('U11017','5'),('R11071','1'),('C11064','1'),('R9039','1'),('C11080','1'),('U11013','1'),('U11013','3'),('R11051','1')];missing=[p for p in need if p not in present]
 (O/'actual-checked-four-net-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));rec={'verdict':'LOCAL_ORIGINAL_RIM_GROUND_CONTACT_SOURCE_REFERENCE_PASS_FIELD5_NINE_TARGETS_PASS_IO3_STILL_SEPARATE'if not missing and not any(r['old_contact_losses']or r['prior_source_keys_lost']or r['old_strict_zero_reference_losses']for r in rows)else'LOCAL_ORIGINAL_RIM_GROUND_SOURCE_REFERENCE_REPAIR_REQUIRED','R423_model_sha256':sha(R/'model.pkl'),'immutable_DIC262_model_sha256':sha(B/'model.pkl'),'rows':rows,'FIELD5_nine_targets_missing':missing,'IO3_383_key_split':'NOT_FIXED_BY_THIS_SCOPE_SBC_OWNED_SUCCESSOR_PENDING','full_all_net_new_true_margin_current_native':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started};put(O/'receipt.json',rec);print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'verdict':rec['verdict'],'FIELD5_missing':missing}),flush=True)
if __name__=='__main__':main()
