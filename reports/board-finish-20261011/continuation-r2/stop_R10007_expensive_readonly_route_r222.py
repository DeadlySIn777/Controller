"""Stop only the verified owned read-only probe before a locally bounded successor."""
import datetime,hashlib,json,psutil
from pathlib import Path
H=Path(__file__).resolve().parent;script=H/'nominate_U10003_R10007_source_reference_B_reconnection_r221.py';out=H/'U10003-R10007-source-reference-B-reconnection-nomination-r221';receipt=out/'receipt.json'
if receipt.exists():
 print('R221_ALREADY_COMPLETED_NO_STOP',flush=True)
else:
 p=psutil.Process(59420);assert abs(p.create_time()-1791832159.4962468)<.0001;cmd=p.cmdline();assert len(cmd)==3 and Path(cmd[-1]).resolve()==script.resolve()and Path(cmd[1]).name=='launch_confined_host.py'and p.name().lower().startswith('python');assert p.cpu_affinity()==list(range(16,28));record={'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'pid':p.pid,'creation_time':p.create_time(),'verified_command':cmd,'script_sha256':hashlib.sha256(script.read_bytes()).hexdigest(),'CPU_seconds_before_stop':sum(p.cpu_times()[:2]),'reason':'Read-only route probe repeatedly offsets complete global source/reference geometry. Successor clips only search work to the local query and retains full unmodified source-body validation.','model_or_board_emitted':False,'native_jobs_stopped':0,'adopted':False};p.terminate();p.wait(timeout=10);target=out/'verified-readonly-stop-r222.json';assert not target.exists();target.write_text(json.dumps(record,indent=1)+'\n');print('R221_VERIFIED_READONLY_STOP',flush=True)
