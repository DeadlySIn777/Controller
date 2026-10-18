"""Preserve broad R60 constructor stop and bound computation to actual lost routes."""
import datetime,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=H/'restore_old_ground_reference_masks_r60.py';dst=H/'restore_old_ground_reference_masks_r62.py';assert not dst.exists()
old=H/'SAFE-old-source-ground-reference-remove-only-masks-r60';assert old.exists()and not(old/'model.pkl').exists()
(old/'deliberate-constructor-stop.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'exact_verified_process_id':20080,'reason':'Avoid recomputing all previously unchanged source-body shadows; independent R57 pins exact303 actual lost old outer routes. Removing new foreign planes can only restore projected old-ground area, so construct around the exact lost routes and verify all76 contacts/source/reference anew.','stopped_before_any_geometry_proposal_or_board':True,'native_jobs':0,'adopted':False},indent=1)+'\n')
s=src.read_text().replace('SAFE-old-source-ground-reference-remove-only-masks-r60','SAFE-old-source-ground-reference-remove-only-masks-r62').replace('R60_','R62_')
a=" refdata=[]\n for ground,ref in"
b=" lostfile=H/'SAFE-logic-four-independent-full-r57/reference-checkpoint.json';assert sha(H/'SAFE-logic-four-independent-full-r57/receipt.json')=='203e598c36adb975374b393929fcb26e40a42315a3eb35eb80a46e967e5b6f52'\n lostrows=json.loads(lostfile.read_bytes());lostby={row['net']:{q['uuid']for q in row['retained_outer_reference_losses']}for row in lostrows};assert sum(map(len,lostby.values()))==303\n refdata=[]\n for ground,ref in"
assert a in s;s=s.replace(a,b)
a="   for t in h['tracks']:\n    if t['layer']!=outer"
b="   for t in h['tracks']:\n    if t['uuid']not in lostby[ground]:continue\n    if t['layer']!=outer"
assert a in s;s=s.replace(a,b)
compile(s,str(dst),'exec');dst.write_text(s)
(H/'ground-reference-mask-r62-derivation.json').write_text(json.dumps({'source_sha256':sha(src),'derived_sha256':sha(dst),'only_constructive_scope_changed':'Protect all previously source-covered parts of exact303 independently identified old routes rather than recomputing all unchanged routes. All old contacts/source/reference gates remain mandatory.','native_jobs':0,'adopted':False},indent=1)+'\n')
print(dst)
