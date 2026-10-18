"""Test whether the exact logic wall is a necessary bridge, without routing."""
import hashlib,json,pickle,sys
from pathlib import Path
H=Path(__file__).resolve().parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
OUT=H/'U10003-exact-logic-wall-native-topology-r205'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
 assert not OUT.exists();OUT.mkdir()
 p=H/'U10003-preserved-branch-exact-two-port-compliant-clock-fault-ground-construction-r196/model.pkl'
 assert sha(p)=='dfb8050d5f45f5602692f2f4bb11c4706937a7821d57fac55a6733042314cae5'
 g,h,b,q,before=pickle.loads(p.read_bytes());uid='eeb33c09-9494-4734-b174-e3c3ceffd73b';net='/FPGA_OUTPUT_REQUEST'
 t=next(x for x in h['tracks']if x['uuid']==uid);assert any(x==t for x in g['tracks'])
 after={**before,'tracks':[x for x in before['tracks']if x['uuid']!=uid]}
 contexts=[K.hole_context(x)for x in(before,after)]
 _,old=K.physical(before,net,contexts[0]);_,new=K.physical(after,net,contexts[1])
 keys=K.F.discrete_keys;membership={k:i for i,xs in enumerate(new)for k in keys(xs)}
 rows=[];loss=[]
 for i,xs in enumerate(old):
  retained=keys(xs)-{('track',uid)};missing=sorted(retained-membership.keys());dest=sorted({membership[k]for k in retained if k in membership})
  row={'before_group':i,'retained_keys':len(retained),'after_groups':dest,'missing':missing,'pads':[{'ref':r['ref'],'num':r['num'],'UUID':r['uuid'],'layer':r['layer']}for r in xs if r['kind']=='pad']}
  rows.append(row)
  if missing or len(dest)>1:loss.append(row)
 (OUT/'before-after-exact-logic-wall-contacts.json').write_text(json.dumps(rows,indent=1)+'\n')
 (OUT/'after-actual-drilled-logic-groups.pkl').write_bytes(pickle.dumps(new,protocol=5))
 result={'verdict':'EXACT_LOGIC_WALL_REMOVE_ONLY_CONTACT_PASS_CURRENT_REFERENCE_NATIVE_OPEN'if not loss else'EXACT_LOGIC_WALL_IS_NECESSARY_BRIDGE','model_sha256':sha(p),'withdrawn_only_original_track':t,'retained_contact_loss_rows':loss,'native_jobs':0,'adopted':False,'manufacturing_ready':False}
 (OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R205_COMPLETE',len(loss),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
