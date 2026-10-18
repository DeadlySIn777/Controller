"""Wait for the existing owned fill, then run only reviewed host audits."""
import os,psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
process=psutil.Process();process.cpu_affinity(list(range(16,28)));process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import datetime,hashlib,json,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
OUT=H/'R275-pinned-actual-native-postfill-audit-continuation-r281'
NF=H/'U10003-HOST-R271-selected-actual-native-LG-FG-IO3-r275/selected-fill'
def put(name,x):(OUT/name).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 assert not OUT.exists();OUT.mkdir();review=H/'field-power/ROOT-R278-R279-R280-corrected-independent-static-review-r691/receipt.json';assert sha(review)=='68a8557778e2b1480740612f7ac138f6a323d328290e60ea04c768839a50040b';rr=json.loads(review.read_bytes());scripts=[]
 for row in rr['reviewed_helpers']:
  p=Path(row['file']);assert sha(p)==row['SHA256']==row['snapshot_SHA256'];scripts.append(p)
 producer=psutil.Process(79128);cmd=producer.cmdline();assert 'native_joint_selected_LG_FG_IO3_fill_r275.py'in' '.join(cmd);assert producer.cpu_affinity()==list(range(16,28));created=producer.create_time()
 frozen=[review,*scripts,H/'field-power/R157_native_selected_actual_conversion_r673.py',H/'field-power/audit_R667_actual_three_ground_landing_native_source_contacts_r669.py',H/'R275-exact-R155-parent-plus-only-ROOT-native-header-context-r276/context.pkl',H/'R275-actual-R157-fresh-five-net-BEFORE-cache-r277/receipt.json',H/'R275-actual-R157-fresh-five-net-BEFORE-cache-r277/actual-R157-five-net-model.pkl',H/'R275-actual-R157-fresh-five-net-BEFORE-cache-r277/actual-R157-five-affected-net-groups.pkl',H/'U10003-HOST-R157-exact-sparse-native-API-clone-r271/copy/board.kicad_pcb',H/'U10003-HOST-layer-aware-native-API-r274/native-joint-API.json',H/'launch_confined_host.py',Path(__file__)];pins={str(p.resolve()):sha(p)for p in frozen};live=Path('Z:/pcb-runs/claude-finish/integrate/revs/r07-ripup-signals-1.kicad_pcb');livehash=sha(live);assert livehash=='0c807b78247740a08c7b5a4a4380f0d8975d10045c9ba505e1e5d353d4cbb8fc'
 put('launch-and-inputs.json',{'producer_PID':79128,'producer_create_time':created,'producer_cmdline':cmd,'pins':pins,'review_sha256':sha(review),'native_jobs_added':0,'numerical_threads':2,'affinity':process.cpu_affinity(),'priority':'BelowNormal','steps':[str(p.resolve())for p in scripts],'only_observed_complete_native_R275_accepted':True,'no_board_write_or_adoption':True})
 put('status.json',{'phase':'WAITING_EXISTING_PINNED_R275_NATIVE_FILL','UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'producer_PID':79128});print('R281_WAITING_EXISTING_NATIVE_79128_REVIEWED_HOST_ONLY',flush=True)
 while True:
  try:
   p=psutil.Process(79128);assert p.create_time()==created,'PID reused; preserve failure and inspect';assert p.cmdline()==cmd
  except psutil.NoSuchProcess:break
  time.sleep(15)
 assert (NF/'receipt.json').is_file(),'Existing native process exited without final receipt'
 for name in ('geometry.json','actual-via-flashes.json'):assert (NF/name).is_file()
 native=json.loads((NF/'receipt.json').read_bytes());assert not native['all_discrete_post_fill_errors'];assert sha(NF/'geometry.json')==native['actual_geometry_SHA256'];assert sha(NF/'actual-via-flashes.json')==native['actual_via_flashes_SHA256']
 for p in frozen:assert sha(p)==pins[str(p.resolve())]
 jobs=[]
 for script in scripts:
  assert sha(live)==livehash;put('status.json',{'phase':'RUNNING_REVIEWED_ACTUAL_POSTFILL_HOST_AUDIT','script':str(script.resolve()),'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()});log=OUT/(script.stem+'.log')
  with log.open('xb')as stream:
   result=subprocess.run([sys.executable,str(H/'launch_confined_host.py'),str(script)],stdout=stream,stderr=subprocess.STDOUT,check=False)
  jobs.append({'script':str(script.resolve()),'script_sha256':sha(script),'exit_code':result.returncode,'log':str(log.resolve()),'log_sha256':sha(log)});put('completed-host-jobs.json',jobs);print('R281_STEP',script.name,result.returncode,flush=True)
  assert result.returncode==0,'Owned postfill audit failed; log preserved, no dependent promotion'
 assert sha(live)==livehash;put('receipt.json',{'status':'REVIEWED_R275_ACTUAL_POSTFILL_HOST_AUDITS_COMPLETED_RESULTS_NEED_ADOPTION_GATE','native_actual_receipt_SHA256':sha(NF/'receipt.json'),'host_jobs':jobs,'all_SOURCE_reference_current_DRC_failures':'Each audit receipt retained; no aggregate promotion','native_jobs_added':0,'live_r07_sha256':livehash,'live_unchanged':True,'adopted':False,'manufacturing_ready':False});put('status.json',{'phase':'COMPLETE','UTC':datetime.datetime.now(datetime.timezone.utc).isoformat()});print('R281_COMPLETE_NO_ADOPTION',flush=True)
if __name__=='__main__':
 try:main()
 except BaseException as exc:
  if OUT.exists()and not(OUT/'receipt.json').exists():put('failure.json',{'type':type(exc).__name__,'message':str(exc),'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'adopted':False})
  raise
