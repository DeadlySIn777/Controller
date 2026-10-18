"""Freeze exact primary outside-R witnesses; no model or geometry mutation."""
import os
os.environ.update(OMP_NUM_THREADS='2',MKL_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',NUMEXPR_NUM_THREADS='2')
import psutil
psutil.Process().cpu_affinity(list(range(16,28)))
psutil.Process().nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
from pathlib import Path
import json,hashlib
from shapely import from_wkb,get_precision
H=Path(__file__).resolve().parent
I=H/'FIELD5-R385-minimal-R155-immutable-parent-raw-FAIL-diagnostic-r451'
O=H/'FIELD5-R451-record162-direct-outside-R-witness-attribution-r453'
O.mkdir(exist_ok=False)
key='c1d27fa1-452b-4e27-985d-5ad23644d800-In4.Cu-immutable-parent-162-'
shapes={r:from_wkb((I/(key+r+'.wkb')).read_bytes())for r in('P','A','R','D','D_minus_R','after','gain')}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def desc(s):return {'geometry_type':s.geom_type,'is_empty':s.is_empty,'area_mm2':s.area,'length_mm':s.length,'bounds_mm':None if s.is_empty else list(s.bounds),'GEOS_grid_mm':get_precision(s),'WKB_sha256':hashlib.sha256(s.wkb).hexdigest()}
P,A,R,after=(shapes[k]for k in('P','A','R','after'))
w={
 'direct_before_outside_R_loss':A.difference(R).difference(after.difference(R)),
 'direct_after_outside_R_gain':after.difference(R).difference(A.difference(R)),
 'after_outside_P':after.difference(P),
 'A_outside_P':A.difference(P),
 'derived_gain_outside_R':shapes['gain'].difference(R),
 'actual_A_minus_after':A.difference(after),
}
rows={}
for role,s in w.items():
 f=O/(role+'.wkb');f.write_bytes(s.wkb);rows[role]={**desc(s),'file':str(f.resolve()),'file_sha256':sha(f),'distance_to_R_mm':None if s.is_empty else s.distance(R),'difference_from_R':desc(s.difference(R)),'difference_from_P':desc(s.difference(P)),'difference_from_after':desc(s.difference(after))}
receipt={'status':'FAIL_PRIMARY_DIRECT_OUTSIDE_R_PRESERVED_NO_MODEL_EMITTED','source_original_zone_UUID':'c1d27fa1-452b-4e27-985d-5ad23644d800','source_layer':'In4.Cu','immutable_original_record_index':162,'current_descendant_indices':[163],'formula':'after=P-((P-A)-R)','actual_identity':{r:{**desc(s),'file':str((I/(key+r+'.wkb')).resolve()),'file_sha256':sha(I/(key+r+'.wkb'))}for r,s in shapes.items()},'witnesses':rows,'no_geometry_coordinate_grid_or_model_mutation':True,'no_area_zero_waiver':True}
(O/'receipt.json').write_text(json.dumps(receipt,indent=2),encoding='utf-8')
print(json.dumps({'receipt_sha256':sha(O/'receipt.json'),'witnesses':rows},indent=2))
