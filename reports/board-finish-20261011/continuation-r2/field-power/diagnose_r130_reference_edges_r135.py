"""Exact retained reference loss cause attribution; no area waiver."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json
from pathlib import Path
from shapely.geometry import LineString
from shapely.ops import unary_union
import contact_layout as C
from inventory import sha
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H.parent/'sbc-power'))
import guarded_power_projection_r44 as P
O=H/'regulated-r130-reference-edge-diagnostic-r135'
def write(path,data):path.write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();base=H/'safe-root22-regulated-source-contact-audit-r130';g,h,b,z,after=pickle.loads((base/'model.pkl').read_bytes());old=H.parent/'safe-logic-five-and-fag-margin-r22';og=pickle.loads((old/'groups.pkl').read_bytes());ng=pickle.loads((base/'groups.pkl').read_bytes());net='/motherboard_motors/FIELD_GND';ref='J11003';a=next(xs for xs in og[net] if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs));bb=next(xs for xs in ng[net] if any(q['kind']=='pad' and(q['ref'],q['pin'])==(ref,'2') for q in xs));delta=unary_union([q['shape'] for q in a if q['kind']=='fill' and q['layer']=='In1.Cu']).difference(unary_union([q['shape'] for q in bb if q['kind']=='fill' and q['layer']=='In1.Cu']));tm={t['uuid']:t for t in h['tracks']};d=pickle.loads((H/'regulated-four-retained-hard-snapshot-r127/proposed-discrete.pkl').read_bytes());r=json.loads((base/'reference-losses.json').read_text())[0];rows=[]
 for loss in r['retained_outer_track_reference_losses']:
  t=tm[loss['uuid']];body=P.bounded_buffer(LineString([t['a'],t['b']]),t['w']/2);hit=body.intersection(delta);causes=[]
  for v in d['vias']:
   for local in (.15,.25):
    cutter=P.bounded_disk(v,max(v['d']/2+local+.025,v['drill']/2+.275));overlap=hit.intersection(cutter).area
    if overlap>1e-12:causes.append({'new_via':v['uuid'],'xy':[v['x'],v['y']],'native_local_clearance_mm':local,'loss_piece_overlap_mm2':overlap})
  rows.append({'track':t,'reported_lost_mm2':loss['prior_source_reference_lost_mm2'],'bounded_true_cap_lost_mm2':hit.area,'bounds':list(hit.bounds),'new_via_cause_rows':causes})
 write(O/'detail.json',rows);write(O/'receipt.json',{'verdict':'EXACT_REFERENCE_CAUSE_DIAGNOSTIC_ONLY','R130_model_sha256':sha(base/'model.pkl'),'rows':len(rows),'delta_WKB_sha256':P.digest(delta),'delta_area_mm2':delta.area,'detail_sha256':sha(O/'detail.json'),'reference_loss_waiver':False,'board_written':False,'native_jobs':0});print('R135',sha(O/'receipt.json'),json.dumps([{'uid':q['track']['uuid'],'a':q['track']['a'],'b':q['track']['b'],'causes':q['new_via_cause_rows']} for q in rows]),flush=True)
if __name__=='__main__':main()
