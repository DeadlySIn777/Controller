"""Locate each non-own-cap reference gap without accepting or trimming it."""
import hashlib,json,pickle,sys
from pathlib import Path
from shapely import from_wkb
from shapely.geometry import Point,LineString
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_declared_settings_projection_r58 as N
OUT=H/'U10003-R243-outside-exact-own-cap-reference-gap-attribution-r244';assert not OUT.exists();OUT.mkdir()
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
folder=H/'U10003-shared-return-two-source-seeded-new-FG-plane-explicit-source-bridge-nomination-r243';rp=folder/'receipt.json';assert sha(rp)=='2a2b2211a9c64fd80c2ec41fa7116913be01fc17c4867a9c656e4b6d83724e1b';r=json.loads(rp.read_bytes());packet=folder/'proposed-two-plane-and-joint-geometry.pkl';assert sha(packet)==r['packet_sha256'];d=pickle.loads(packet.read_bytes());joint=d['joint_geometry'];mp=H/'R10007-HOST-current-fresh-native-pad-authority-r238/model.pkl';g,h,b,q,full=pickle.loads(mp.read_bytes());shared=joint['new_shared_ground_via'];hard={**h,'tracks':[t for t in h['tracks']if t['uuid']not in joint['only_nine_unadopted_field_tracks_withdrawn']]+joint['new_tracks']+joint['exact_native_clock_track_restore'],'vias':[v for v in h['vias']if v['uuid']!=shared['uuid']]+[shared]};records,trees=K.F.build({**hard,'zones':[]});vby={v['uuid']:v for v in hard['vias']};caps=unary_union([N.bounded_disk(vby[u],rad)for u,rad in [('7f2431b3-4dcd-5b17-88ce-8aae4c3d66d4',.525),('2938cbdd-1d38-4238-9455-504b30f06e5e',.575),('1f45e002-4f40-4087-bbed-3be260272d8f',.375)]]);rows=[]
for z in d['replace_only_two_FG_zones']:
 layer=z['layer'];ref=from_wkb((H/'U10003-shared-return-two-source-seeded-new-FG-plane-source-seed-diagnosis-r241'/(layer+'-actual-J3-source-reference.wkb')).read_bytes()).union(z['shape'])
 for t in joint['new_tracks']+joint['exact_native_clock_track_restore']:
  body=K.A.shape({'kind':'segment',**t});gap=body.difference(ref).difference(caps)
  if gap.is_empty:continue
  wp=OUT/(layer+'-'+t['uuid']+'-raw-outside-own-caps.wkb');wp.write_bytes(gap.wkb);near=[]
  for j in trees[layer].query(gap.buffer(.8),predicate='intersects'):
   other=records[layer][int(j)]
   if K.L.norm(other['net'])=='/motherboard_motors/FIELD_GND':continue
   p1,p2=nearest_points(gap,other['shape']);near.append({'UUID':other['uuid'],'kind':other['kind'],'net':other['net'],'minimum_raw_gap_piece_to_actual_Cu_mm':gap.distance(other['shape']),'closest_gap_xy_mm':[p1.x,p1.y],'closest_actual_Cu_xy_mm':[p2.x,p2.y]})
  near.sort(key=lambda x:x['minimum_raw_gap_piece_to_actual_Cu_mm']);rows.append({'reference_layer':layer,'track_UUID':t['uuid'],'net':t['net'],'actual_track_layer':t['layer'],'raw_outside_own_caps_mm2':gap.area,'raw_bounds_mm':list(gap.bounds),'gap_WKB_sha256':sha(wp),'nearest_actual_foreign_reference_primitives':near[:8]})
result={'verdict':'R243_LITERAL_NONOWN_REFERENCE_FAIL_ATRIBUTED_NO_WAIVER','plane_packet_sha256':sha(packet),'model_sha256':sha(mp),'rows':rows,'native_jobs':0,'adopted':False,'manufacturing_ready':False};(OUT/'receipt.json').write_text(json.dumps(result,indent=1)+'\n');print('R244_OUTSIDE_OWN_CAPS',json.dumps(rows),sha(OUT/'receipt.json'),flush=True)
