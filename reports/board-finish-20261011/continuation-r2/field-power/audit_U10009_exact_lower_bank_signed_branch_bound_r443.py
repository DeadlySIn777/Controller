"""Exact planning current cut; no equal sharing or barrel capacity claim."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,time
from pathlib import Path
H=Path(__file__).resolve().parent
for d in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/d))
import audit_DIC_C1022_actual_R250_full77_and_signals_r258 as K
from inventory import sha
R=H/'U10009-R397-exact-R155-coupled-source-feed-construction-r411'
P=H/'U10009-retained-lower-VS-ordinary-barrel-coupled-nomination-r397'
LED=H.parent/'protected24-port-allocation-r1/receipt.json'
O=H/'U10009-exact-lower-VS-one-barrel-cut-signed-current-bound-r443'
def put(f,x):f.write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();start=time.monotonic();assert sha(R/'model.pkl')=='4bde59b8375ad9c512307f4894c1a5c2d6919f1cfb9f91c3669079e57a75e639';assert sha(LED)=='4d8415f8ed77987244dba1bad3acb2632913a0b96a9d8666902a17a4896002ea'
 g,h,b,q,c=pickle.loads((R/'model.pkl').read_bytes());d=pickle.loads((P/'only-coupled-ordinary-and-inner-plane-nominee.pkl').read_bytes());vid=d['vias'][0]['uuid'];net=K.L.norm(d['vias'][0]['net']);actual=pickle.loads((R/'actual-two-net-groups.pkl').read_bytes());prior=K.root(actual[net],'U11004','17');test={**c,'vias':[v for v in c['vias']if v['uuid']!=vid]};_,groups=K.physical(test,net,K.hole_context(test));cutroot=K.root(groups,'U11004','17');cut=K.root(groups,'U10009','34');assert not K.keys(cut)&K.keys(cutroot)
 endpoints={r['uuid']for r in cut if r['kind']=='pad'};lost=K.keys(prior)-K.keys(cutroot);pads=[{'UUID':r['uuid'],'ref':r['ref'],'pin':str(r['pin']),'layer':r['layer']}for r in cut if r['kind']=='pad'];impacts=[];lo=hi=0.
 for t in json.loads(LED.read_text())['terms']:
  if t['domain']!='FA':continue
  allpoints={e['physical_pad_uuid']for e in t['eligible_physical_endpoints']};hit=allpoints&endpoints
  if not hit:continue
  x=t['signed_supply_current_a'];minimum=x if allpoints<=endpoints else min(0.,x);maximum=x if allpoints<=endpoints else max(0.,x);lo+=minimum;hi+=maximum;impacts.append({'term':t['name'],'signed_term_A':x,'eligible_pad_count':len(allpoints),'actual_cut_eligible_pad_UUIDs':sorted(hit),'allocation':'CONSERVATIVE_UNKNOWN_SIMPLEX_NO_EQUAL_SPLIT','minimum_A':minimum,'maximum_A':maximum})
 put(O/'receipt.json',{'verdict':'EXACT_SIGNED_BRANCH_CUT_PLANNING_BOUND_CAPACITY_AND_MUTUAL_GATES_OPEN','rejected_R411_model_sha256':sha(R/'model.pkl'),'protected57term_ledger_sha256':sha(LED),'single_removed_only_NEW_barrel_UUID':vid,'no_geometry_emitted_or_adopted':True,'all_removed_barrel_retained_keys_cut_UUIDs':[list(k)for k in sorted(lost)],'cut_exact_pad_layer_records':pads,'signed_current_interval_A':[lo,hi],'term_impacts':impacts,'R419_real_LOGIC_split_and_old_reference_losses':'PRESERVED_FAIL_R411_NOT_ACCEPTED','full_four_outputs_.5A_and_all_eight_VS_retained':True,'separate_external_output_returns_and_device_GND_allocation':'PRESERVED','barrel_package_necks_unequal_sharing_sheet_drop_temp_transient_native':'OPEN','native_jobs':0,'elapsed_seconds':time.monotonic()-start});print('R443',sha(O/'receipt.json'),'bound',[lo,hi],flush=True)
if __name__=='__main__':main()
