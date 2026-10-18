"""Verify the host floating native-fill record path without changing inputs."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,inspect,hashlib
from pathlib import Path
from shapely import get_precision
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for n in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/n))
import complete_geometry_r2 as G
import contact_layout as C
from inventory import sha
O=H/'floating-native-fill-record-roundtrip-r248'
def main():
 assert not O.exists();O.mkdir();f=H/'REG-seven-corrected-current-head-conservative-delta-audit-r242/model.pkl';g,h,b,z,c=pickle.loads(f.read_bytes());nativeids={q['uuid'] for q in h['zones']};rows=[]
 for q in c['zones']:
  if q['uuid'] not in nativeids:continue
  for layer,records in q['fills'].items():
   source=C.poly(records);out=[C.poly(G.records(x)) for x in source];after=[x for xs in out for x in xs]
   # Reconstructing each polygon avoids any new union/snap operator.
   assert len(source)==len(after),(q['uuid'],layer,'component count')
   exact=all(a.wkb==b.wkb for a,b in zip(source,after));coords=all(list(a.exterior.coords)==list(b.exterior.coords) and [list(r.coords) for r in a.interiors]==[list(r.coords) for r in b.interiors] for a,b in zip(source,after))
   grids=[get_precision(x) for x in after]
   rows.append({'native_UUID':q['uuid'],'layer':layer,'polygon_count':len(source),'coordinate_arrays_exact':coords,'WKB_exact':exact,'all_roundtrip_grid_zero':all(v==0 for v in grids)})
   assert exact and coords and all(v==0 for v in grids),rows[-1]
 funcs={'records':inspect.getsource(G.records),'components':inspect.getsource(G.p.hubs.components),'poly':inspect.getsource(C.poly)}
 (O/'exact-runtime-functions.json').write_text(json.dumps(funcs,indent=1)+'\n',encoding='utf-8');(O/'rows.json').write_text(json.dumps(rows,indent=1)+'\n',encoding='utf-8');receipt={'verdict':'FLOATING_NATIVE_FILL_RECORD_COORDINATES_WKB_AND_ZERO_GRID_EXACT','input_model_sha256':sha(f),'native_fill_layer_rows':len(rows),'native_fill_polygons':sum(r['polygon_count'] for r in rows),'runtime_function_receipt_sha256':sha(O/'exact-runtime-functions.json'),'rows_sha256':sha(O/'rows.json'),'no_projection_geometry_or_native_adoption':True};(O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(json.dumps(receipt),flush=True);print('R248',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
