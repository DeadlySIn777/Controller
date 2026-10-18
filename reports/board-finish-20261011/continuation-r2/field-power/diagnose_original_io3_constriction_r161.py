"""Geometry only: original IO3 contact path and minimum-width provenance."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
from shapely.ops import unary_union
from inventory import sha
H=Path(__file__).resolve().parent;O=H/'original-IO3-constriction-diagnosis-r161'
def main():
 assert not O.exists();O.mkdir();rp=H/'paired-regional-six-regulated-full-contact-audit-r142';old=pickle.loads((rp/'ROOT_R22-regional-groups.pkl').read_bytes())['/IO_3V3'];new=pickle.loads((rp/'REG_R130-regional-groups.pkl').read_bytes())['/IO_3V3'];A=unary_union([q['shape'] for q in old[0] if q['kind']=='fill' and q['layer']=='In2.Cu']);start=unary_union([q['shape'] for q in new[5] if q['layer']=='In2.Cu']);end=unary_union([q['shape'] for q in new[0] if q['layer']=='In2.Cu']);rows=[]
 for width in (0,.3,.25,.2,.15,.1,.05,.02,.005,.001):
  free=A if not width else A.buffer(-width/2-.00002);parts=[free] if free.geom_type=='Polygon' else [q for q in getattr(free,'geoms',[]) if q.geom_type=='Polygon'];joins=[q for q in parts if not q.intersection(start).is_empty and not q.intersection(end).is_empty];rows.append({'eroded_preservation_mask_width_mm':width,'connected_polygon_count':len(parts),'components_attaching_both_prior_IO3_partitions':len(joins),'candidate_bounds_mm':[list(q.bounds) for q in joins]})
 (O/'receipt.json').write_text(json.dumps({'verdict':'OLD_CONDUCTOR_DIAGNOSTIC_NOT_NATIVE_CURRENT_PROOF','parent_receipt_sha256':sha(rp/'receipt.json'),'rows':rows,'no_new_IO3_Cu_or_width_rule_exception_proposed':True,'tiny_old_fill_retention_is_not_native_minimum_feature_or_current_qualification':True},indent=1)+'\n',encoding='utf-8');print('R161',sha(O/'receipt.json'),json.dumps(rows),flush=True)
if __name__=='__main__':main()
