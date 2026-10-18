"""Preserve r12 and derive its unchanged automatic alarm re-arm."""
import hashlib,json,re
from pathlib import Path
H=Path(__file__).resolve().parent
p=H/'arm_resource_watch_r12.py';out=H/'arm_resource_watch_r13.py';assert not out.exists()
s=p.read_text();s=re.sub(r'r1[12]',lambda m:{'r11':'r12','r12':'r13'}[m.group()],s)
compile(s,str(out),'exec');out.write_text(s)
(H/'resource-watch-r13-derivation.json').write_text(json.dumps({'prior_arm_sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'derived_arm_sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'thresholds_unchanged':True,'new_heavy_slots':0},indent=1)+'\n')
