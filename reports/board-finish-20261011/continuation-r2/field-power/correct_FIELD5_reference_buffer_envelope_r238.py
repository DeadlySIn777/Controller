"""Clip only the new FIELD5 outline against exact eligible current In4 references."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent
for n in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/n))
import regional_guarded_declared_projection_r140 as P
import contact_layout as C
import fast_contacts as F
import physical_reference_losses_r1 as REF
from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
from inventory import sha
O=H/'FIELD5-current-reference-envelope-correction-r238'
def write(path,data):path.write_text(json.dumps(data,indent=1)+'\n',encoding='utf-8')
def main():
 assert not O.exists();O.mkdir();base=H/'R54-native-wider-IO3-monitor-joint-audit-r214';nom=H/'FIELD5-actual-IO3-preserving-alternate-r225';g,h,b,z,bc=pickle.loads((base/'model.pkl').read_bytes());restore_bound_generated_precision_states(b,z);q=pickle.loads((nom/'proposed-zones.pkl').read_bytes())[0];assert q['uuid']=='61cb8179-7754-5031-bbea-0da464bf816f'
 for role in ('shape','zone_outline_shape'):raw=q[role].wkb;q[role]=set_precision(q[role],1e-6,mode='pointwise');assert raw==q[role].wkb
 original=copy.deepcopy(q);native_ids={t['uuid'] for t in g['tracks']};near=q['zone_outline_shape'].buffer(2);tracks=[t for t in h['tracks'] if t['uuid'] in native_ids and t['layer']=='B.Cu'];ledger=[];masks=[]
 for ground,ref,pin,gap in [('/motherboard_motors/FIELD_GND','J11003','2',.275),('/motherboard_do/FIELD_B_0V','J11005','2',.625),('/LOGIC_GND','J11001','2',.625)]:
  root=next(xs for xs in F.graph(bc,ground) if any(x['kind']=='pad' and(x['ref'],x['pin'])==(ref,pin) for x in xs));source=unary_union([x['shape'] for x in root if x['kind']=='fill' and x['layer']=='In4.Cu']);bodies=[];rows=[]
  for t in tracks:
   if C.norm(t['net'])==ground or h['domains_normalized'].get(C.norm(t['net']))!=h['domains_normalized'][ground]:continue
   body=REF.A.shape({'kind':'segment',**t})
   if not body.intersects(near):continue
   part=body.intersection(source)
   if part.area<=1e-12:continue
   bodies.append(part);rows.append({'old_track_UUID':t['uuid'],'raw_net':t['net'],'exact_old_source_reference_mm2':part.area,'part_sha256':P.digest(part)})
  mask=unary_union(bodies)
  if mask.is_empty:continue
  cut=P.bounded_buffer(mask,gap+.0001);changed=[]
  for role in ('shape','zone_outline_shape'):
   old=q[role];q[role]=set_precision(old.difference(cut),1e-6);changed.append({'role':role,'old_sha256':P.digest(old),'new_sha256':P.digest(q[role]),'removed_mm2':old.difference(q[role]).area,'added_mm2':q[role].difference(old).area})
  masks.append((gap,mask));name=ground.split('/')[-1];mf=O/(name+'.reference-mask.wkb');cf=O/(name+'.outward-cutter.wkb');mf.write_bytes(mask.wkb);cf.write_bytes(cut.wkb);ledger.append({'ground':ground,'required_guard_mm':gap,'constructor_reserve_mm':.0001,'exact_ref_rows':rows,'mask_file_sha256':sha(mf),'cutter_file_sha256':sha(cf),'changes':changed})
 proofs=[]
 for gap,mask in masks:
  area=P.bounded_buffer(q['shape'],gap).intersection(mask).area;proofs.append({'required_guard_mm':gap,'actual_direct_guarded_buffer_reference_intrusion_mm2':area});assert area<1e-12,proofs[-1]
 route=json.loads((nom/'receipt.json').read_text(encoding='utf-8'))['rows'][0]['source_bridge'];line=LineString(route['points_mm']);coretests=[{'width_mm':w,'physical_missing_core_area_mm2':line.buffer(w/2,quad_segs=64).difference(q['shape']).area} for w in (.35,.34,.30)];annuli=[]
 for v in h['vias']:
  if C.norm(v['net'])!=C.norm(q['net']) or 'In4.Cu' not in v['flashed']:continue
  ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128));overlap=ann.intersection(q['shape']).area
  if overlap>1e-9:annuli.append({'UUID':v['uuid'],'xy_mm':[v['x'],v['y']],'actual_old_In4_flash':True,'annular_overlap_mm2':overlap,'intended_outline_contains_center':q['zone_outline_shape'].contains(Point(v['x'],v['y']))})
 (O/'proposed-corrected-zone.pkl').write_bytes(pickle.dumps([q],protocol=5));write(O/'reference-clip-ledger.json',ledger);receipt={'verdict':'FIELD5_OWNED_REFERENCE_CLIP_NOMINEE_FULL_GATES_OPEN','baseline_sha256':sha(base/'model.pkl'),'nominee_receipt_sha256':sha(nom/'receipt.json'),'zone_UUID':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'required_guards_unchanged':True,'only_new_FIELD5_shape_and_intended_outline_changed':True,'total_removed_mm2':original['shape'].difference(q['shape']).area,'total_added_mm2':q['shape'].difference(original['shape']).area,'actual_guarded_buffer_reference_proofs':proofs,'core_capsule_tests':coretests,'actual_native_source_target_annular_overlaps':annuli,'zone_pickle_sha256':sha(O/'proposed-corrected-zone.pkl'),'ledger_sha256':sha(O/'reference-clip-ledger.json'),'full_source_contact_reference_geometry_current_native':'OPEN','native_jobs':0,'board_written':False};write(O/'receipt.json',receipt);print(json.dumps(receipt),flush=True);print('R238 complete',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
