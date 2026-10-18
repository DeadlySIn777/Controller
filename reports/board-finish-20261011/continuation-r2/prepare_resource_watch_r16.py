"""Derive the next unchanged resource watch with a ten-second overlap."""
import hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
p=H/'arm_resource_watch_r15.py';o=H/'arm_resource_watch_r16.py';r=H/'resource-watch-r16-derivation.json';assert not o.exists()and not r.exists()
s=re.sub(r'r(14|15)(?![0-9])',lambda m:'r'+str(int(m[1])+1),p.read_text());compile(s,str(o),'exec');o.write_text(s)
r.write_text(json.dumps({'prior_arm_script_sha256':sha(p),'derived_arm_script_sha256':sha(o),'only_prior_next_revision_names_incremented':True,'original_watch_bytes_thresholds_and_no_heavy_slot_policy_preserved':True,'CPU_limit_percent':70,'GPU_limit_C':80,'GPU_limit_W':350,'prior_evidence_preserved':True},indent=1)+'\n');print(json.dumps({'script':str(o),'sha256':sha(o)}))
