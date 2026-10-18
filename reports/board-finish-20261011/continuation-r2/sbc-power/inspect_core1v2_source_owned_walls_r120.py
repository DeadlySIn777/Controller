"""Describe exact owned walls around the proposed additional source collar."""
from pathlib import Path
import json,pickle,hashlib
from shapely.geometry import Point,LineString
H=Path(__file__).resolve().parent.parent
mp=H/'sbc-power/core1v2-extra-In4-source-guarded-input-r112/model.pkl'
g,h,b,z,c=pickle.loads(mp.read_bytes());v=next(q for q in h['vias'] if q['uuid']=='f6ad6a15-3a41-4605-9ad5-72f4ba7d5d92');pt=Point(v['x'],v['y']);rows=[]
for q in z:
    if q['layer']=='In4.Cu' and q['net']!=v['net'] and q['shape'].distance(pt)<5:
        rows.append({k:val for k,val in q.items() if k not in ('shape','zone_outline_shape')}|{'distance_to_source_center_mm':q['shape'].distance(pt),'shape_area_mm2':q['shape'].area,'shape_bounds_mm':list(q['shape'].bounds)})
print(json.dumps({'source_via':v,'near_owned_In4_walls':rows},indent=1),flush=True)
O=H/'sbc-power/core1v2-source-owned-wall-diagnostic-r120';assert not O.exists();O.mkdir()
(O/'receipt.json').write_text(json.dumps({'parent_model_sha256':hashlib.sha256(mp.read_bytes()).hexdigest(),'near_owned_In4_walls':rows,'native_jobs':0,'board_written':False},indent=1)+'\n')
