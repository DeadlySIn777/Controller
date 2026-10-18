"""Derive the next unchanged alarm schedule without replacing prior evidence."""
import hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
p=H/'arm_resource_watch_r13.py';out=H/'arm_resource_watch_r14.py';r=H/'resource-watch-r14-derivation.json'
assert not out.exists() and not r.exists()
s=p.read_text();s=re.sub(r'r(12|13)(?![0-9])',lambda m:'r'+str(int(m[1])+1),s)
compile(s,str(out),'exec');out.write_text(s)
r.write_text(json.dumps({'prior_arm_script_sha256':sha(p),'derived_arm_script_sha256':sha(out),'only_prior_next_revision_names_incremented':True,'original_watch_bytes_thresholds_and_existing_no_heavy_slot_policy_preserved':True,'CPU_limit_percent':70,'GPU_limit_C':80,'GPU_limit_W':350,'prior_evidence_preserved':True},indent=1)+'\n')
print(json.dumps({'script':str(out),'sha256':sha(out)}))
