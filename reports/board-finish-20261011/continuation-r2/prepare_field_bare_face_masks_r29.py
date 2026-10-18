"""Freeze exact outer pockets and legal all-layer via regions for wall attribution."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;s=H/'nominate_field_ground_owned_antipads_r28.py';o=H/'diagnose_field_bare_face_masks_r29.py';text=s.read_text()
a="   print('R28_FIELD_SITE_FACE',pad['ref'],radius,region.area,len(faces),flush=True)";b="   (out/(uid+'-'+str(radius)+'-via-legal.wkb')).write_bytes(region.wkb)\n   for fi,f in enumerate(faces):(out/(uid+'-'+str(radius)+'-outer-face-'+str(fi)+'.wkb')).write_bytes(f.wkb)\n   print('R29_OUTER_FACE_GEOMETRY',pad['ref'],radius,[{'area':f.area,'bounds':list(f.bounds),'reaches_window_edge':f.distance(win.boundary)<.101,'nearest_via_site_distance':f.distance(region)}for f in faces],flush=True)"
assert text.count(a)==1 and not o.exists();text=text.replace(a,b).replace('controller-ground-bare-r28/','controller-ground-bare-r29/');compile(text,str(o),'exec');o.write_text(text)
(H/'field-bare-face-masks-r29-derivation.json').write_text(json.dumps({'source_sha256':hashlib.sha256(s.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(o.read_bytes()).hexdigest(),'all_actual_ordinary_dimensions_source_spacing_area_and_mask_rules_unchanged':True,'only_face_and_site_WKB_bounds_and_fresh_UUID_seed_added':True,'board_written':False,'native_jobs':0},indent=1)+'\n')
