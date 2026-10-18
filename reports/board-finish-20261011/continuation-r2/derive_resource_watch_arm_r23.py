"""Rearm only the unchanged existing watch before R22 expires."""
import json,hashlib
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'arm_resource_watch_r22.py';target=H/'arm_resource_watch_r23.py'
assert not target.exists()
code=source.read_text().replace('r21','PREVIOUS_REV_TOKEN').replace('r22','r23').replace('PREVIOUS_REV_TOKEN','r22')
compile(code,str(target),'exec');target.write_text(code)
receipt={'source_sha256':hashlib.sha256(source.read_bytes()).hexdigest(),'target_sha256':hashlib.sha256(target.read_bytes()).hexdigest(),'only_existing_watch_revision_names_changed':True,'new_heavy_slots':0}
(H/'resource-watch-r23-arm-derivation.json').write_text(json.dumps(receipt,indent=1)+'\n')
print(json.dumps(receipt))
