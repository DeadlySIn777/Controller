"""Schedule the next unchanged resource-watch interval without new work slots."""
import hashlib,json,runpy
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'arm_resource_watch_r31.py';target=H/'arm_resource_watch_r32.py';assert not target.exists()
code=source.read_text().replace('r31','r32').replace('r30','r31');compile(code,str(target),'exec');target.write_text(code)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();receipt=H/'resource-watch-arm-derivation-r32.json';assert not receipt.exists();receipt.write_text(json.dumps({'source_file':str(source),'source_sha256':sha(source),'derived_file':str(target),'derived_sha256':sha(target),'only_revision_folder_numbers_changed':True,'CPU_limit_percent':70,'GPU_limit_C':80,'GPU_limit_W':350,'new_heavy_slots':0},indent=1)+'\n');runpy.run_path(str(target),run_name='__main__')
