"""Continue the unchanged CPU/GPU alarms on the next existing interval."""
import hashlib,json,runpy
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'arm_resource_watch_r28.py';target=H/'arm_resource_watch_r29.py'
assert not target.exists()
code=source.read_text().replace('r28','r29').replace('r27','r28')
compile(code,str(target),'exec');target.write_text(code)
receipt=H/'resource-watch-arm-derivation-r29.json';assert not receipt.exists()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
receipt.write_text(json.dumps({'source_file':str(source),'source_sha256':sha(source),'derived_file':str(target),'derived_sha256':sha(target),'only_revision_folder_numbers_changed':True,'CPU_limit_percent':70,'GPU_limit_C':80,'GPU_limit_W':350,'new_heavy_slots':0},indent=1)+'\n')
runpy.run_path(str(target),run_name='__main__')
