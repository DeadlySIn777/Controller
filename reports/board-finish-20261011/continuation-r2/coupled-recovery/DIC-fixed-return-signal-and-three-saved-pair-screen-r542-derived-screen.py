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
out=H/'DIC-fixed-return-signal-and-three-saved-pair-screen-r542';assert not out.exists();out.mkdir();start=time.monotonic();mp=H/'Q0-only-new-FA-recess-explicit-100nm-margin-r526/model.pkl';assert sha(mp)=='97e6f5193c9102102ec86a50c7d142def2d9c498495c8acdbd7202f466f84e14';g,h,b,q,current=pickle.loads(mp.read_bytes());sig=next(v for v in h['vias']if v['uuid']=='55ab5777-4032-59ab-94d1-d5a4478c7a72');ret=next(v for v in h['vias']if v['uuid']=='9ef5dbc8-049b-5a46-b319-e13870c3e4c4');NET=K.L.norm(sig['net']);GND='/LOGIC_GND';assert K.L.norm(ret['net'])==GND;assert(sig['x'],sig['y'],sig['d'],sig['drill'])==(130.782294,90.235607,.5,.2);assert(ret['x'],ret['y'])==(130.951774,91.046517);oldpt=Point(sig['x'],sig['y']);centre=Point(ret['x'],ret['y']);incident=[t for t in h['tracks']if K.L.norm(t['net'])==NET and any(math.dist(xy,[sig['x'],sig['y']])<1e-10 for xy in(t['a'],t['b']))];assert len(incident)==2 and {t['layer']for t in incident}=={'F.Cu','In2.Cu'};withheld={sig['uuid']}|{t['uuid']for t in incident};source=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';iv=K.C.inventory(source.read_bytes());assert withheld.isdisjoint(iv[3]);window=box(ret['x']-1.15,ret['y']-1.15,ret['x']+1.15,ret['y']+1.15);ring=K.Z.bounded_disk(ret,1.0).difference(centre.buffer(.90,quad_segs=256));dom=h['domains_normalized'];req=lambda n:.15 if dom.get(K.L.norm(n))==dom[NET]else .6;records,trees=K.F.build({**h,'zones':[]});obstacles=[];rows=[]
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
bf=H/'Q0-R526-full-current-contacts-source-reference-r528/actual-before-and-after-source-banks.pkl';assert sha(bf)=='9b48079a0eb2b1a592dca1fc195ffe70b350e9ff9a110f069178a9f207db0a17';banks=pickle.loads(bf.read_bytes());lgroot=banks['after'][GND];sourceRefs={l:unary_union([r['shape']for r in lgroot if r['kind']=='fill'and r['layer']==l])for l in('In1.Cu','In4.Cu')};cz={z['uuid']:z for z in current['zones']};rp=H/'DIC-three-return-saved-window-correction-r366/selected-minimal-ground-return-relocations.json';returns=json.loads(rp.read_bytes());assert len(returns)==2;movingGround={r['old_return_UUID']:r['new_xy_mm']for r in returns};oldVia={v['uuid']:v for v in h['vias']};outmap={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','B.Cu':'In4.Cu','In3.Cu':'In4.Cu'};screened=[];positive=[];ignored=withheld|set(movingGround)
policyfile=Path(K.A.S.CONTROLLED);policy=json.loads(policyfile.read_bytes());exactpolicy=next((v for n,v in policy['nets'].items()if K.L.norm(n)==NET),None);assert exactpolicy is None or exactpolicy.get('class')in(None,'NONE'),'Saved unclassified route cannot bypass a controlled assignment'
for site in sites:
 xy=site['new_signal_xy_mm'];point=Point(xy);newtracks=site['only_two_incident_track_endpoint_nominees'];geom=[]
 for t in newtracks:
  axis=LineString([t['a'],t['b']]);body=K.A.shape({'kind':'segment',**t});layer=t['layer'];radius=t['w']/2
  for j in trees[layer].query(body.buffer(.9),predicate='intersects'):
   r=records[layer][int(j)]
   if r['uuid']in ignored or K.L.norm(r['net'])==NET:continue
   if r['kind']=='track'and not r['source'].get('m'):a=r['source'];d=axis.distance(LineString([a['a'],a['b']]))-radius-a['w']/2
   elif r['kind']=='via':a=r['source'];d=axis.distance(Point(a['x'],a['y']))-radius-(a['d']if layer in a['flashed']else a['drill'])/2
   else:d=axis.distance(r['shape'])-radius
   required=req(r['net'])+.025
   if d<required:geom.append({'kind':'true_new_endpoint_track_foreign_'+r['kind'],'new_UUID':t['uuid'],'other_UUID':r['uuid'],'layer':layer,'gap_mm':d,'required_mm':required})
  for z in q:
   if z['layer']!=layer or K.L.norm(z['net'])==NET or z['shape'].distance(body)>.9:continue
   d=axis.distance(z['shape'])-radius;required=max(float(z['clearance_mm']),req(z['net']))+.025
   if d<required:geom.append({'kind':'new_endpoint_track_current_owned_foreign_role','new_UUID':t['uuid'],'other_UUID':z['uuid'],'layer':layer,'gap_mm':d,'required_mm':required})
  for v in h['vias']:
   if v['uuid']in ignored or K.L.norm(v['net'])==NET:continue
   d=axis.distance(Point(v['x'],v['y']))-radius-v['drill']/2-.005
   if d<.275:geom.append({'kind':'new_endpoint_track_every_foreign_drill','new_UUID':t['uuid'],'other_UUID':v['uuid'],'layer':layer,'gap_mm':d,'required_mm':.275})
  for r in h['rule_areas']:
   if layer in r['layers']and r.get('no_tracks')and any(body.distance(s)<.025 for s in K.L.poly(r['outline'])):geom.append({'kind':'native_no_tracks','new_UUID':t['uuid'],'rule_UUID':r['uuid']})
  for r in reserve['keepouts']:
   if layer in r['layers']and NET not in exempt.get(r['name'],set())and any(body.distance(s)<.025 for s in K.L.poly(r['outline'])):geom.append({'kind':'frozen_reserve','new_UUID':t['uuid'],'name':r['name']})
 moved=[{**sig,'x':xy[0],'y':xy[1]}]+[{**oldVia[uid],'x':at[0],'y':at[1]}for uid,at in movingGround.items()];deltas={};afterRefs={}
 for layer in('In1.Cu','In4.Cu'):
  rr=[]
  for r in lgroot:
   if r['kind']!='fill'or r['layer']!=layer:continue
   z=cz[r['uuid']];cuts=[]
   for v in moved:
    rad=v['drill']/2 if K.L.norm(v['net'])==GND else max(v['drill']/2+.275,v['d']/2+max(float(z['clearance_mm']),.15)+.025)
    if Point(v['x'],v['y']).distance(r['shape'])<=rad:cuts.append(K.Z.bounded_disk(v,rad))
   if cuts:rr.append(r['shape'].intersection(unary_union(cuts)))
  delta=unary_union(rr);deltas[layer]=delta;afterRefs[layer]=sourceRefs[layer].difference(delta)
 losses=[]
 for outer,inner in outmap.items():
  delta=deltas[inner]
  if delta.is_empty:continue
  for j in trees[outer].query(delta.envelope,predicate='intersects'):
   r=records[outer][int(j)]
   if r['kind']!='track'or r['uuid']in withheld or K.L.norm(r['net'])==GND or dom.get(K.L.norm(r['net']))!=dom[GND]:continue
   loss=r['shape'].intersection(delta)
   if not loss.is_empty:losses.append({'UUID':r['uuid'],'raw_net':r['net'],'layer':outer,'original_native_UID':r['uuid']in iv[3],'raw_lost_actual_before_reference_mm2':loss.area,'raw_loss_WKB_sha256':K.C.sha(loss.wkb)})
 newref=[]
 for t in newtracks:
  body=K.A.shape({'kind':'segment',**t});plane='In1.Cu';raw=body.difference(afterRefs[plane]);outsideown=raw.difference(K.Z.bounded_disk(moved[0],.525));newref.append({'UUID':t['uuid'],'layer':t['layer'],'raw_actual_current_before_after_source_gap_mm2':raw.area,'raw_gap_empty':raw.is_empty,'gap_outside_exact_0p525_new_SIG_aperture_mm2':outsideown.area,'gap_outside_exact_aperture_empty':outsideown.is_empty,'source_supported_own_scope_and_old_unused_SIG_antipad_healing':'OPEN_NO_GENERIC_DISK_CREDIT'})
 annuli=[]
 for v in [ret]+moved[1:]:
  ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128));aa={l:ann.buffer(-.025,quad_segs=128).intersection(afterRefs[l]).area for l in afterRefs};annuli.append({'return_UUID':v['uuid'],'xy_mm':[v['x'],v['y']],'actual_current_source_annular_interior_mm2':aa,'source_annulus_nomination_pass':all(a>.005 for a in aa.values()),'fresh_drilled_global_source_graph_and_NATIVE_flash':'OPEN'})
 record={**site,'full_two_track_true_geometry_errors':geom,'strict_all_retained_current_native_AND_new_track_reference_losses':losses,'new_two_track_raw_current_reference_ledgers':newref,'all_three_real_return_after_nominal_new_hole_annular_witnesses':annuli,'current_controlled_map_file':str(policyfile),'current_controlled_map_sha256':sha(policyfile),'exact_saved_NET_controlled_assignment':exactpolicy,'strict_physical_endpoint_and_retained_reference_nomination_pass':not geom and not losses and all(a['source_annulus_nomination_pass']for a in annuli)};screened.append(record)
 if record['strict_physical_endpoint_and_retained_reference_nomination_pass']:positive.append(record)
