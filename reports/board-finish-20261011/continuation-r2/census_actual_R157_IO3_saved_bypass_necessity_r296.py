"""Read cached full native groups before replaying a historical bypass."""
import os,psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
K=N.K;sha=N.sha
OUT=H/'actual-full-R157-IO3-source-saved-bypass-necessity-r296';assert not OUT.exists();OUT.mkdir()
folder=H/'R275-actual-R157-fresh-five-net-BEFORE-cache-r277';fp=folder/'actual-R157-five-affected-net-groups.pkl';assert sha(fp)=='9a35f032891022b3c6cc0dfee0018cf6aa394b923c8589d8be18a06a04f49a91'
groups=pickle.loads(fp.read_bytes())['/IO_3V3'];source=K.root(groups,'R18001','2');keys=K.keys(source)
targets=['a20caeb5','3945a1ae','6007d13f'];rows=[]
for prefix in targets:
 found=[(i,r)for i,gs in enumerate(groups)for r in gs if r['uuid'].startswith(prefix)and r['kind']=='via']
 assert found,prefix
 rows.append({'UUID_prefix':prefix,'actual_members':sorted({(i,r['uuid'],r['layer'])for i,r in found}),'all_actual_barrel_rows_on_R18001_SOURCE':all(r in source for _,r in found)})
# Identity membership only; no costly/global or tolerant Cu Boolean shortcut.
put=lambda n,x:(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
put('receipt.json',{'status':'ACTUAL_FULL_NATIVE_R157_IO3_SOURCE_AND_SAVED_BYPASS_NEED_CENSUS','full_native_geometry_SHA256':'421ce21eac9964fc53834514a560274e9527f9284c29da02fe94d37b950f1c6b','actual_groups_SHA256':sha(fp),'IO3_group_count':len(groups),'actual_SOURCE_R18001_layer_key_count':len(keys),'actual_SOURCE_pad_count':len({r['uuid']for r in source if r['kind']=='pad'}),'saved_R379_endpoint_memberships':rows,'both_old_bypass_endpoints_already_on_SOURCE':all(r['all_actual_barrel_rows_on_R18001_SOURCE']for r in rows[:2]),'historical_R353_3689_keys_NOT_current_head_waiver':True,'native_jobs':0,'adopted':False})
print(json.dumps({'source_keys':len(keys),'groups':len(groups),'endpoint_memberships':rows}),flush=True)
