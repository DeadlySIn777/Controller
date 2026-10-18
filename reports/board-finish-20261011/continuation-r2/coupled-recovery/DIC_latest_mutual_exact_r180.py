"""Independent frozen latest-head discrete/positive mutual screen only.

Never overlays a whole saved model onto current. Source/contact/current and
native full composition remain the integrator's separate mandatory gates.
"""
import json,pickle,gc
from pathlib import Path
import audit_aux_exact_raw as A
import contact_layout as L
import fast_contacts as F
import guarded_power_projection_r44 as Z
import restore_SAFE_generated_precision_states_r168 as PS
from shapely import from_wkb
from shapely.geometry import Point,LineString
H=Path(__file__).resolve().parent;C=A.C
PROFILE=('net','layer','clearance_mm','min_thickness_mm','pad_connect_mode','priority','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')

def audit(nt,nv,removed,domains):
 rows=[];errors=[];pins={};profile_open=[]
 models=[('R214_ACTUAL_JOINT',H.parent/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl','87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e')]
 for label,path,pin in models:
  raw=A.read(path);assert C.sha(raw)==pin;g,h,b,q,after=pickle.loads(raw);pins[str(path)]=pin;items={v['uuid']:v for key in('tracks','vias','pads') for v in h[key]};assert set(removed)<={t['uuid'] for t in h['tracks']};hh={**h,'tracks':[t for t in h['tracks'] if t['uuid'] not in removed],'zones':[]};rec,trees=F.build(hh)
  for item in nv+nt:
   via='d' in item;net=L.norm(item['net']);body=Z.bounded_disk(item,item['d']/2) if via else A.shape({'kind':'segment',**item});layers=('F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu') if via else(item['layer'],);near=[]
   for layer in layers:
    for i in trees[layer].query(body.buffer(.9),predicate='intersects'):
     old=rec[layer][int(i)];other=L.norm(old['net'])
     if net==other:continue
     req=(.15 if domains.get(net)==domains.get(other) else .6)+.025;d=body.distance(old['shape']);entry={'head':label,'new_UUID':item['uuid'],'layer':layer,'old_kind':old['kind'],'old_UUID':old['uuid'],'old_raw_net':old['net'],'exact_distance_mm':d,'guarded_required_mm':req};near.append(entry)
     if d<req-1e-8:errors.append({'kind':'latest_discrete_Cu',**entry})
   if via:
    p=Point(item['x'],item['y']);hole=Z.bounded_disk(item,item['drill']/2);smdnear=[];hole_near=[];pitch=[]
    for pad in h['pads']:
     for layer,polys in pad['layers'].items():
      if pad['smd'] and layer in('F.Cu','B.Cu'):
       smdnear.extend((hole.distance(sh)-.005,pad['uuid'],pad['ref'],pad['num']) for sh in L.poly(polys) if sh.distance(p)<2)
     hole_near.extend((hole.distance(sh)-.005,pad['uuid']) for sh in L.poly(pad.get('hole') or []) if sh.distance(p)<2)
    for v in h['vias']:
     distance=p.distance(Point(v['x'],v['y']))
     if distance>2:continue
     pitch.append((distance,v['uuid']));hole_near.append((hole.distance(Z.bounded_disk(v,v['drill']/2))-.005,v['uuid']))
    if smdnear and min(smdnear)[0]<.275:errors.append({'kind':'latest_SMD_aperture','head':label,'new_UUID':item['uuid'],'minimum':min(smdnear)})
    if hole_near and min(hole_near)[0]<.275:errors.append({'kind':'latest_every_hole_aperture','head':label,'new_UUID':item['uuid'],'minimum':min(hole_near)})
    if pitch and min(pitch)[0]<.815:errors.append({'kind':'latest_ordinary_pitch','head':label,'new_UUID':item['uuid'],'minimum':min(pitch)})
   rows.append({'head':label,'new_UUID':item['uuid'],'local_foreign_Cu_records':near})
  # Every actual canonical profile is read directly. Do not substitute another
  # net/layer's fallback (notably C10036 .25/125 versus main FBG .15/124).
  for z in q:
   assert all(k in z for k in('net','layer','clearance_mm')),('missing hard-only electrical geometry settings',label,z['uuid']);missing=[k for k in PROFILE if k not in z]
   if missing:profile_open.append({'head':label,'UUID':z['uuid'],'missing_native_profile_fields':missing,'use':'UNQUALIFIED_HARD_GEOMETRY_RESERVATION_ONLY_NO_PROFILE_FALLBACK'})
   other=L.norm(z['net'])
   for item in nv+nt:
    via='d' in item
    if not via and item['layer']!=z['layer']:continue
    net=L.norm(item['net']);body=Z.bounded_disk(item,item['d']/2) if via else A.shape({'kind':'segment',**item});gap=.15 if domains.get(net)==domains.get(other) else .6;req=max(float(z['clearance_mm']),gap)+.025;radius=item['drill']/2 if via and net==other else (max(item['drill']/2+.275,item['d']/2+req) if via else item['w']/2+req);cut=Z.bounded_disk(item,radius) if via else Z.bounded_buffer(LineString([item['a'],item['b']]),radius)
    for role in('shape','zone_outline_shape'):
     shape=z[role]
     if shape.distance(body)>1:continue
     d=body.distance(shape);intersection=cut.intersection(shape);entry={'head':label,'new_UUID':item['uuid'],'canonical_UUID':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'role':role,'role_WKB_sha256':C.sha(shape.wkb),'direct_settings_only':{k:z[k] for k in PROFILE if k in z},'native_profile_missing_fields_explicit_OPEN':missing,'foreign_body_gap_mm':d,'guarded_required_mm':req,'prospective_cut_intersection_mm2':intersection.area,'prospective_cut_WKB_sha256':C.sha(cut.wkb)};rows.append(entry)
     if net!=other and d<req-1e-8:errors.append({'kind':'latest_canonical_Cu',**entry})
     if not intersection.is_empty:errors.append({'kind':'latest_canonical_cut_contact_projection_required',**entry})
  del raw,g,h,b,q,after,rec,trees,hh,items;gc.collect()
 # R201 is applied only as its exact one-In3 successor authority. All4 drills,
 # conservative six annuli and outward plane cuts are screened independently.
 p=H.parent/'sbc-power/IO3-wider-minimal-validated-integration-packet-r201/receipt.json';r=json.loads(A.read(p));assert C.sha(A.read(p))=='cee3eacedd73ba63788decafd0a3b169afee6a0fbfa76f76e5acc60e8cc83e2d';rb=A.read(r['replacement_objects_file']);assert C.sha(rb)=='ff59c9d7f91230a57ea11f1c4b98832cf3eb2601306f57ed8da6086e8f89282d';packet=pickle.loads(rb);raw=A.read(r['frozen_full_model_file']);assert C.sha(raw)=='bf5603eebd87b3c5c197b8ae1266c0c0e780c3628dc65adbaa6b7f94f31721af';g,h,b,q,after=pickle.loads(raw);precision=PS.restore_bound_generated_precision_states(b,q);z=next(z for z in q if z['uuid']==packet[0]['uuid']);assert len(packet)==1 and all(packet[0][k]==z[k] for k in PROFILE) and all(packet[0][role].wkb==z[role].wkb for role in('shape','zone_outline_shape'))
 for v in nv+[t for t in nt if t['layer']==z['layer']]:
  via='d' in v
  for role in('shape','zone_outline_shape'):
   body=Z.bounded_disk(v,v['d']/2) if via else A.shape({'kind':'segment',**v});hole=Z.bounded_disk(v,v['drill']/2) if via else Point();radius=.425 if via else v['w']/2+.175;cut=Z.bounded_disk(v,radius) if via else Z.bounded_buffer(LineString([v['a'],v['b']]),radius);entry={'head':'R201_exact_one_In3','new_UUID':v['uuid'],'canonical_UUID':z['uuid'],'role':role,'exact_WKB_sha256':C.sha(z[role].wkb),'body_distance_mm':body.distance(z[role]),'guarded_required_mm':.175,'drill_intersection_mm2':hole.intersection(z[role]).area,'outward_antipad_or_track_cut_radius_mm':radius,'outward_antipad_intersection_mm2':cut.intersection(z[role]).area};rows.append(entry)
   if entry['body_distance_mm']<.175 or entry['drill_intersection_mm2']>0 or entry['outward_antipad_intersection_mm2']>0:errors.append({'kind':'R201_actual_canonical',**entry})
 cp=H.parent/'sbc-power/C1022-validated-native-integration-packet-r222/receipt.json';cr=json.loads(A.read(cp));assert C.sha(A.read(cp))=='ab63866ae63e1aff6da41f96630346989bdc4d92e9eb2feee499173b37f3ab02';assert cr['positive_R214_parent_sha256']==models[0][2] and not(cr['delete_rows'] or cr['footprint_replacement_rows'] or cr['owned_new_zone_replacement_rows']);assert len(cr['add_rows'])==1;tr=cr['add_rows'][0];ch=A.read(tr['chunk_path']);assert C.sha(ch)==tr['chunk_sha256']=='63d51b2d46a4c94f886f22cff7e9cd86dbf841a4b26a83437be88e76718f9b2d';actual=A.G.parse(tr['uuid'],ch,{});assert actual['kind']=='segment' and actual['net']=='/IO_3V3' and actual['layer']=='B.Cu' and actual['w']==.3 and actual['a']==[157.29,92.427] and actual['b']==[158.5821,91.6881];rb=A.read(cr['exact_full_reference_body_file']);assert C.sha(rb)==cr['exact_full_reference_body_sha256']=='c01be256377bb7d06f54d9361b0ac644b366bd52a5528c8d7e62ef48ce4b515d';held=from_wkb(rb);peerrows=[]
 for item in nv+nt:
  via='d' in item;net=L.norm(item['net'])
  if not via and item['layer']!='B.Cu':continue
  body=Z.bounded_disk(item,item['d']/2) if via else A.shape({'kind':'segment',**item});req=(.15 if domains.get(net)==domains['/IO_3V3'] else .6)+.025;entry={'held_peer_UUID':tr['uuid'],'held_chunk_sha256':C.sha(ch),'held_reference_body_sha256':C.sha(rb),'new_UUID':item['uuid'],'same_B_actual_Cu_distance_mm':body.distance(held),'guarded_required_mm':req};peerrows.append(entry)
  if entry['same_B_actual_Cu_distance_mm']<req-1e-8:errors.append({'kind':'held_C1022_actual_B_Cu',**entry})
 for v in nv:
  radius=v['drill']/2 if L.norm(v['net'])=='/LOGIC_GND' else v['d']/2+.25+.025;cut=Z.bounded_disk(v,radius);area=cut.intersection(held).area;entry={'held_peer_UUID':tr['uuid'],'new_UUID':v['uuid'],'source_reference_layer':'In4.Cu','actual_GND_reference_cut_radius_mm':radius,'held_full_body_reference_intersection_mm2':area};peerrows.append(entry)
  if area>0:errors.append({'kind':'held_C1022_old_full_body_reference_cut',**entry})
 return {'verdict':'EXACT_LATEST_FROZEN_DISCRETE_POSITIVE_IO3_MUTUAL_PASS_COMBINED_CONTACT_SOURCE_CURRENT_NATIVE_OPEN' if not errors else'EXACT_LATEST_MUTUAL_INCOMPLETE','rows':rows,'errors':errors,'frozen_model_pins':pins,'unqualified_hard_only_native_profiles_explicit_OPEN':profile_open,'R201_receipt_sha256':C.sha(A.read(p)),'R201_lossless_bound_precision_restorations':precision,'held_C1022_R222_receipt_sha256':C.sha(A.read(cp)),'held_C1022_R222_actual_Cu_and_full_body_reference_rows':peerrows,'full_latest_composition_all77_contacts_source_refs_current_native':'OPEN'}
