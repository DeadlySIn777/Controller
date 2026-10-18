"""Preserve and stop only the exact empty owned R121 search."""
from pathlib import Path
import hashlib,json,time,psutil
H=Path(__file__).resolve().parent
out=H/'major-rail-coupled-source-exit-feeds-r121'
p=psutil.Process(51060)
cmd=p.cmdline()
assert any('construct_major_rail_coupled_source_exit_r121.py' in x for x in cmd),cmd
assert not list(out.iterdir()),'Preserve accepted/checkpoint work; refuse stop.'
receipt={'verdict':'EMPTY_OWNED_R121_STOPPED_FOR_REGIONALLY_BOUNDED_LOGGED_SUCCESSOR','PID':p.pid,'command_line':cmd,'creation_unix':p.create_time(),'CPU_user_seconds':p.cpu_times().user,'CPU_system_seconds':p.cpu_times().system,'accepted_geometry':0,'last_reported_mesh_coordinates':189905,'source_script_sha256':hashlib.sha256((H/'construct_major_rail_coupled_source_exit_r121.py').read_bytes()).hexdigest(),'successor_requires_exact_prior_CORE_source_keys_and_all_new_CORE_components':True,'native_jobs':0,'board_written':False,'stopped_unix':time.time(),'finite_search_failure_not_no_path_proof':True}
p.terminate();p.wait(timeout=15)
(out/'deliberate-stop-receipt-r123.json').write_text(json.dumps(receipt,indent=1)+'\n')
print('EXACT_OWN_R121_EMPTY_STOPPED',p.pid)
