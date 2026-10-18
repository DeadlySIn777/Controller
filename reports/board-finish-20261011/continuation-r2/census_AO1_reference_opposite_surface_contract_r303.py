"""Inspect exact analog source/return identities before proposing a bridge."""
import os,psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
OUT=H/'AO1-opposite-surface-reference-source-contract-census-r303';assert not OUT.exists();OUT.mkdir()
fp=H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert N.sha(fp)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';_,h,_,_,_=pickle.loads(fp.read_bytes())
posefile=H/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/before-native-all-FP-pad-pose.json';poses=json.loads(posefile.read_bytes())['pads'];refs={'C14643','U14626','U14621','U14622','U14623','U14624','J14621','J14622'}
rows=[]
for p in h['pads']:
 if p['ref']not in refs:continue
 obs=poses[p['uuid']];assert obs[1]==p['net'];rows.append({'UUID':p['uuid'],'ref':p['ref'],'pin':str(p['num']),'raw_net':p['net'],'domain':h['domains_normalized'].get(N.L.norm(p['net'])),'native_at':[obs[2]/1e6,obs[3]/1e6],'native_layers':obs[4],'hole':bool(p.get('hole'))})
(OUT/'exact-native-analog-source-return-pins.json').write_text(json.dumps(rows,indent=1)+'\n',encoding='utf-8')
put=lambda n,x:(OUT/n).write_text(json.dumps(x,indent=1)+'\n',encoding='utf-8')
put('receipt.json',{'status':'AO1_NATIVE_OPPOSITE_SURFACE_AND_ELECTRICAL_PIN_IDENTITIES_ONLY','native_R753_pose_SHA256':N.sha(posefile),'source_host_SHA256':N.sha(fp),'pin_count':len(rows),'SOURCE_return_root_not_inferred_from_nominal_ground_name':True,'native_jobs':0,'adopted':False})
for r in rows:
 if r['ref']in('C14643','U14626'):print(json.dumps(r),flush=True)
