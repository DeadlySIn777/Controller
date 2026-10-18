"""Preserve R618's reader failure; bind all actual zone profiles by native UUID."""
from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;src=H/'construct_XF_actual_J1_In1_positive_shadow_no_via_r618.py';dest=H/'construct_XF_actual_J1_In1_positive_shadow_no_via_r620.py';assert not dest.exists();text=src.read_text()
failure=H/'XF-actual-J1-positive-In1-shadow-no-drill-F-path-r618/failure.json';assert not failure.exists();failure.write_text(json.dumps({'status':'READER_FAILURE_NO_GEOMETRY_OR_ROUTE_VERDICT','error':'StopIteration while locating a native actual-fill zone UUID in a different host current zone-role context','script_SHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'native_jobs':0,'adopted':False,'correction':'R620 reads explicit clearance profiles from exact R157 native raw chunks, not a differently inventoried current zone-role list'},indent=1)+'\n')
text=text.replace('hashlib,time,uuid','hashlib,time,uuid,re')
text=text.replace("XF-actual-J1-positive-In1-shadow-no-drill-F-path-r618","XF-actual-J1-positive-In1-shadow-no-drill-F-path-r620").replace('R618','R620')
old="ng=json.loads(gf.read_bytes())"
new="ng=json.loads(gf.read_bytes());np=pin(P/'R155-known-reference-native-diagnostic-r157/copy/board.kicad_pcb','3e6b099d85e1cfc4f3b30eb69c4de91dde6440dbab007af59a94d2405c34cd38');native_inventory=K.C.inventory(np.read_bytes())[3];native_profiles={}\n+ for zone in ng['zones']:\n+  ch=native_inventory[zone['uuid']];m=re.search(rb'\\(connect_pads(?:\\s+[^()\\s]+)?\\s*\\(clearance\\s+([0-9.]+)\\)',ch);assert m,zone['uuid'];native_profiles[zone['uuid']]=float(m.group(1))"
new=new.replace('\n+ ','\n ')
assert old in text;text=text.replace(old,new)
old="oldzone=next(z for z in c['zones']if z['uuid']==zone['uuid']);req=max(.15,float(oldzone['clearance_mm']),domain_gap(zone['net'],LG))+.025"
new="current_profiles=[float(z['clearance_mm'])for z in c['zones']if z['uuid']==zone['uuid']];req=max([.15,native_profiles[zone['uuid']],domain_gap(zone['net'],LG)]+current_profiles)+.025"
assert old in text;text=text.replace(old,new)
text=text.replace("'guarded_mm':req,'mask':mask})\n holes,_", "'guarded_mm':req,'exact_native_profile_clearance_mm':native_profiles[zone['uuid']],'current_profile_values_mm':current_profiles,'mask':mask})\n holes,_")
dest.write_text(text);print('R620_SCRIPT',hashlib.sha256(dest.read_bytes()).hexdigest())
