"""Preserve the empty hard-wall search before its one-owned-plane successor."""
from pathlib import Path
import json,hashlib,time
import psutil
H=Path(__file__).resolve().parent.parent
def sha(f):return hashlib.sha256(Path(f).read_bytes()).hexdigest()
sp=H/'sbc-power/major-rail-prioritized-extra-source-input-r118.json';assert sha(sp)=='39d079e16d104ee544797a78735ae4a5dae35d480db455692dd72faf97b2b181'
old=H/'sbc-power/major-rail-prioritized-extra-source-feeds-r117';assert old.exists() and not list(old.iterdir())
matches=[]
for q in psutil.process_iter(['pid','cmdline']):
    try:
        cmd=q.info['cmdline'] or []
        if any(a.replace('\\','/').endswith('/construct_major_rail_prioritized_extra_source_r117.py') for a in cmd) and any(a.replace('\\','/').endswith('/major-rail-prioritized-extra-source-input-r118.json') for a in cmd):matches.append(q)
    except (psutil.NoSuchProcess,psutil.AccessDenied):pass
assert len(matches)==1;pr=matches[0];cmd=pr.cmdline();assert any(a.replace('\\','/').endswith('/launch_confined_host.py') for a in cmd)
r={'verdict':'EMPTY_HARD_OWNED_WALL_RUN_STOPPED_FOR_EXPLICIT_LOCAL_OWNED_CORE_EXIT_CARVE','PID':pr.pid,'command_line':cmd,'creation_unix':pr.create_time(),'cpu_user_seconds':pr.cpu_times().user,'cpu_system_seconds':pr.cpu_times().system,'accepted_geometry':0,'blocking_owned_new_CORE_UUID':'c7e36847-4380-503d-80f2-836420105d9e','successor_allowed_bounded_exit_box_mm':[233.212,91.61,239.212,97.61],'successor_requires_exact_CORE_pad_track_via_and_all_proposed_CORE_component_source_retention':True,'successor_script_sha256':sha(H/'sbc-power/construct_major_rail_coupled_source_exit_r121.py'),'finite_failed_search_not_no_path_proof':True,'native_jobs':0,'board_written':False,'stopped_unix':time.time()}
pr.terminate();pr.wait(timeout=10);(old/'deliberate-stop-receipt-r122.json').write_text(json.dumps(r,indent=1)+'\n')
print('STOPPED_ONLY_EMPTY_HARD_WALL_R117',pr.pid,'COUPLED_SOURCE_SUCCESSOR',r['successor_script_sha256'],flush=True)
