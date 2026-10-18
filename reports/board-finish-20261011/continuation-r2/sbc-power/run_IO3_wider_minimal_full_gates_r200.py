"""Independent full gates and literal final .30-width on one confined host slot."""
from pathlib import Path
import sys,runpy,json,hashlib,pickle
from shapely.geometry import LineString
P=Path(__file__).resolve().parent;mp=P/'IO3-group6-wider-minimal-canonical-union-r196/model.pkl';assert mp.exists()
g,h,b,z,c=pickle.loads(mp.read_bytes());q=next(q for q in z if(q['net'],q['layer'])==('/IO_3V3','In3.Cu'))
f=P/'IO3-group6-wider-existing-port-r193/receipt.json';r=json.loads(f.read_bytes());a=r['accepted'][0];core=LineString(a['points_mm']).buffer(.15,quad_segs=256)
outside=core.difference(q['zone_outline_shape']);assert q['zone_outline_shape'].covers(core),('literal_final_wider_core_not_covered',outside.area)
(P/'IO3-wider-final-canonical-width-r200.json').write_text(json.dumps({'model_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'new_branch_UUID':a['new_UUID'],'canonical_IO3_In3_UUID':q['uuid'],'literal_full_capsule_width_mm':.3,'literal_final_intended_capsule_covered':True,'outside_area_mm2':outside.area,'physical_own_drill_overlap_mm2':core.intersection(q['zone_outline_shape'].difference(q['shape'])).area,'no_current_or_thermal_qualification_inferred':True},indent=1)+'\n')
del g,h,b,z,c,q
results=[]
for name in ('audit_IO3_wider_minimal_geometry_r197.py','audit_IO3_wider_minimal_original_contacts_r198.py','audit_IO3_wider_minimal_all76_r199.py'):
 f=P/name;print('IO3_WIDER_MINIMAL_GATE_START',name,flush=True);sys.argv=[str(f),str(mp)];runpy.run_path(str(f),run_name='__main__');results.append({'script':name,'script_sha256':hashlib.sha256(f.read_bytes()).hexdigest()})
(P/'IO3-wider-minimal-sequential-gate-run-r200.json').write_text(json.dumps({'model_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'completed':results,'native_jobs':0,'board_written':False},indent=1)+'\n')
