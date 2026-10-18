"""Permit the exact same-net track termination on its actual source barrel."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=H/'nominate_monitor_rotation_source_via_r64.py';dst=H/'nominate_monitor_rotation_source_via_r66.py';assert not dst.exists();s=src.read_text().replace('field-monitor-R9026-rotation-source-via-r64','field-monitor-R9026-rotation-source-termination-r66').replace('controller-monitor-rotation-r64/','controller-monitor-rotation-r66/').replace('R64_','R66_')
a="+[N.bounded_disk(v,v['drill']/2)for v in mh['vias']]"
b="+[N.bounded_disk(v,v['drill']/2)for v in mh['vias']if not(C.norm(raw)==ground and v['uuid']==own_target['uuid'] and [v['x'],v['y']]==end)]"
assert a in s;s=s.replace(a,b)
a="'courtyard_changes':courtyard_changes}";b="'courtyard_changes':courtyard_changes,'only_own_actual_source_barrel_termination_excluded_from_foreign_hole_trace_clearance':own_target['uuid']if C.norm(raw)==ground else None}"
assert a in s;s=s.replace(a,b)
compile(s,str(dst),'exec');dst.write_text(s)
(H/'monitor-source-termination-r66-derivation.json').write_text(json.dumps({'source_sha256':sha(src),'derived_sha256':sha(dst),'R64_early_failure':'Ground trace endpoint was wrongly prohibited by the drill of the exact same-net via it must terminate on.','exact_scoped_fix':'Exclude only same-net actual source-target via from foreign-hole clearance for this terminating ground trace; newvia SMD/everyotherhole pitch/ring native rules unchanged, all physical drills remain in connectivity and source model.','all_source_reference_current_threshold_native_gates':'OPEN','native_jobs':0,'adopted':False},indent=1)+'\n');print(dst)
