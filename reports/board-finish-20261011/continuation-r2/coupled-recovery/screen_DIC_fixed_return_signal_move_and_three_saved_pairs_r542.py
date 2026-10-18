"""Screen only saved three DIC pair corrections/incident two NEW tracks.

Use exact current projected source references for strict retained-neighbor
cuts. Raw source-body gaps and unqualified own/stale apertures stay OPEN.
No aliases, native job, model edit, cache reclaim or disk waiver is made.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'nominate_DIC_fixed_return_minimal_signal_port_move_r540.py'
code=base.read_text().replace('DIC-fixed-return-minimal-signal-port-move-r540','DIC-fixed-return-signal-and-three-saved-pair-screen-r542')
needle="sites.sort(key=lambda r:(r['signal_move_mm'],r['new_signal_xy_mm']));"
assert code.count(needle)==1
addition="""bf=H/'Q0-R526-full-current-contacts-source-reference-r528/actual-before-and-after-source-banks.pkl';assert sha(bf)=='9b48079a0eb2b1a592dca1fc195ffe70b350e9ff9a110f069178a9f207db0a17';banks=pickle.loads(bf.read_bytes());lgroot=banks['after'][GND];sourceRefs={l:unary_union([r['shape']for r in lgroot if r['kind']=='fill'and r['layer']==l])for l in('In1.Cu','In4.Cu')};cz={z['uuid']:z for z in current['zones']};rp=H/'DIC-three-return-saved-window-correction-r366/selected-minimal-ground-return-relocations.json';returns=json.loads(rp.read_bytes());assert len(returns)==2;movingGround={r['old_return_UUID']:r['new_xy_mm']for r in returns};oldVia={v['uuid']:v for v in h['vias']};outmap={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','B.Cu':'In4.Cu','In3.Cu':'In4.Cu'};screened=[];positive=[];ignored=withheld|set(movingGround)
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
"""
code=code.replace(needle,addition+needle)
code=code.replace("'physical_nominee_count':len(sites)","'physical_nominee_count':len(sites),'endpoint_strict_reference_screened_count':len(screened),'strict_endpoint_current_reference_positive_count':len(positive),'actual_current_J1_source_array_sha256':sha(bf),'two_saved_other_return_moves_bound':movingGround")
derived=H/'DIC-fixed-return-signal-and-three-saved-pair-screen-r542-derived-screen.py';assert not derived.exists();derived.write_text(code)
exec(compile(code,str(derived),'exec'))
