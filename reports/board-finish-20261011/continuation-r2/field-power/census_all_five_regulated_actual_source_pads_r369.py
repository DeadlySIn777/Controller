"""Complete named-pad and actual physical-piece source census, no derating."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent
for x in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/x))
import contact_layout as L
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
import restore_field_current_mixed_precision_states_r366 as MP
from inventory import sha
O=H/'all-five-regulated-actual-drilled-source-census-r369'
B=H/'REG-U25-DIC-SBC273-two-new-REG-actual-fill-margin-repair-r364'
RAILS=[('FIELD5','/motherboard_power_entry/FIELD_5V','L11003','2',.34113098119891167,.36),('A3','/motherboard_do/DOA_FIELD_3V3','U11017','1',.042766088,.05),('B3','/motherboard_do/DOB_FIELD_3V3','U11018','1',.0731810363,.09),('BDO3','DOB_DO_FIELD_3V3','U11038','1',.0312356923,.04),('B5PRE','/motherboard_do/DOB_FIELD_5V_PRE','L19001','2',.13258538461538463,.14)]
def write(f,v):f.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();started=time.monotonic();assert sha(B/'model.pkl')=='a39e7784abf8969b7f68176555b2c37b5227981cbc615c4bd542205e410373ad';g,h,b,z,c=pickle.loads((B/'model.pkl').read_bytes());states=MP.restore_bound_field_current_precision_states(b,z);ctx=K.hole_context(c);rows=[];allgroups={}
 for label,net,ref,pin,current,policy in RAILS:
  _,groups=K.physical(c,net,ctx);allgroups[net]=groups;root=K.root(groups,ref,pin);keys=K.keys(root);allpads={p['uuid']:p for p in h['pads']if L.norm(p['net'])==net and str(p.get('num','')) not in('','0')};rootpads={r['uuid']for r in root if r['kind']=='pad'};missing=[]
  for uid,p in allpads.items():
   if uid not in rootpads:missing.append({'UUID':uid,'ref':p['ref'],'pin':str(p['num']),'raw_net':p['net'],'native_pose':p.get('xy'),'actual_layer_keys':list(p['layers'])})
  detached=[]
  for i,xs in enumerate(groups):
   if xs is root:continue
   detached.append({'physical_group':i,'named_native_pad_UUIDs':sorted({r['uuid']for r in xs if r['kind']=='pad'}),'retained_track_via_layer_keys':[list(k)for k in sorted(K.keys(xs))],'fill_roles':sorted({(r['uuid'],r['layer'])for r in xs if r['kind']=='fill'})})
  row={'rail':label,'normalized_lookup_net':net,'source_selector':ref+'.'+pin,'source_actual_named_pad_UUIDs':sorted(r['uuid']for r in root if r['kind']=='pad'and r['ref']==ref and str(r['pin'])==pin),'all_named_physical_pad_count':len(allpads),'source_rooted_named_physical_pad_count':len(set(allpads)&rootpads),'unrooted_named_native_pads':missing,'actual_source_nonfill_layer_key_count':len(keys),'detached_actual_drilled_groups':detached,'complete_normal_planning_A':current,'separate_copper_policy_A':policy,'capacity_corner_current_barrel_ground_mesh_thermal_native':'OPEN'};rows.append(row);write(O/'checkpoint.json',rows);print('R369',label,'named',len(allpads),'rooted',len(set(allpads)&rootpads),'missing',len(missing),'detached',len(detached),flush=True)
 (O/'all-five-actual-drilled-regulated-groups.pkl').write_bytes(pickle.dumps(allgroups,protocol=5));write(O/'all-five-actual-native-pad-and-piece-source-ledger.json',rows)
 rec={'verdict':'ALL_FIVE_REGULATED_NAMED_PADS_ACTUAL_SOURCE_ROOTED'if not any(r['unrooted_named_native_pads']for r in rows)else'REGULATED_NAMED_SOURCE_CLOSURE_OPEN_EXACT_TARGETS_LISTED','model_sha256':sha(B/'model.pkl'),'normal_model_sha256':sha(H/'normal-model-r3.json'),'rows':rows,'source_bound_all_simultaneous_outputs_limits_unchanged':True,'physical_contact_oldreference_trueCu_mesh_current_and_native':'OPEN_SEPARATE','native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-started};write(O/'receipt.json',rec);print('R369_COMPLETE',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
