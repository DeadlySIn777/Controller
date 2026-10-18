"""Minimal NEW SIG55ab move into .90-1.0 from fixed real return9ef.

Only the unaccepted signal barrel and its incident new track endpoints are
withdrawn for physical nomination. All native/other current Cu stays hard.
No copper/model/native mutation, cache reclaim or reference credit occurs.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time,math
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely.strtree import STRtree
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
out=H/'DIC-fixed-return-minimal-signal-port-move-r540';assert not out.exists();out.mkdir();start=time.monotonic();mp=H/'Q0-only-new-FA-recess-explicit-100nm-margin-r526/model.pkl';assert sha(mp)=='97e6f5193c9102102ec86a50c7d142def2d9c498495c8acdbd7202f466f84e14';g,h,b,q,current=pickle.loads(mp.read_bytes());sig=next(v for v in h['vias']if v['uuid']=='55ab5777-4032-59ab-94d1-d5a4478c7a72');ret=next(v for v in h['vias']if v['uuid']=='9ef5dbc8-049b-5a46-b319-e13870c3e4c4');NET=K.L.norm(sig['net']);GND='/LOGIC_GND';assert K.L.norm(ret['net'])==GND;assert(sig['x'],sig['y'],sig['d'],sig['drill'])==(130.782294,90.235607,.5,.2);assert(ret['x'],ret['y'])==(130.951774,91.046517);oldpt=Point(sig['x'],sig['y']);centre=Point(ret['x'],ret['y']);incident=[t for t in h['tracks']if K.L.norm(t['net'])==NET and any(math.dist(xy,[sig['x'],sig['y']])<1e-10 for xy in(t['a'],t['b']))];assert len(incident)==2 and {t['layer']for t in incident}=={'F.Cu','In2.Cu'};withheld={sig['uuid']}|{t['uuid']for t in incident};source=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';iv=K.C.inventory(source.read_bytes());assert withheld.isdisjoint(iv[3]);window=box(ret['x']-1.15,ret['y']-1.15,ret['x']+1.15,ret['y']+1.15);ring=K.Z.bounded_disk(ret,1.0).difference(centre.buffer(.90,quad_segs=256));dom=h['domains_normalized'];req=lambda n:.15 if dom.get(K.L.norm(n))==dom[NET]else .6;records,trees=K.F.build({**h,'zones':[]});obstacles=[];rows=[]
for layer in K.LAYERS:
 for j in trees[layer].query(window.buffer(.9),predicate='intersects'):
  r=records[layer][int(j)]
  if r['uuid']in withheld or K.L.norm(r['net'])==NET:continue
  rad=.25+req(r['net'])+.025;mask=K.Z.bounded_buffer(r['shape'],rad);obstacles.append(mask);rows.append({'kind':'all6_exact_foreign_discrete_'+r['kind'],'UUID':r['uuid'],'raw_net':r['net'],'layer':layer,'expanded_by_signal_radius_plus_clearance_guard_mm':rad,'mask_WKB_sha256':K.C.sha(mask.wkb)})
 for z in q:
  if z['layer']!=layer or K.L.norm(z['net'])==NET or z['shape'].distance(window)>.9:continue
  rad=.25+max(float(z['clearance_mm']),req(z['net']))+.025;mask=K.Z.bounded_buffer(z['shape'],rad);obstacles.append(mask);rows.append({'kind':'all6_current_owned_role_hard','UUID':z['uuid'],'raw_net':z['net'],'layer':layer,'expanded_radius_mm':rad,'mask_WKB_sha256':K.C.sha(mask.wkb)})
for p in h['pads']:
 if p['smd']:
  for layer,rs in p['layers'].items():
   if layer not in('F.Cu','B.Cu'):continue
   for sh in K.L.poly(rs):
    if sh.distance(window)>.6:continue
    mask=K.Z.bounded_buffer(sh,.1+.280);obstacles.append(mask);rows.append({'kind':'ordinary_every_SMD_drill_aperture','UUID':p['uuid'],'ref':p['ref'],'pin':p['num'],'layer':layer,'mask_WKB_sha256':K.C.sha(mask.wkb)})
 for sh in K.L.poly(p.get('hole')or[]):
  if sh.distance(window)>.6:continue
  mask=K.Z.bounded_buffer(sh,.1+.280);obstacles.append(mask);rows.append({'kind':'ordinary_every_pad_drill','UUID':p['uuid'],'mask_WKB_sha256':K.C.sha(mask.wkb)})
for v in h['vias']:
 if v['uuid']==sig['uuid']or Point(v['x'],v['y']).distance(window)>1:continue
 mask=K.Z.bounded_disk(v,max(.815,v['drill']/2+.1+.280));obstacles.append(mask);rows.append({'kind':'ordinary_every_retained_via_pitch_and_drill','UUID':v['uuid'],'raw_net':v['net'],'mask_WKB_sha256':K.C.sha(mask.wkb)})
for r in h['rule_areas']:
 if r.get('no_vias'):
  for sh in K.L.poly(r['outline']):
   if sh.distance(window)>.6:continue
   mask=K.Z.bounded_buffer(sh,.275);obstacles.append(mask);rows.append({'kind':'native_no_vias','UUID':r['uuid'],'mask_WKB_sha256':K.C.sha(mask.wkb)})
reserve,exempt=K.A.reservations()
for r in reserve['keepouts']:
 if NET in exempt.get(r['name'],set()):continue
 for sh in K.L.poly(r['outline']):
  if sh.distance(window)>.6:continue
  mask=K.Z.bounded_buffer(sh,.275);obstacles.append(mask);rows.append({'kind':'original_saved_reserve','name':r['name'],'mask_WKB_sha256':K.C.sha(mask.wkb)})
free=ring.difference(unary_union(obstacles));(out/'full-fixed-return-saved-window-physical-signal-centres.wkb').write_bytes(free.wkb);put(out/'all6-original-current-hard-obstacle-ledger.json',rows);sites=[]
for part in K.RF.parts(free.buffer(-.002,quad_segs=128)):
 candidates=[part.representative_point(),nearest_points(oldpt,part)[1]]
 for radius in(.925,.95,.975):
  theta=math.atan2(sig['y']-ret['y'],sig['x']-ret['x'])
  for i in range(-96,97):candidates.append(Point(ret['x']+radius*math.cos(theta+i*math.pi/96),ret['y']+radius*math.sin(theta+i*math.pi/96)))
 for p in candidates:
  at=[round(c,6)for c in p.coords[0]];pp=Point(at);distance=pp.distance(centre)
  if not free.covers(pp)or not .90<=distance<=1:continue
  if any(x['new_signal_xy_mm']==at for x in sites):continue
  changed=[]
  for t in incident:
   a=[at if math.dist(xy,[sig['x'],sig['y']])<1e-10 else xy for xy in(t['a'],t['b'])];changed.append({**t,'a':a[0],'b':a[1],'width_and_raw_net_and_layer_preserved':True})
  sites.append({'signal_UUID':sig['uuid'],'old_signal_xy_mm':[sig['x'],sig['y']],'new_signal_xy_mm':at,'fixed_return_UUID':ret['uuid'],'fixed_return_xy_mm':[ret['x'],ret['y']],'new_saved_window_spacing_mm':distance,'signal_move_mm':pp.distance(oldpt),'only_two_incident_track_endpoint_nominees':changed,'physical_centre_nomination_only_full_segment_source_reference_old_contacts_and_native_OPEN':True})
sites.sort(key=lambda r:(r['signal_move_mm'],r['new_signal_xy_mm']));put(out/'minimal-fixed-return-signal-sites-and-two-endpoint-changes.json',sites[:40]);put(out/'exact-new-original-signal-port-and-two-withdrawable-track-definitions.json',{'signal':sig,'fixed_return':ret,'incident_new_only_tracks':incident,'none_in_original_native_source_inventory':True});result={'verdict':'MINIMAL_NEW_SIGNAL_PORT_FIXED_RETURN_PHYSICAL_POSITIVE_NOMINATION_ALL_ROUTE_REFERENCE_GATES_OPEN'if sites else'FIXED_RETURN_FULL_SAVED_WINDOW_PHYSICAL_SIGNAL_NOMINATION_INCOMPLETE','current_model_sha256':sha(mp),'native_original_parent_sha256':sha(source),'raw_signal_net':sig['net'],'only_NEW_signal_UUID':sig['uuid'],'fixed_return_UUID':ret['uuid'],'only_incident_NEW_track_UUIDs':[t['uuid']for t in incident],'continuous_full_saved_window_physical_legal_area_mm2':free.area,'continuous_full_saved_window_physical_empty':free.is_empty,'saved_spacing_mm':[.90,1.0],'physical_nominee_count':len(sites),'smallest_shift_nominee':sites[0]if sites else None,'all_original_Cu_and_OTHER_current_new_Cu_rules_profiles_holes_unchanged':True,'no_reference_cache_reclaim_disk_or_plane_by_name_credit':True,'all_actual_newbody_reference_pair_source_old_reference_contacts_native_current_SI':'OPEN','all_prior_raw_failures_preserved':True,'native_jobs':0,'board_or_model_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**result}),flush=True)
