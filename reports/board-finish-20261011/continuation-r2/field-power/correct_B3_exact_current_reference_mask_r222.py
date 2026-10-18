"""Subtract only new B3 copper that would erode exact current LOGIC references."""
import os
for n in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[n]='2'
import psutil
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,pickle,json,copy
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent
for n in ('sbc-power','coupled-recovery'):sys.path.insert(0,str(H.parent/n))
import regional_guarded_declared_projection_r140 as P
import fast_contacts as F
import contact_layout as C
import physical_reference_losses_r1 as REF
from restore_SAFE_generated_precision_states_r168 import restore_bound_generated_precision_states
from inventory import sha
O=H/'B3-exact-current-LOGIC-reference-correction-r222'

def main():
 assert not O.exists();O.mkdir();base=H/'R54-native-wider-IO3-monitor-joint-audit-r214';assert sha(base/'model.pkl')=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e'
 g,h,b,z,a=pickle.loads((base/'model.pkl').read_bytes());restore_bound_generated_precision_states(b,z);root=next(xs for xs in F.graph(a,'/LOGIC_GND') if any(q['kind']=='pad' and(q['ref'],q['pin'])==('J11001','2') for q in xs));ref=unary_union([q['shape'] for q in root if q['kind']=='fill' and q['layer']=='In1.Cu'])
 Q=H/'REG-rebuilt-B3-on-wider-IO3-full-audit-r212';allq=pickle.loads((Q/'new-owned-zones.pkl').read_bytes());q=next(q for q in allq if q['uuid']=='20d6742a-cc6b-5ada-8a37-f921f002007a')
 for role in ('shape','zone_outline_shape'):q[role]=set_precision(q[role],1e-6,mode='pointwise')
 old=copy.deepcopy(q);near=q['zone_outline_shape'].buffer(2.0);rows=[];bodies=[];original={t['uuid'] for t in g['tracks']}
 for t in h['tracks']:
  if t['layer']!='F.Cu' or t['uuid'] not in original:continue
  body=REF.A.shape({'kind':'segment',**t})
  if not body.intersects(near):continue
  prior=body.intersection(ref)
  if prior.area<=1e-12:continue
  bodies.append(prior);rows.append({'track_UUID':t['uuid'],'raw_net':t['net'],'exact_prior_source_reference_area_mm2':prior.area,'exact_reference_intersection_WKB_sha256':P.digest(prior)})
 mask=unary_union(bodies);cut=P.bounded_buffer(mask,.625+.00002);q['shape']=set_precision(q['shape'].difference(cut),1e-6);q['zone_outline_shape']=set_precision(q['zone_outline_shape'].difference(cut),1e-6)
 ledger=[]
 for role in ('shape','zone_outline_shape'):
  removed=old[role].difference(q[role]);added=q[role].difference(old[role]);f=O/(role+'.removed.wkb');f.write_bytes(removed.wkb);ledger.append({'role':role,'before_sha256':P.digest(old[role]),'after_sha256':P.digest(q[role]),'removed_area_mm2':removed.area,'added_area_mm2':added.area,'removed_file_sha256':sha(f)})
 (O/'exact-current-prior-reference-mask.wkb').write_bytes(mask.wkb);(O/'exact-outward-reference-cutter.wkb').write_bytes(cut.wkb);(O/'proposed-corrected-zone.pkl').write_bytes(pickle.dumps([q],protocol=5));(O/'old-reference-track-intersections.json').write_text(json.dumps(rows,indent=1)+'\n',encoding='utf-8')
 pts=json.loads((H/'B3-exact-cross-layer-pair-r206/cross-layer-receipt.json').read_text(encoding='utf-8'))
 # Physical component count/annuli are diagnostic; subsequent full graph determines source.
 comps=[q['shape']] if q['shape'].geom_type=='Polygon' else list(q['shape'].geoms);ann=[]
 dh=pickle.loads((Q/'proposed-discrete.pkl').read_bytes())
 for v in h['vias']+dh['vias']:
  if C.norm(v['net'])!=C.norm(q['net']):continue
  disk=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128);hole=Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128);ar=disk.difference(hole);hits=[{'component':i,'area_mm2':ar.intersection(p).area} for i,p in enumerate(comps) if ar.intersection(p).area>1e-9]
  if hits:ann.append({'via_UUID':v['uuid'],'at_mm':[v['x'],v['y']],'native_intended_contains_center':q['zone_outline_shape'].contains(Point(v['x'],v['y'])),'overlaps':hits})
 receipt={'verdict':'OWNED_B3_REFERENCE_CLIP_PROPOSAL_FULL_GATES_REQUIRED','parent_native_peer_model_sha256':sha(base/'model.pkl'),'exact_old_B3_Q_sha256':P.digest(old['shape']),'changed_UUID':q['uuid'],'changed_layer':q['layer'],'required_foreign_gap_with_guard_mm':.625,'extra_construction_reserve_mm':.00002,'reference_mask_file_sha256':sha(O/'exact-current-prior-reference-mask.wkb'),'cutter_sha256':sha(O/'exact-outward-reference-cutter.wkb'),'operation_ledger':ledger,'reference_track_count':len(rows),'physical_piece_count':len(comps),'actual_existing_and_new_annular_overlaps':ann,'corrected_zone_pickle_sha256':sha(O/'proposed-corrected-zone.pkl'),'no_original_native_copper_or_definitions_modified':True,'native_jobs':0,'board_written':False,'source_current_min_feature_contact_reference_native_gates':'OPEN'}
 (O/'receipt.json').write_text(json.dumps(receipt,indent=1)+'\n',encoding='utf-8');print(json.dumps(receipt),flush=True);print('R222 complete',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':main()
