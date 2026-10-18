"""Locate finite-site rejection without relaxing source/physical guards."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;s=H/'nominate_field_ground_owned_antipads_r26.py';o=H/'nominate_field_ground_owned_antipads_r28.py';text=s.read_text()
a="   for _,inner,s,face in sorted(options,key=lambda x:x[:2]):";b="   print('R28_SITE_MEETING',pad['ref'],radius,'option_count',len(options),'same_outer_face_site_area',sum(region.intersection(f).area for f in faces),'source_area_by_inner',{inner:sum(region.intersection(f).intersection(N.bounded_buffer(sources[inner],.2)).area for f in faces)for inner in ('In1.Cu','In2.Cu','In3.Cu','In4.Cu')},flush=True)\n"+a
assert text.count(a)==1;text=text.replace(a,b)
a="    if not region.covers(site)or not face.covers(site)or ann.intersection(sources[inner]).area<.01:continue";b="    ov=ann.intersection(sources[inner]).area\n    if not region.covers(site)or not face.covers(site)or ov<.01:\n     print('R28_SITE_REJECT',pad['ref'],inner,[site.x,site.y],'region',region.covers(site),'face',face.covers(site),'source_annulus_area',ov,flush=True);continue"
assert text.count(a)==1;text=text.replace(a,b).replace('controller-ground-bare-r26/','controller-ground-bare-r28/').replace('R24_FIELD','R28_FIELD').replace('R24_COMPLETE','R28_COMPLETE');assert not o.exists();compile(text,str(o),'exec');o.write_text(text)
(H/'field-bare-face-diagnosis-r28-derivation.json').write_text(json.dumps({'source_sha256':hashlib.sha256(s.read_bytes()).hexdigest(),'derived_sha256':hashlib.sha256(o.read_bytes()).hexdigest(),'exact_all_actual_source_and_physical_guards_unchanged':True,'only_intermediate_face_and_site_rejection_counts_and_fresh_UUID_seed_added':True,'native_jobs':0,'board_written':False},indent=1)+'\n')
