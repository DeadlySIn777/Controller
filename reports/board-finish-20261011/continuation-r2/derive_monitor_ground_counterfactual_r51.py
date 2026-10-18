"""Exact temporary UV-wall absence to locate a coupled source-rooted ground site."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;src=H/'nominate_monitor_ground_opening_r47.py';dst=H/'nominate_monitor_ground_counterfactual_r51.py';assert not dst.exists();t=src.read_text()
t=t.replace('controller-monitor-ground-r47','controller-monitor-ground-r51').replace('R47_','R51_')
marker="old=health['removed_exact_host_track'];assert next(t for t in h['tracks']if t['uuid']==old['uuid'])==old;"
assert marker in t;t=t.replace(marker,"health=copy.deepcopy(health);health['new_tracks']=[];old=health['removed_exact_host_track'];assert next(t for t in h['tracks']if t['uuid']==old['uuid'])==old;")
t=t.replace("record['coupled_monitor_return_reference_pass']=min(record['coupled_monitor_return_missing_mm2'].values())==0","record['coupled_monitor_return_reference_pass']=False;record['monitor_UV_route_restoration']='MISSING_TEMPORARY_GEOMETRY_COUNTERFACTUAL_NEVER_NATIVE_OR_ADOPTED'")
t=t.replace('ORDINARY_GROUND_NEW_ONLY_ANTIPAD_SOURCE_NOMINATIONS_FULL_GATE_OPEN','TEMPORARY_UV_WALL_ABSENCE_GROUND_SITE_NOMINATION_EXACT_MONITOR_RESTORATION_REQUIRED')
compile(t,str(dst),'exec');dst.write_text(t)
(H/'monitor-ground-counterfactual-r51-derivation.json').write_text(json.dumps({'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'target_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'temporary_removed_exact_UV_wall':'b7ddd466-0bed-4b5a-968d-9ef0ce166364','originalmonitorrestorationmandatory':'Only geometric nomination. No native board or acceptance may use the temporary removed route.','all6ordinary_Cu_drill_SMD_guards_retained':True,'adopted':False},indent=1)+'\n')
print(dst)
