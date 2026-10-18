"""Read-only exact raw/grid comparison of the nominated owned CORE wall."""
from pathlib import Path
import sys,pickle,json,hashlib
from shapely import set_precision,get_num_coordinates
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'field-power'))
import guarded_declared_settings_projection_r58 as N
src=H/'core1v2-extra-In4-source-guarded-input-r112/model.pkl'
old,h,b,z,current=pickle.loads(src.read_bytes())
q=next(x for x in z if x['uuid']=='c7e36847-4380-503d-80f2-836420105d9e')
result={'baseline_sha256':hashlib.sha256(src.read_bytes()).hexdigest(),'zone_UUID':q['uuid'],'pieces':[]}
for key in ('shape','zone_outline_shape'):
 s=q[key];t=set_precision(s,1e-6)
 result['pieces'].append({'key':key,'raw_sha256':N.digest(s),'grid_sha256':N.digest(t),'raw_coordinate_count':get_num_coordinates(s),'raw_area_mm2':s.area,'grid_added_mm2':t.difference(s).area,'grid_removed_mm2':s.difference(t).area,'geometrically_equals_grid':s.equals(t)})
print(json.dumps(result,indent=1))
