"""Confine this agent's host-only constructors before numerical imports."""
import datetime,hashlib,json,os,runpy,sys,time
from pathlib import Path
import psutil
HERE=Path(__file__).resolve().parent
if len(sys.argv)<2:raise ValueError('Own exact host script filename required')
target=(HERE/sys.argv[1]).resolve()
if target.parent!=HERE or target==Path(__file__).resolve() or not target.is_file():raise ValueError('Only this isolated workspace host script is allowed')
for key in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[key]='2'
process=psutil.Process();process.cpu_affinity(list(range(16,28)));process.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
pin=hashlib.sha256(target.read_bytes()).hexdigest();stamp=time.time_ns();out=HERE/f'host-launch-{target.stem}-{stamp}.json'
receipt={'schema':'confined-host-launch-r1','target':str(target),'target_sha256':pin,'pid':process.pid,'affinity_before_numerical_imports':process.cpu_affinity(),'priority_before_numerical_imports':int(process.nice()),'numeric_environment':{k:os.environ[k] for k in ('OMP_NUM_THREADS','MKL_NUM_THREADS','OPENBLAS_NUM_THREADS','NUMEXPR_NUM_THREADS')},'native_slots_added':0,'gpu_jobs':0,'start_UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'completed':False}
out.write_text(json.dumps(receipt,indent=1)+'\n');print(json.dumps({'launch_receipt':str(out),'pid':process.pid,'affinity':process.cpu_affinity(),'numeric_threads':2}),flush=True)
sys.argv=[str(target)]+sys.argv[2:]
try:
    runpy.run_path(str(target),run_name='__main__')
    receipt['completed']=True
finally:
    receipt['target_unchanged']=hashlib.sha256(target.read_bytes()).hexdigest()==pin
    receipt['finish_UTC']=datetime.datetime.now(datetime.timezone.utc).isoformat();out.write_text(json.dumps(receipt,indent=1)+'\n')
if not receipt['target_unchanged']:raise ValueError('Frozen host target changed during run')
