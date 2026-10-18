"""Run only this isolated host audit with the user's total CPU cap."""
import datetime, hashlib, json, os, subprocess, sys, time
from pathlib import Path
import psutil
HERE=Path(__file__).resolve().parent
OUT=HERE/'resource-FA-full-window-ordinary-return-guard-r11'
SCRIPT=HERE/'screen_FA_full_window_ordinary_FG_returns_r11.py'
ALLOWED=list(range(16,28))

def put(name,obj):
    (OUT/name).write_text(json.dumps(obj,indent=1)+'\n',encoding='utf-8')

def family(proc):
    try:return [proc,*proc.children(recursive=True)]
    except psutil.NoSuchProcess:return []

def main():
    OUT.mkdir(exist_ok=False);me=psutil.Process();me.cpu_affinity(ALLOWED);me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
    env=os.environ.copy();env.update({n:'2' for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS')})
    put('plan.json',{'script':str(SCRIPT),'SHA256':hashlib.sha256(SCRIPT.read_bytes()).hexdigest(),'python':sys.executable,'affinity':ALLOWED,'numeric_threads':2,'total_CPU_limit_percent':80,'suspend_at_percent':70,'resume_below_percent':62,'native_jobs':0})
    paused=set();peak=0.;breaches=0;samples=0
    with (OUT/'host.log').open('w',encoding='utf-8') as log:
        run=subprocess.Popen([sys.executable,'-X','utf8',str(SCRIPT)],env=env,stdout=log,stderr=subprocess.STDOUT);proc=psutil.Process(run.pid)
        try:
            while run.poll() is None:
                cpu=psutil.cpu_percent(interval=1);peak=max(peak,cpu);breaches+=cpu>=80;samples+=1;action=None
                if cpu>=70 and not paused:
                    for child in reversed(family(proc)):
                        try:child.suspend();paused.add(child.pid)
                        except psutil.NoSuchProcess:pass
                    action='suspend_owned_job_tree'
                elif cpu<62 and paused:
                    for pid in list(paused):
                        try:psutil.Process(pid).resume()
                        except psutil.NoSuchProcess:pass
                    paused.clear();action='resume_owned_job_tree'
                row={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'CPU_percent':cpu,'action':action,'paused_pids':sorted(paused)}
                with (OUT/'samples.jsonl').open('a',encoding='utf-8') as stream:stream.write(json.dumps(row)+'\n')
                if samples%10==0 or action:put('status.json',{'phase':'RUNNING','pid':run.pid,'samples':samples,'peak_CPU_percent':peak,'samples_at_or_above_80_percent':breaches,'last_sample':row})
        finally:
            for pid in paused:
                try:psutil.Process(pid).resume()
                except psutil.NoSuchProcess:pass
        code=run.wait()
    put('status.json',{'phase':'COMPLETE' if code==0 else 'FAILED_RESULTS_PRESERVED','exit_code':code,'samples':samples,'peak_CPU_percent':peak,'samples_at_or_above_80_percent':breaches,'native_jobs':0})
    raise SystemExit(code)

if __name__=='__main__':main()
