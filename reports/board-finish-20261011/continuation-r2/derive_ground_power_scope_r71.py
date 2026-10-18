"""Correct R70 candidate field adapter; all qualification flags remain false."""
import datetime,hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=H/'restore_old_ground_reference_masks_r70.py';dst=H/'restore_old_ground_reference_masks_r71.py';assert not dst.exists();s=src.read_text().replace('SAFE-old-source-ground-reference-power-scope-proposal-r70','SAFE-old-source-ground-reference-power-scope-proposal-r71').replace('R70_','R71_')
a="power_UIDs={q['uuid']for q in candidates}";assert a in s;s=s.replace(a,"power_UIDs={q['exact_track_UUID']for q in candidates}")
compile(s,str(dst),'exec');dst.write_text(s)
(H/'SAFE-old-source-ground-reference-power-scope-proposal-r70/input-adapter-failure.json').write_text(json.dumps({'utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'script_sha256':sha(src),'failure':'Source proposal names exact_track_UUID; constructor mistakenly expected uuid. Stopped before any masks/model/source proof or native job.','adopted':False},indent=1)+'\n')
(H/'ground-power-scope-r71-derivation.json').write_text(json.dumps({'source_sha256':sha(src),'derived_sha256':sha(dst),'only_change':'Correct candidate UUID schema; R70/R71 classification remains an unaccepted PDN proposal with original strict checker FAIL kept.','native_jobs':0,'adopted':False},indent=1)+'\n');print(dst)
