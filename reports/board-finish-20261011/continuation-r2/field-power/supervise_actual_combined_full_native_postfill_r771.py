"""Wait for the existing R299 native result, then run one serial host audit.

This supervisor launches no KiCad job and never edits native inputs/cache.
"""
import os, psutil
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import datetime, hashlib, json, subprocess, sys, time
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parent
OUT=H/'combined-full-native-postfill-serial-host-supervisor-r771'
assert not OUT.exists();OUT.mkdir()
NF=ROOT/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full'
PR=H/'R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763/prepare-receipt.json'
assert PR.is_file()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(PR)=='23c1b5669b0453132fe6b88ec41dc00cfe6c9ac48613386cbeb29ad149355019'
first=H/'audit_combined_R753_actual_full_state_conn_scope_r763.generated.py'
second=H/'audit_combined_actual_full_source_gains_and_CPP_partitions_r767.py'
assert sha(first)=='1b7fabb30f39a5cb6329dd26a7bff3aa6f1a9c778b0a9d28efa19490a655cd8b'
pins={str(p):sha(p)for p in(Path(__file__),PR,first,second)}
def put(name,obj):(OUT/name).write_text(json.dumps(obj,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def state(phase,**kw):put('status.json',{'phase':phase,'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'native_jobs':0,'adopted':False,**kw});print('R771',phase,flush=True)
put('input-and-sequential-job-pins.json',{'input_SHA256':pins,'native_output_dir':str(NF),'host_runs':[[str(first),'--after'],[str(second)]],'native_jobs':0,'CPU_affinity':list(range(16,28)),'priority':'BELOW_NORMAL','numeric_threads':2,'no_new_heavy_or_native_slot':True})
state('WAITING_EXISTING_FULL_R299_NATIVE_RECEIPT')
started=time.monotonic()
while not (NF/'receipt.json').is_file():
 completion=NF.parent/'native-process-completion.json'
 if completion.is_file():
  data=json.loads(completion.read_bytes())
  if data['exit_code']:
   state('EXISTING_NATIVE_FAILED_NO_HOST_SUBSTITUTE',native_exit_code=data['exit_code']);raise SystemExit(1)
 if time.monotonic()-started>43200:
  state('WAIT_BOUND_EXCEEDED_NATIVE_NO_RESULT_NO_SUBSTITUTE');raise SystemExit(1)
 time.sleep(10)
for required in ('actual-full-refill-geometry.json','actual-full-refill-via-flashes.json','partitions.json','before-native-all-FP-pad-pose.json'):assert(NF/required).is_file(),required
assert all(sha(f)==h for f,h in pins.items())
native=json.loads((NF/'receipt.json').read_bytes());assert native['candidate_SHA256']=='7bddce003de3ac2324be5a6ac442e6b662b92915908d4b79e6209d40a098b8a2'
put('actual-native-receipt-binding.json',{'file':str(NF/'receipt.json'),'SHA256':sha(NF/'receipt.json'),'candidate_SHA256':native['candidate_SHA256']})
for i,args in enumerate(([str(first),'--after'],[str(second)])):
 assert all(sha(f)==h for f,h in pins.items())
 state('SERIAL_CONFINED_ACTUAL_HOST_AUDIT_RUNNING',step=i+1,script=args[0])
 with (OUT/('host-step-'+str(i+1)+'.log')).open('w',encoding='utf-8')as log:
  result=subprocess.run([sys.executable,'-X','utf8',*args],stdout=log,stderr=subprocess.STDOUT)
 put('host-step-'+str(i+1)+'-completion.json',{'exit_code':result.returncode,'log_SHA256':sha(OUT/('host-step-'+str(i+1)+'.log'))})
 if result.returncode:
  state('HOST_AUDIT_FAILED_RAW_EVIDENCE_PRESERVED',step=i+1,exit_code=result.returncode);raise SystemExit(result.returncode)
r1=H/'R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763/receipt.json'
r2=H/'R753-actual-FULL-source-gain-native-planner-guards-and-CPP-pad-partitions-r767/receipt.json'
assert all(sha(f)==h for f,h in pins.items())
put('receipt.json',{'status':'BOTH_ACTUAL_FULL_STATE_HOST_AUDITS_COMPLETED_COUNTS_AND_FAILURES_RETAINED',
 'actual_native_receipt_SHA256':sha(NF/'receipt.json'),'first_actual_host_receipt':{'file':str(r1),'SHA256':sha(r1)},
 'second_actual_host_receipt':{'file':str(r2),'SHA256':sha(r2)},'input_SHA256':pins,
 'native_DRC_source_current_and_manufacturing':'OPEN_OR_FAIL_SEPARATE; no audit status override',
 'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started})
state('COMPLETE_RAW_COUNTS_AND_NATIVE_CURRENT_GATES_HELD')
