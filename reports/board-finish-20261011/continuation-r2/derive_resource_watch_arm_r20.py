"""Advance only the saved watch revision names, retaining all thresholds and monitor bytes."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
src=H/'arm_resource_watch_r19.py';dst=H/'arm_resource_watch_r20.py';assert not dst.exists()
s=src.read_text().replace('r18','PREVIOUS_WATCH_TOKEN').replace('r19','r20').replace('PREVIOUS_WATCH_TOKEN','r19');compile(s,str(dst),'exec');dst.write_text(s)
(H/'resource-watch-r20-arm-derivation.json').write_text(json.dumps({'source_sha256':sha(src),'derived_sha256':sha(dst),'only_revision_names_advanced':True,'CPU_limit_percent':70,'GPU_limit_C':80,'GPU_limit_W':350,'new_heavy_slots':0,'watch_bytes_to_remain_exact':True},indent=1)+'\n')
print(dst)
