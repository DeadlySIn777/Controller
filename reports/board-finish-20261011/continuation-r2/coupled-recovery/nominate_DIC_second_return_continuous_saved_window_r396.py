"""Full continuous saved stitch window, source-bound physical masks, no grid."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'construct_Q0_four_wall_two_port_route_r350.py';s=base.read_text().split('def req(a,bb):')[0].replace('Q0-four-wall-two-port-route-constructor-r350','DIC-second-return-continuous-saved-window-r396');exec(compile(s,str(base),'exec'))
LG='/LOGIC_GND';sig=next(v for v in h['vias']if v['uuid'].startswith('55ab5777'));old=next(v for v in h['vias']if v['uuid'].startswith('9ef5dbc8'));removed={v['uuid']for v in h['vias']if v['uuid'].startswith(('99cc6bf8','9ef5dbc8','0330815c'))};roi=Point(sig['x'],sig['y']).buffer(1.2,quad_segs=128).envelope;roiMargin=roi.buffer(2);ring=Point(sig['x'],sig['y']).buffer(.997,quad_segs=256).difference(Point(sig['x'],sig['y']).buffer(.903,quad_segs=256));obs=[];ledger=[]
def req(a,bb):return .15 if dom.get(K.L.norm(a))==dom.get(K.L.norm(bb))else .6
for layer in K.LAYERS:
 for j in trees[layer].query(roiMargin,predicate='intersects'):
  r=discrete[layer][int(j)]
  if r['uuid']in removed or K.L.norm(r['net'])==LG:continue
  rad=.25+req(LG,r['net'])+.030;obstacle=K.Z.bounded_buffer(r['shape'].intersection(roiMargin),rad);obs.append(obstacle);ledger.append({'kind':'foreign_'+r['kind'],'uuid':r['uuid'],'layer':layer,'net':r['net'],'cutter_WKB_sha256':K.C.sha(obstacle.wkb),'rad_after_foreign_body_mm':rad})
 for z in q:
  if z['layer']!=layer or K.L.norm(z['net'])==LG or z['shape'].distance(roi)>2:continue
  rad=.25+max(float(z['clearance_mm']),req(LG,z['net']))+.030;assert rad<2;cut=K.Z.bounded_buffer(z['shape'].intersection(roiMargin),rad);obs.append(cut);ledger.append({'kind':'current_foreign_owned_plane_hard','uuid':z['uuid'],'layer':layer,'net':z['net'],'cutter_WKB_sha256':K.C.sha(cut.wkb)})
for u,n,hole in holes:
 if u in removed or hole.distance(roi)>2:continue
 obs.append(K.Z.bounded_buffer(hole,.1+.280))
for v in h['vias']:
 if v['uuid']in removed:continue
 p=Point(v['x'],v['y'])
 if p.distance(roi)<1:obs.append(K.Z.bounded_disk(v,.815))
for p in h['pads']:
 if not p['smd']:continue
 for layer,rs in p['layers'].items():
  if layer not in('F.Cu','B.Cu'):continue
  for body in K.L.poly(rs):
   if body.distance(roi)<1:obs.append(K.Z.bounded_buffer(body,.1+.280))
for r in h['rule_areas']:
 if r.get('no_vias'):obs.extend(K.Z.bounded_buffer(sh,.275)for sh in K.L.poly(r['outline'])if sh.distance(roi)<1)
for r in reserve['keepouts']:
 if LG not in exempt.get(r['name'],set()):obs.extend(K.Z.bounded_buffer(sh,.275)for sh in K.L.poly(r['outline'])if sh.distance(roi)<1)
sourceRoot=K.root(groups[LG],'J11001','2');sourceRefs={p:unary_union([r['shape']for r in sourceRoot if r['kind']=='fill'and r['layer']==p]).intersection(roiMargin)for p in('In1.Cu','In4.Cu')};OUT={'F.Cu':'In1.Cu','In2.Cu':'In1.Cu','B.Cu':'In4.Cu','In3.Cu':'In4.Cu'};refObstacles=[]
for outer,plane in OUT.items():
 for j in trees[outer].query(roiMargin,predicate='intersects'):
  r=discrete[outer][int(j)]
  if r['kind']!='track'or K.L.norm(r['net'])==LG or dom.get(K.L.norm(r['net']))!=dom[LG]:continue
  prior=r['shape'].intersection(sourceRefs[plane])
  if prior.is_empty:continue
  cut=K.Z.bounded_buffer(prior,.1+.001);refObstacles.append(cut)
physical=ring.difference(unary_union(obs));final=physical.difference(unary_union(refObstacles));(out/'saved-entire-window-physical-legal-centres.wkb').write_bytes(physical.wkb);(out/'saved-entire-window-strict-old-reference-legal-centres.wkb').write_bytes(final.wkb);rows=[];selected=None
for part in sorted(K.RF.parts(final),key=lambda sh:sh.distance(Point(old['x'],old['y']))):
 for p in [part.representative_point(),part.centroid]:
  at=[round(p.x,6),round(p.y,6)];p=Point(at)
  if not final.covers(p):continue
  ann=p.buffer(.25,quad_segs=128).difference(p.buffer(.1,quad_segs=128));witness={l:ann.buffer(-.025,quad_segs=128).intersection(ref).area for l,ref in sourceRefs.items()};row={'xy_mm':at,'distance_to_signal_mm':p.distance(Point(sig['x'],sig['y'])),'distance_from_old_return_mm':p.distance(Point(old['x'],old['y'])),'actual_before_J1_source_finite_annular_interior_mm2':witness,'actual_SOURCE_annular_nomination_pass':all(a>.005 for a in witness.values())};rows.append(row)
  if row['actual_SOURCE_annular_nomination_pass']:selected=row;break
 if selected:break
put(out/'continuous-mask-native-object-ledger.json',ledger);put(out/'continuous-mask-site-nominations.json',rows);report={'verdict':'DIC_SECOND_RETURN_CONTINUOUS_PHYSICAL_SOURCE_NOMINATION_ONLY','input_model_file':str(model),'input_model_sha256':sha(model),'operator_file':str(operator),'operator_sha256':sha(operator),'actual_drilled_source_groups_sha256':sha(groupsfile),'signal_UUID':sig['uuid'],'signal_xy_mm':[sig['x'],sig['y']],'old_return_UUID':old['uuid'],'old_return_xy_mm':[old['x'],old['y']],'window_mm':[.903,.997],'continuous_physical_legal_area_mm2':physical.area,'continuous_physical_legal_nonempty':not physical.is_empty,'continuous_strict_retained_source_reference_legal_area_mm2':final.area,'continuous_strict_retained_source_reference_legal_nonempty':not final.is_empty,'selected':selected,'no_finite_grid_negative_claim':True,'all_signal_and_native_source_items_unchanged':True,'full_after_holes_source_contact_reference_native_current_SI':'OPEN','all_R155_R368_R7_CORE_ROOT42_and_old_designated_pair_raw_FAILURES_preserved':True,'native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',report);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**report}),flush=True)
