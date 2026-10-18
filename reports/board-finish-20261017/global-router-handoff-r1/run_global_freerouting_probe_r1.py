"""Isolated global Freerouting bulk experiment, total CPU guard and exact command."""
import os,sys,json,hashlib,time,subprocess,datetime
from pathlib import Path
import psutil
HERE=Path(__file__).resolve().parent;OUT=HERE/'global-probe-r1';DSN=HERE/'stage4-actual-R299-fills-domain600-global-reroutable.dsn';JAVA=Path('C:/Users/Gluis/.codex/toolchains/air-board-router/jre25/jdk-25.0.4.1+1-jre/bin/java.exe');JAR=Path('C:/Users/Gluis/.codex/toolchains/air-board-router/freerouting-2.4.1.jar');ALLOWED=list(range(16,28))
sha=lambda f:hashlib.sha256(Path(f).read_bytes()).hexdigest()
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1)+'\n',encoding='utf-8')
def main():
 OUT.mkdir(exist_ok=False);me=psutil.Process();me.cpu_affinity(ALLOWED);me.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS);home=OUT/'isolated-user-home';home.mkdir();env=os.environ.copy();env.update({'APPDATA':str(OUT/'appdata'),'LOCALAPPDATA':str(OUT/'localappdata')})
 for key in('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):env[key]='2'
 command=[str(JAVA),'-Xmx16g','-XX:ActiveProcessorCount=4','-Djava.awt.headless=true','-Duser.home='+str(home),'-jar',str(JAR),'-de',str(DSN),'-do',str(OUT/'global-route.ses'),'-mp','32','-mt','4','--gui.enabled=false','--api_server.enabled=false','--mcp_server.enabled=false','--usage_and_diagnostic_data.disable_analytics=true','--feature_flags.multi_threading=true']
 pins={str(p):sha(p)for p in(DSN,JAVA,JAR,Path(__file__))};put('command.json',{'argv':command,'input_SHA256':pins,'isolated_user_state':str(home),'numeric_threads':2,'Java_active_processors':4,'router_optimizer_threads':4,'CPU_affinity':ALLOWED,'total_CPU_limit_percent':80,'suspend_at_percent':70,'resume_below_percent':62,'existing_92778_route_objects_unlocked_only_in_donor':True,'native_actual_plane_fill_and_SI_current_acceptance':'REQUIRED_BEFORE_ADOPTION','native_fill_calls':0})
 paused=False;peak=0.;breaches=0;samples=0;t=time.monotonic()
 with (OUT/'freerouting.log').open('w',encoding='utf-8')as log:
  run=subprocess.Popen(command,cwd=OUT,env=env,stdout=log,stderr=subprocess.STDOUT);proc=psutil.Process(run.pid);put('status.json',{'phase':'RUNNING','pid':run.pid,'command_file':str(OUT/'command.json')})
  try:
   while run.poll()is None:
    cpu=psutil.cpu_percent(interval=1);peak=max(peak,cpu);breaches+=cpu>=80;samples+=1;action=None
    if cpu>=70 and not paused:proc.suspend();paused=True;action='suspend_owned_java'
    elif cpu<62 and paused:proc.resume();paused=False;action='resume_owned_java'
    row={'UTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'total_CPU_percent':cpu,'action':action}
    with (OUT/'CPU-samples.jsonl').open('a',encoding='utf-8')as f:f.write(json.dumps(row)+'\n')
    if samples%10==0 or action:put('status.json',{'phase':'RUNNING','pid':run.pid,'samples':samples,'peak_total_CPU_percent':peak,'samples_at_or_above_80_percent':breaches,'elapsed_seconds':time.monotonic()-t,'last_sample':row})
  finally:
   if paused:
    try:proc.resume()
    except psutil.NoSuchProcess:pass
  code=run.wait()
 put('status.json',{'phase':'COMPLETE'if code==0 else'FAILED_OUTPUTS_PRESERVED','exit_code':code,'samples':samples,'peak_total_CPU_percent':peak,'samples_at_or_above_80_percent':breaches,'elapsed_seconds':time.monotonic()-t,'session_exists':(OUT/'global-route.ses').exists(),'inputs_unchanged':all(sha(p)==v for p,v in pins.items()),'adopted':False,'native_fill_calls':0});raise SystemExit(code)
if __name__=='__main__':main()
