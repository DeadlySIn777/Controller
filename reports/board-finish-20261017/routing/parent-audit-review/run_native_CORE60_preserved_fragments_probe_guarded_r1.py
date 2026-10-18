"""CPU-monitored owned read-only KiCad process, without native fill or save."""
import os,sys,json,time,hashlib,subprocess,datetime
from pathlib import Path
import psutil
H=Path(__file__).resolve().parent;SCRIPT=H/'probe_CORE60_preserved_native_outlines_r1.py'
OUT=H/'resource-CORE60-native-probe-guard-r1';PYTHON='C:/Program Files/KiCad/10.0/bin/python.exe';ALLOWED=list(range(16,28))
def write(n,v):(OUT/n).write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def family(p):
    try:return[p,*p.children(recursive=True)]
    except psutil.NoSuchProcess:return[]
def main():
    OUT.mkdir();me=psutil.Process();me.cpu_affinity(ALLOWED);me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    env=os.environ.copy();env.update({n:'2'for n in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')})
    write('plan.json',{'script':str(SCRIPT),'script_SHA256':hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),'python':PYTHON,'affinity':ALLOWED,'numeric_threads':2,'native_read_only_API_jobs':1,'native_fill_jobs':0,'suspend_at_total_CPU_percent':70,'resume_below_percent':62,'user_total_CPU_limit_percent':80})
    peak=0.;samples=0;breaches=0;paused=set()
    with(OUT/'native.log').open('w',encoding='utf-8')as log:
        run=subprocess.Popen([PYTHON,'-X','utf8',str(SCRIPT)],env=env,stdout=log,stderr=subprocess.STDOUT);proc=psutil.Process(run.pid)
        try:
            while run.poll()is None:
                cpu=psutil.cpu_percent(interval=1);peak=max(peak,cpu);samples+=1;breaches+=cpu>=80;action=None
                if cpu>=70 and not paused:
                    for child in reversed(family(proc)):
                        try:child.suspend();paused.add(child.pid)
                        except psutil.NoSuchProcess:pass
                    action='suspend_owned_tree'
                elif cpu<62 and paused:
                    for pid in list(paused):
                        try:psutil.Process(pid).resume()
                        except psutil.NoSuchProcess:pass
                    paused.clear();action='resume_owned_tree'
                row={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'CPU_percent':cpu,'action':action,'paused_PIDs':sorted(paused)}
                with(OUT/'samples.jsonl').open('a',encoding='utf-8')as f:f.write(json.dumps(row)+'\n')
        finally:
            for pid in paused:
                try:psutil.Process(pid).resume()
                except psutil.NoSuchProcess:pass
        code=run.wait()
    write('status.json',{'phase':'COMPLETE'if code==0 else'FAILED_OUTPUTS_PRESERVED','exit_code':code,'samples':samples,'peak_total_CPU_percent':peak,'samples_at_or_above_80_percent':breaches,'native_fill_jobs':0});raise SystemExit(code)
if __name__=='__main__':main()