put(out/'all-minimal-signal-site-two-track-pair-and-strict-retained-reference-screens.json',screened);put(out/'strict-positive-minimal-signal-and-three-return-nominations.json',positive);sites=positive
sites.sort(key=lambda r:(r['signal_move_mm'],r['new_signal_xy_mm']));put(out/'minimal-fixed-return-signal-sites-and-two-endpoint-changes.json',sites[:40]);put(out/'exact-new-original-signal-port-and-two-withdrawable-track-definitions.json',{'signal':sig,'fixed_return':ret,'incident_new_only_tracks':incident,'none_in_original_native_source_inventory':True});result={'verdict':'MINIMAL_NEW_SIGNAL_PORT_FIXED_RETURN_PHYSICAL_POSITIVE_NOMINATION_ALL_ROUTE_REFERENCE_GATES_OPEN'if sites else'FIXED_RETURN_FULL_SAVED_WINDOW_PHYSICAL_SIGNAL_NOMINATION_INCOMPLETE','current_model_sha256':sha(mp),'native_original_parent_sha256':sha(source),'raw_signal_net':sig['net'],'only_NEW_signal_UUID':sig['uuid'],'fixed_return_UUID':ret['uuid'],'only_incident_NEW_track_UUIDs':[t['uuid']for t in incident],'continuous_full_saved_window_physical_legal_area_mm2':free.area,'continuous_full_saved_window_physical_empty':free.is_empty,'saved_spacing_mm':[.90,1.0],'physical_nominee_count':len(sites),'endpoint_strict_reference_screened_count':len(screened),'strict_endpoint_current_reference_positive_count':len(positive),'actual_current_J1_source_array_sha256':sha(bf),'two_saved_other_return_moves_bound':movingGround,'smallest_shift_nominee':sites[0]if sites else None,'all_original_Cu_and_OTHER_current_new_Cu_rules_profiles_holes_unchanged':True,'no_reference_cache_reclaim_disk_or_plane_by_name_credit':True,'all_actual_newbody_reference_pair_source_old_reference_contacts_native_current_SI':'OPEN','all_prior_raw_failures_preserved':True,'native_jobs':0,'board_or_model_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**result}),flush=True)
