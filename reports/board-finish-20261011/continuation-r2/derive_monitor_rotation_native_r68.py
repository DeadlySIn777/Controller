"""Preserve failed test shell and fix PATH/exact chunk bytes without altering native inputs."""
import datetime,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=H/'stage_monitor_native_rotation_r67.py';dst=H/'stage_monitor_native_rotation_r68.py';assert not dst.exists();s=src.read_text().replace('field-monitor-native-R9026-rotation-r67','field-monitor-native-R9026-rotation-r68')
a="newfile.write_text(new)";assert a in s;s=s.replace(a,"newfile.write_bytes(new.encode())")
a="with(out/'native.log').open('w')as log:run=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT)"
b="env=os.environ.copy();env['PATH']='C:/Program Files/Git/usr/bin;C:/Program Files/Git/bin;'+env['PATH']\n with(out/'native.log').open('w')as log:run=subprocess.run(cmd,stdout=log,stderr=subprocess.STDOUT,env=env)"
assert a in s;s=s.replace(a,b);compile(s,str(dst),'exec');dst.write_text(s)
(H/'field-monitor-native-R9026-rotation-r67/failed-shell-stop.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exact_verified_shell_PID':41196,'parent_host_PID':31384,'reason':'Host omitted Git utilities from PATH: mkdir could not acquire any slot and sleep was unavailable. Native KiCad script never started.','native_rotation_verdict':'UNMEASURED_TOOL_ENVIRONMENT_FAIL','stopped_only_own_waiting_shell':True,'original_source_and_other_running_native_measurement_untouched':True},indent=1)+'\n')
(H/'monitor-native-r68-derivation.json').write_text(json.dumps({'source_sha256':sha(src),'derived_sha256':sha(dst),'changes':'Correct helper shell PATH; exact footprint chunk uses byte write instead of Windows newline translation. Same one-root native pose operation and guards; no geometry/header/oldCu/source changes.','existing_test_slot_only':True,'new_heavy_slots':0,'adopted':False},indent=1)+'\n');print(dst)
