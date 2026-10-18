"""Rank original unrecovered joins with the actual combined native pad poses."""
import os,psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,math,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;sha=N.sha
OUT=H/'original-r07-residual-joins-current-R753-native-pad-ranking-r301';assert not OUT.exists();OUT.mkdir()
fp=H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(fp)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';_,h,_,_,_=pickle.loads(fp.read_bytes())
poses=H/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/before-native-all-FP-pad-pose.json';native=json.loads(poses.read_bytes())['pads'];pm={};counts={}
for pad in h['pads']:
 key=(pad['ref'],str(pad['num']));n=counts.get(key,0);counts[key]=n+1;name=pad['ref']+'.'+str(pad['num'])+'#'+str(n);row=native[pad['uuid']];assert row[0]==str(pad['num'])and row[1]==pad['net'];pm[name]={'UUID':pad['uuid'],'ref':pad['ref'],'pin':str(pad['num']),'raw_net':row[1],'at':[row[2]/1e6,row[3]/1e6],'native_layers':row[4],'name':name}
residual=H/'original-r07-seventeen-lost-joins-actual-native-R157-residual-r287/actual-full-native-R157-unrestored-original-lost-relationships.json';rows=json.loads(residual.read_bytes());results=[]
for row in rows:
 groups=row['actual_R157_current_groups'];pairs=[]
 for i,g1 in enumerate(groups):
  for j,g2 in enumerate(groups):
   if j<=i:continue
   for a in g1:
    for b in g2:
     pa,pb=pm[a],pm[b];layers=sorted(set(pa['native_layers'])&set(pb['native_layers'])&{'F.Cu','B.Cu'});pairs.append({'a':pa,'b':pb,'common_surface_layers':layers,'distance_mm':math.dist(pa['at'],pb['at'])})
 pairs.sort(key=lambda x:(not bool(x['common_surface_layers']),x['distance_mm']));net=row['normalized_original_net'];results.append({'normalized_net':net,'original_full_native_R157_remaining_joins':row['actual_R157_remaining_required_joins'],'current_R753_native_pad_nearest_pairs':pairs[:8],'already_in_combined_candidate_or_active':net in('/motherboard_di/DI6_LOGIC','/motherboard_do/DOA_Q0_READY_N','/motherboard_di/DI15_LOGIC')})
results.sort(key=lambda r:(r['already_in_combined_candidate_or_active'],r['current_R753_native_pad_nearest_pairs'][0]['distance_mm']))
(OUT/'ranked-current-native-pad-pairs.json').write_text(json.dumps(results,indent=1,allow_nan=False)+'\n',encoding='utf-8')
(OUT/'receipt.json').write_text(json.dumps({'status':'ACTUAL_R753_NATIVE_PAD_POSE_REMAINING_R07_LOSS_RANKING_NO_NEW_ROUTE','original_residual_file_SHA256':sha(residual),'current_native_pad_pose_SHA256':sha(poses),'record_count':len(results),'all_original_pad_UUID_raw_nets_retained':True,'pending_native_full_R753_partition_changes_not_credited':True,'native_jobs':0,'adopted':False},indent=1)+'\n',encoding='utf-8')
for r in results:
 pair=r['current_R753_native_pad_nearest_pairs'][0];print(r['normalized_net'],pair['a']['name'],pair['a']['at'],pair['b']['name'],pair['b']['at'],round(pair['distance_mm'],6),pair['common_surface_layers'],'active',r['already_in_combined_candidate_or_active'],flush=True)
