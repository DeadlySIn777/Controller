"""Freeze only exact new-primitive masks for current owned zone roles.

Original native outlines/filled records are never reconstructed or snapped.
This preflight reports literal gains; it does not waive or install them.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
out=H/'Q0-current-owned-role-antipad-masks-r486';assert not out.exists();out.mkdir();start=time.monotonic();mp=H/'Q0-exact-R476-ground-contact-pose-r478/model.pkl';assert sha(mp)=='aec47d8600135e340be9e38ca18891e2903e7c283ee0b7095673d383ce079ebd';g,h,b,q,current=pickle.loads(mp.read_bytes());pp=H/'Q0-R474-ground-contact-pose-native-r476/exact-owned-discrete-and-pose-nomination.pkl';assert sha(pp)=='b226073ec3597d7115d9216bb1a6ff3c1fd9904d25652cd3d518df216cd1a067';op=pickle.loads(pp.read_bytes());nt=op['tracks'];nv=op['vias'];extra=[{**v,'added_layer_only':'In2.Cu'}for v in op['existing_SENSE_vias']];dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(K.L.norm(a))==dom.get(K.L.norm(bb))else .6;operations=[];rows=[];modelq={z['uuid']:z for z in q};assert len(modelq)==len(q)
for z in q:
 uid=z['uuid'];net=K.L.norm(z['net']);layer=z['layer'];local=float(z['clearance_mm']);masks={'shape':[],'zone_outline_shape':[]};maskrows=[]
 for item in nt+nv+extra:
  via='d'in item;same=K.L.norm(item['net'])==net
  if 'added_layer_only'in item and layer!=item['added_layer_only']:continue
  if not via and(item['layer']!=layer or same):continue
  if via and same and'added_layer_only'in item:continue
  req=max(local,gap(item['net'],net))+.025;rad=item['drill']/2 if via and same else max(item['drill']/2+.275,item['d']/2+req)if via else item['w']/2+req;mask=K.Z.bounded_disk(item,rad)if via else K.Z.bounded_buffer(LineString([item['a'],item['b']]),rad)
  if mask.distance(z['shape'])>0 and mask.distance(z['zone_outline_shape'])>0:continue
  masks['shape'].append(mask)
  if not(via and same):masks['zone_outline_shape'].append(mask)
  maskrows.append({'UUID':item['uuid'],'net':item['net'],'radius_mm':rad,'kind':'existing_natural_NEW_In2_annulus'if'added_layer_only'in item else'new_via'if via else'new_track','physical_role_only_own_actual_drill':bool(via and same),'native_intent_own_barrel_center_never_removed':bool(via and same),'mask_WKB_sha256':K.C.sha(mask.wkb)})
 for pad in h['pads']:
  if pad['ref']!='R10016'or K.L.norm(pad['net'])==net or layer not in pad['layers']:continue
  shape=unary_union(K.L.poly(pad['layers'][layer]));mask=K.Z.bounded_buffer(shape,max(local,gap(pad['net'],net))+.025)
  if mask.distance(z['shape'])>0 and mask.distance(z['zone_outline_shape'])>0:continue
  masks['shape'].append(mask);masks['zone_outline_shape'].append(mask);maskrows.append({'UUID':pad['uuid'],'kind':'exact_new_SMD_pose','net':pad['net'],'mask_WKB_sha256':K.C.sha(mask.wkb)})
 for role,xs in masks.items():
  mask=unary_union(xs)
  if mask.is_empty or not mask.intersects(z[role]):continue
  before=set_precision(z[role],0);assert before.wkb==z[role].wkb;after=before.difference(mask);gain=after.difference(before);removed=before.difference(after)
  if removed.is_empty and gain.is_empty:continue
  stem=uid+'-'+role;(out/(stem+'-exact-new-primitive-mask.wkb')).write_bytes(mask.wkb);(out/(stem+'-raw-after-subtraction.wkb')).write_bytes(after.wkb)
  if not gain.is_empty:(out/(stem+'-raw-literal-gain.wkb')).write_bytes(gain.wkb)
  row={'UUID':uid,'net':z['net'],'layer':layer,'role':role,'exact_role_local_clearance_mm':local,'before_role_WKB_sha256':K.C.sha(before.wkb),'after_raw_role_WKB_sha256':K.C.sha(after.wkb),'mask_WKB_file':str(out/(stem+'-exact-new-primitive-mask.wkb')),'mask_WKB_sha256':K.C.sha(mask.wkb),'literal_gain_empty':gain.is_empty,'literal_gain_mm2':gain.area,'actual_removed_mm2':removed.area,'native_original_design_outline_unchanged':True,'integer_nm_new_boundary_and_current_filled_alignment':'OPEN','all_exact_mask_items':maskrows};rows.append(row);operations.append({'UUID':uid,'layer':layer,'role':role,'before_WKB_sha256':K.C.sha(z[role].wkb),'exact_negative_mask':mask,'raw_after':after,'all_raw_gain_failures_preserved':True})
opfile=out/'only-current-owned-roles-exact-negative-masks.pkl';opfile.write_bytes(pickle.dumps(operations,protocol=5));put(out/'every_owned_role_exact_new_primitive_subtraction_preflight.json',rows);result={'verdict':'CURRENT_OWNED_ROLE_NEW_PRIMITIVE_MASKS_FROZEN_LITERAL_GAINS_AND_CANONICAL_REPLAY_OPEN','current_model_sha256':sha(mp),'exact_discrete_packet_sha256':sha(pp),'exact_negative_role_packet_file':str(opfile),'exact_negative_role_packet_sha256':sha(opfile),'current_owned_zone_count':len(q),'actual_changed_role_count':len(rows),'raw_literal_gain_role_count':sum(not r['literal_gain_empty']for r in rows),'all_unaffected_current_q_WKB_profiles_original_native_outlines_and_filled_arrays_exact':True,'all_full_current_source_reference_contact_native_precision_and_fill_alignment_gates':'OPEN','native_jobs':0,'model_or_board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**result}),flush=True)
