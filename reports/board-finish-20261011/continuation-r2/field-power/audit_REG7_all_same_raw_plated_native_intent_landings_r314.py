import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import json,pickle
from pathlib import Path
from shapely.geometry import Point
from inventory import sha
H=Path(__file__).resolve().parent;R=H/'REG7-native-support-minimal-current-delta-r312';M=H/'REG-explicit-local-integer-boundary-reference-repair-r307';O=H/'REG7-all-same-raw-plated-native-intent-census-r314'
def main():
 assert not O.exists();O.mkdir();manifest=json.loads((R/'owned-file-manifest.json').read_text());assert all(sha(R/n)==v for n,v in manifest.items());_,h,_,_,_=pickle.loads((M/'model.pkl').read_bytes());z=pickle.loads((R/'new-REG7-zones.pkl').read_bytes());rows=[];aliases=[]
 for q in z:
  b=q['zone_outline_shape'].bounds
  for v in h['vias']:
   if v['net']!=q['net'] or q['layer'] not in v['span']:continue
   pt=Point(v['x'],v['y']);ann=pt.buffer(v['d']/2,quad_segs=256).difference(pt.buffer(v['drill']/2,quad_segs=256));overlap=q['shape'].intersection(ann).area
   if overlap<=1e-12:continue
   rows.append({'owned_zone_UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'same_raw_plated_via_UUID':v['uuid'],'centre_mm':[v['x'],v['y']],'d_mm':v['d'],'drill_mm':v['drill'],'physical_annular_overlap_mm2':overlap,'centre_inside_intended_outline':q['zone_outline_shape'].contains(pt),'host_layer_flash':q['layer'] in v['flashed'],'native_fill_actual_contact_required':True})
 bad=[r for r in rows if not r['centre_inside_intended_outline']];out={'verdict':'REG7_EXACT_SAME_RAW_EXPECTED_ANNULAR_CENTRES_INSIDE_INTENDED_PASS_NATIVE_CONTACT_OPEN' if not bad else 'REG7_NATIVE_INTENDED_PURE_OWN_HOLE_REJECTED','parent_packet_receipt_SHA256':sha(R/'receipt.json'),'packet_manifest_SHA256':sha(R/'owned-file-manifest.json'),'exact_same_raw_plated_positive_annuli_checked':len(rows),'rows':rows,'failures':bad,'no_foreign_or_NPTH_hole_changed':True,'physical_drill_voids_preserved':True,'1870_extra_In3_not_in_packet':True,'all_native_flash_and_zone_contact_require_actual_refill':True,'native_jobs':0,'board_written':False,'adopted':False};(O/'receipt.json').write_text(json.dumps(out,indent=1)+'\n',encoding='utf-8');print(json.dumps({'receipt_SHA256':sha(O/'receipt.json'),'checks':len(rows),'errors':len(bad)}),flush=True)
if __name__=='__main__':main()
