"""Schedule the unchanged existing CPU/GPU alarms before r9 expires."""
import datetime,hashlib,json,runpy,shutil
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def main():
    prior=H/'resource-monitor-r16';status=json.loads((prior/'resource-status.json').read_bytes())
    if status['phase']!='RUNNING':raise ValueError('Current watch no longer running; inspect before arming')
    out=H/'resource-monitor-r17'
    if out.exists():raise ValueError('Preserve existing alarm evidence')
    out.mkdir();shutil.copy2(prior/'watch.py',out/'watch.py')
    start=datetime.datetime.fromisoformat(status['until_utc'])-datetime.timedelta(seconds=10)
    if start<=datetime.datetime.now(datetime.timezone.utc):raise ValueError('Scheduled watch time already passed')
    (out/'prior-watch-receipt.json').write_text(json.dumps({'prior_watch':'resource-monitor-r16','prior_running_pid':status['pid'],'prior_until_utc':status['until_utc'],'scheduled_start_utc':start.isoformat(),'next_watch_sha256':sha(out/'watch.py'),'CPU_limit_percent':70,'GPU_limit_C':80,'GPU_limit_W':350,'new_heavy_slots':0,'new_watch_duration_hours':1,'overlap_seconds':10},indent=1)+'\n',encoding='utf-8')
    source=H/'schedule_resource_watch_r16.py';target=H/'schedule_resource_watch_r17.py';code=source.read_text(encoding='utf-8')
    if target.exists() or code.count("out=HERE/'resource-monitor-r16'")!=1:raise ValueError('Fresh schedule derivation required')
    target.write_text(code.replace("out=HERE/'resource-monitor-r16'","out=HERE/'resource-monitor-r17'"),encoding='utf-8')
    (out/'derivation.json').write_text(json.dumps({'prior_scheduler_sha256':sha(source),'new_scheduler_sha256':sha(target),'watch_bytes_unchanged':sha(prior/'watch.py')==sha(out/'watch.py'),'only_schedule_folder_changed':True,'no_process_control_or_heavy_slots':True},indent=1)+'\n',encoding='utf-8')
    print(json.dumps({'phase':'SCHEDULED_ALARM_REARM','scheduled_utc':start.isoformat()}),flush=True)
    runpy.run_path(str(target),run_name='__main__')
if __name__=='__main__':main()
