from pathlib import Path
import json,hashlib
H=Path(__file__).resolve().parent;p=H/'inventory_AO1_ground_island_actual_loads_r660.py';s=p.read_text()
(H/'AO1-two-joined-ground-islands-exact-fresh-source-downstream-load-catalogue-r660/failure.json').write_text(json.dumps({'verdict':'READER_SCHEMA_FAILURE_RETAINED','error':"R632 pad catalogue uses UUID/layers; r660 reader requested uuid/layer",'source_SHA256':hashlib.sha256(p.read_bytes()).hexdigest(),'native_jobs':0,'material_changes':0},indent=1)+'\n')
for old,new in[("'UUID':p['uuid'],'layer':p['layer']","'UUID':p['UUID'],'layers':p['layers']"),('load-catalogue-r660','load-catalogue-r662'),('R660_COMPLETE','R662_COMPLETE')]:
 assert s.count(old)==1;s=s.replace(old,new)
out=H/'inventory_AO1_ground_island_actual_loads_r662.generated.py';assert not out.exists();out.write_text(s)
