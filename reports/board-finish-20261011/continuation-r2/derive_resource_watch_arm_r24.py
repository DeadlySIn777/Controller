"""Schedule the same existing CPU/GPU watch, changing revision names only."""
import hashlib,json
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'arm_resource_watch_r23.py';target=H/'arm_resource_watch_r24.py';assert not target.exists()
code=source.read_text().replace('r22','PRIOR_REV_TOKEN').replace('r23','r24').replace('PRIOR_REV_TOKEN','r23');compile(code,str(target),'exec');target.write_text(code)
(H/'resource-watch-r24-arm-derivation.json').write_text(json.dumps({'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'target_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'only_existing_watch_revision_names_changed':True,'new_heavy_slots':0},indent=1)+'\n')
