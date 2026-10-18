"""Save strict geometry-only UV reroute candidates for a coupled return repair."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;src=H/'nominate_monitor_uv_wall_r45.py';dst=H/'nominate_monitor_uv_wall_geometry_r46.py';assert not dst.exists()
t=src.read_text().replace('field-monitor-uv-wall-reroute-r45','field-monitor-uv-wall-geometry-r46').replace('controller-monitor-wall-r45','controller-monitor-wall-r46').replace('R45_','R46_')
old='(.05,.1,.15,.2,.25,.3,.35,.4,.45,.5,.55,.6,.7,.8,1.,1.2,1.5,2.,-.1,-.2,-.3)';assert old in t;t=t.replace(old,'(-.3,-.2,-.1,.05,.1,.15,.2,.25,.3,.35,.4,.45,.5,.55,.6,.7,.8,1.,1.2,1.5,2.)')
old='if not errors and min(missing.values())==0:';assert old in t;t=t.replace(old,'if not errors:')
t=t.replace("'actual_adjacent_source_reference_layer':min(missing,key=missing.get)","'actual_adjacent_source_reference_layer':None,'return_reference_scope':'OPEN_COUPLED_GROUND_RETURN_REQUIRED_NO_REFERENCE_CREDIT'")
t=t.replace('STRICT_SAME_F_MONITOR_WALL_NOMINEE_REFERENCE_CONTACT_SOURCE_NATIVE_OPEN','STRICT_SAME_F_MONITOR_WALL_GEOMETRY_ONLY_COUPLED_RETURN_CONTACT_SOURCE_NATIVE_OPEN')
compile(t,str(dst),'exec');dst.write_text(t)
(H/'monitor-coupled-r46-derivation.json').write_text(json.dumps({'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'target_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'geometry_guards_unchanged':True,'reference_deficits_preserved_and_open':True,'purpose':'construct actual coupled source return, never accept missing reference','adopted':False,'board_written':False},indent=1)+'\n')
print(dst)
