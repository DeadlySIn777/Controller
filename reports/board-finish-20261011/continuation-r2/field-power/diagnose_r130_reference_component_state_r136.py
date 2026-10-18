"""Separate geometric source-island loss from serialized precision replay."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json
from pathlib import Path
from shapely.geometry import box
from shapely.ops import unary_union
from shapely import get_precision
import contact_layout as C
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'));import guarded_power_projection_r44 as P
O=H/'regulated-r130-reference-state-diagnostic-r136'
def write(path,data):path.write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();old=H.parent/'safe-logic-five-and-fag-margin-r22';new=H/'safe-root22-regulated-source-contact-audit-r130';gs=[]
 for base in (old,new):
  groups=pickle.loads((base/'groups.pkl').read_bytes())['/motherboard_motors/FIELD_GND'];root=next(xs for xs in groups if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11003','2') for q in xs));gs.append((groups,root))
 win=box(315,141,326,147);rows=[]
 for q in gs[0][1]:
  if q['kind']!='fill' or q['layer']!='In1.Cu' or not q['shape'].intersects(win):continue
  newer=[x for x in gs[1][1] if x['kind']=='fill' and x['uuid']==q['uuid'] and x['layer']==q['layer']];ns=unary_union([x['shape'] for x in newer]);allnew=unary_union([x['shape'] for group in gs[1][0] for x in group if x['kind']=='fill' and x['uuid']==q['uuid'] and x['layer']==q['layer']]);lost=q['shape'].difference(ns);rows.append({'fill_uuid':q['uuid'],'old_area_mm2':q['shape'].area,'new_root_shape_count':len(newer),'new_root_union_area_mm2':ns.area,'old_to_new_root_removed_mm2':lost.area,'old_to_all_new_removed_mm2':q['shape'].difference(allnew).area,'old_to_new_root_removed_near13tracks_mm2':lost.intersection(win).area,'old_sha256':P.digest(q['shape']),'new_root_union_sha256':P.digest(ns),'old_loaded_precision':get_precision(q['shape'])})
 write(O/'detail.json',rows);write(O/'receipt.json',{'verdict':'REFERENCE_COMPONENT_STATE_DIAGNOSTIC_ONLY','old_model_sha256':sha(old/'model.pkl'),'new_model_sha256':sha(new/'model.pkl'),'detail_sha256':sha(O/'detail.json'),'board_written':False});print(json.dumps(rows),flush=True)
if __name__=='__main__':main()
