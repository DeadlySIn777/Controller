import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
psutil.Process().cpu_affinity([16,17])
from pathlib import Path
import hashlib,json,shapely
HERE=Path(__file__).resolve().parent;OUT=HERE/'native-integer-field-union-r1';CON=HERE/'native-50um-splice-construction-r5';assert not OUT.exists();OUT.mkdir()
def rows(s):
    result=[]
    for p in([s]if s.geom_type=='Polygon'else list(s.geoms)):
        rr=[]
        for ring in[p.exterior,*p.interiors]:
            cc=[]
            for x,y in list(ring.coords)[:-1]:
                xi,yi=round(x*1e6),round(y*1e6);assert abs(x-xi/1e6)<1e-12 and abs(y-yi/1e6)<1e-12;cc.append([xi,yi])
            rr.append(cc)
        result.append(rr)
    return result
files=[CON/'field-old-intent.wkb',CON/'field-support-patch.wkb'];old,support=[shapely.from_wkb(p.read_bytes())for p in files]
(OUT/'input.json').write_text(json.dumps({'old_field_integer_IU':rows(old),'support_integer_IU':rows(support),'input_sha256':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in files}},indent=2)+'\n')
print(json.dumps({'old_vertices':len(shapely.get_coordinates(old)),'support_vertices':len(shapely.get_coordinates(support))}))
