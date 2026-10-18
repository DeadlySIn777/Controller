"""Keep the existing resource alarms armed without adding heavy work."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
prior=H/'arm_resource_watch_r21.py';out=H/'arm_resource_watch_r22.py';assert not out.exists();s=prior.read_text();s=s.replace('r20','PRIOR_WATCH_REV_TOKEN').replace('r21','r22').replace('PRIOR_WATCH_REV_TOKEN','r21');compile(s,str(out),'exec');out.write_text(s)
(H/'resource-watch-r22-arm-derivation.json').write_text(json.dumps({'prior_arm_sha256':sha(prior),'new_arm_sha256':sha(out),'only_previous_current_revision_names_changed':True,'unchanged_watch_bytes_required':'8dcbd7d7aed01d63b5bbfc72979463465a889ccfdc6114dd9250cda75024ea1e','CPU_percent_limit':70,'GPU_C_limit':80,'GPU_W_limit':350,'new_heavy_slots':0},indent=1)+'\n');print('R22_RESOURCE_ARM_DERIVED',sha(out),flush=True)
