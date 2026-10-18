"""Re-arm existing alarms ten seconds before the current watch expires."""
import datetime,hashlib,json,runpy,time
from pathlib import Path
HERE=Path(__file__).resolve().parent
out=HERE/'resource-monitor-r10'
receipt=json.loads((out/'prior-watch-receipt.json').read_bytes())
start=datetime.datetime.fromisoformat(receipt['scheduled_start_utc'])
(out/'schedule-status.json').write_text(json.dumps({'phase':'ARMED_FOR_AUTOMATIC_START','scheduled_utc':start.isoformat(),'new_heavy_slots':0},indent=1)+'\n',encoding='utf-8')
while datetime.datetime.now(datetime.timezone.utc)<start:
    time.sleep(min(10,max(.1,(start-datetime.datetime.now(datetime.timezone.utc)).total_seconds())))
if hashlib.sha256((out/'watch.py').read_bytes()).hexdigest()!=receipt['next_watch_sha256']:raise ValueError('Frozen watch script changed')
runpy.run_path(str(out/'watch.py'),run_name='__main__')
