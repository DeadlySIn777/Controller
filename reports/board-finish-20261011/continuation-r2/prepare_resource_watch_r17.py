"""Advance only revision names of the proven unchanged alarm scheduler."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
source=H/'arm_resource_watch_r16.py';target=H/'arm_resource_watch_r17.py';assert not target.exists();s=source.read_text();s=s.replace('r16','r17').replace('r15','r16');compile(s,str(target),'exec');target.write_text(s);(H/'resource-watch-r17-preparation.json').write_text(json.dumps({'source_sha256':sha(source),'derived_sha256':sha(target),'only_revision_names_changed':True,'CPU_limit_percent':70,'GPU_limit_C':80,'GPU_limit_W':350,'new_heavy_slots':0},indent=1)+'\n')
