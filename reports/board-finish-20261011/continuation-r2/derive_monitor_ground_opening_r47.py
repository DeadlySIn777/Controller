"""Couple one geometry-only monitor reroute to a real ordinary ground source via."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;src=H/'nominate_field_ground_bulge_opening_r40.py';dst=H/'nominate_monitor_ground_opening_r47.py';assert not dst.exists()
t=src.read_text()
for a,b in {'field-health-wall-bulge-r39':'field-monitor-uv-wall-geometry-r46','controller-ground-bare-r40':'controller-monitor-ground-r47',"targets=['d64c464d-de71-4c7e-9d98-b870e2ad977f']":"targets=['6d65e765-0689-4977-98aa-e5c00d7c8922']",'R24_':'R47_','exact-owned-health-wall-reroute':'exact-owned-monitor-wall-reroute','exact_owned_old_health_track_removed':'exact_owned_old_monitor_track_removed','whole_health_retained_contact_and_reference_audit':'whole_monitor_retained_contact_and_reference_audit'}.items():assert a in t,a;t=t.replace(a,b)
marker="if ok:carves+=cuts;"
assert marker in t
t=t.replace("if ok:carves+=cuts;","if ok:\n     actual=root(F.graph(trial,NET));reference={l:unary_union([q['shape']for q in actual if q['layer']==l])for l in ('In1.Cu','In4.Cu')};monitorbody=unary_union([LineString([t['a'],t['b']]).buffer(t['w']/2,resolution=256)for t in health['new_tracks']]);record['coupled_monitor_return_missing_mm2']={l:monitorbody.difference(reference[l]).area for l in reference};record['coupled_monitor_return_reference_pass']=min(record['coupled_monitor_return_missing_mm2'].values())==0\n    if ok:carves+=cuts;")
compile(t,str(dst),'exec');dst.write_text(t)
(H/'monitor-ground-r47-derivation.json').write_text(json.dumps({'source_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'target_sha256':hashlib.sha256(dst.read_bytes()).hexdigest(),'scope':'exact b7 voltage-monitor-preserving detour and ordinary .5/.2 ground source fanout only; all6 blockers and source returns checked','reference_open_in_R46_preserved_and_recomputed_with_actual_coupled_return':True,'all_other_contacts_refs_native_current_open':True,'adopted':False,'board_written':False},indent=1)+'\n')
print(dst)
