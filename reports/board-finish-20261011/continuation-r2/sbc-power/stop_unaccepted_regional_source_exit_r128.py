"""Preserve diagnostic R125 candidates before exact confined replay."""
from pathlib import Path
import hashlib,json,time,psutil
H=Path(__file__).resolve().parent;out=H/'major-rail-regional-logged-source-exit-r125'
p=psutil.Process(68396);cmd=p.cmdline()
assert any('construct_major_rail_regional_logged_source_exit_r125.py' in x for x in cmd)
assert not list(out.glob('accepted*')) and not (out/'model.pkl').exists()
files={str(f.relative_to(out)):hashlib.sha256(f.read_bytes()).hexdigest() for f in out.rglob('*') if f.is_file()}
r={'verdict':'UNACCEPTED_DIAGNOSTIC_ROUTER_STOPPED_TO_REPLAY_FROZEN_PHYSICAL_CANDIDATE_WITH_STRICT_EXTRA_CLEARANCE','PID':p.pid,'command_line':cmd,'creation_unix':p.create_time(),'CPU_user_seconds':p.cpu_times().user,'CPU_system_seconds':p.cpu_times().system,'frozen_failed_files':files,'accepted_source_geometry':0,'no_area_or_clearance_waiver':True,'native_jobs':0,'board_written':False,'stopped_unix':time.time()}
p.terminate();p.wait(timeout=15)
(out/'deliberate-stop-receipt-r128.json').write_text(json.dumps(r,indent=1)+'\n')
print('EXACT_R125_DIAGNOSTIC_STOPPED',p.pid)
