"""Actual ordinary through-via ports outside frozen SBC corridor; no waiver."""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'construct_Q0_four_wall_two_port_route_r350.py'
prefix=base.read_text(encoding='utf-8').split('def req(a,bb):')[0].replace('Q0-four-wall-two-port-route-constructor-r350','Q0-real-rule-legal-port-nomination-r356')
exec(compile(prefix,str(base),'exec'))
def req(a,bb):return .15 if dom.get(K.L.norm(a))==dom.get(K.L.norm(bb))else .6
obs=[];ledger=[]
for layer in K.LAYERS:
 for j in trees[layer].query(window.buffer(2),predicate='intersects'):
  r=discrete[layer][int(j)]
  if r['uuid']in delete or r['uuid']in padids or K.L.norm(r['net'])==NET:continue
  obs.append(r['shape'].buffer(.25+req(NET,r['net'])+.030,quad_segs=128))
 for z in q:
  if z['layer']==layer and K.L.norm(z['net'])not in(NET,GND)and z['shape'].distance(window)<2:obs.append(z['shape'].buffer(.25+max(req(NET,z['net']),float(z['clearance_mm']))+.030,quad_segs=128))
 for z in current['zones']:
  if z.get('prospective_not_native')or K.L.norm(z['net'])==NET or dom.get(K.L.norm(z['net']))==dom.get(NET):continue
  for s in K.L.poly(z['fills'].get(layer,[])):
   if s.distance(window)<2:obs.append(s.buffer(.25+max(req(NET,z['net']),float(z['clearance_mm']))+.030,quad_segs=128))
for n,s in newsh.items():
 if K.L.norm(pads[n]['net'])!=NET:obs.append(s.buffer(.25+req(NET,pads[n]['net'])+.030,quad_segs=128))
for u,n,s in holes:
 if s.distance(window)<1:obs.append(s.buffer(.1+.280,quad_segs=128))
for v in h['vias']:
 pp=Point(v['x'],v['y'])
 if pp.distance(window)<1:obs.append(pp.buffer(.815,quad_segs=128))
for p in h['pads']:
 if not p['smd']or p['uuid']in padids:continue
 for layer,rs in p['layers'].items():
  if layer not in('F.Cu','B.Cu'):continue
  for s in K.L.poly(rs):
   if s.distance(window)<1:obs.append(s.buffer(.1+.280,quad_segs=128))
for s in newsh.values():obs.append(s.buffer(.1+.280,quad_segs=128))
for r in h['rule_areas']:
 if r.get('no_vias'):obs.extend(s.buffer(.275,quad_segs=128)for s in K.L.poly(r['outline']))
for r in reserve['keepouts']:
 if NET not in exempt.get(r['name'],set()):obs.extend(s.buffer(.275,quad_segs=128)for s in K.L.poly(r['outline']))
viaparts=window.difference(unary_union(obs));(out/'ordinary-all6-SMD-hole-pitch-rule-legal-centres.wkb').write_bytes(viaparts.wkb)
# Refuse generic source-by-name: return annuli must already lie in the actual
# J11003 physical source graph on BOTH actual used reference layers.
returnrows=[];eligible=[]
for v in h['vias']:
 if K.L.norm(v['net'])!=GND or Point(v['x'],v['y']).distance(window)>1.1:continue
 rr=[r for r in trueRoot if r['kind']=='via'and r['uuid']==v['uuid']];ann=Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128).difference(Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128));test={l:{'source_via_actual_layer':any(r['layer']==l for r in rr),'source_annular_interior_area_mm2':ann.buffer(-.025,quad_segs=128).intersection(oldrefs[l]).area}for l in oldrefs}
 if not all(z['source_via_actual_layer']and z['source_annular_interior_area_mm2']>.002 for z in test.values()):continue
 ring=Point(v['x'],v['y']).buffer(.997,quad_segs=128).difference(Point(v['x'],v['y']).buffer(.903,quad_segs=128));poly=ring.intersection(viaparts);returnrows.append({'return_UUID':v['uuid'],'return_xy_mm':[v['x'],v['y']],'qualified_before_actual_source_annuli':test,'rule_legal_window_area_mm2':poly.area});eligible.append((v,poly))
def ffree():
 obs=[]
 for j in trees['F.Cu'].query(window.buffer(1),predicate='intersects'):
  r=discrete['F.Cu'][int(j)]
  if r['uuid']in delete or r['uuid']in padids or K.L.norm(r['net'])==NET:continue
  obs.append(r['shape'].buffer(req(NET,r['net'])+.030,quad_segs=128))
 obs.append(newsh['2'].buffer(.180,quad_segs=128))
 for z in q:
  if z['layer']=='F.Cu'and K.L.norm(z['net'])not in(NET,GND)and z['shape'].distance(window)<1:obs.append(z['shape'].buffer(max(req(NET,z['net']),float(z['clearance_mm']))+.030,quad_segs=128))
 for u,n,s in holes:
  if n!=NET and s.distance(window)<1:obs.append(s.buffer(.280,quad_segs=128))
 for r in h['rule_areas']:
  if'F.Cu'in r['layers']and r.get('no_tracks'):obs.extend(s.buffer(.025,quad_segs=128)for s in K.L.poly(r['outline']))
 for r in reserve['keepouts']:
  if'F.Cu'in r['layers']and NET not in exempt.get(r['name'],set()):obs.extend(s.buffer(.025,quad_segs=128)for s in K.L.poly(r['outline']))
 return window.difference(unary_union(obs)).buffer(-.105,quad_segs=128).intersection(oldrefs['In1.Cu'].buffer(-.105,quad_segs=128))
fr=ffree();polys=K.RF.parts(fr);nominees={};fpga=signalF.buffer(-.04,quad_segs=128);target=newsh['1'].buffer(-.04,quad_segs=128)
for role,attach in [('source',fpga),('target',target)]:
 components=[(i,p)for i,p in enumerate(polys)if not p.intersection(attach).is_empty];rows=[]
 for v,pp in eligible:
  for ci,part in components:
   gg=pp.intersection(part)
   for piece in K.RF.parts(gg):
    # Three distinct interior choices per exact eligible fragment, all checked
    # against the exact buffered polygon after micrometre serialization.
    choices=[piece.representative_point(),piece.centroid,nearest_points(piece,attach)[0]]
    for point in choices:
     at=[round(point.x,6),round(point.y,6)];point=Point(at)
     if not gg.covers(point)or not oldrefs['In1.Cu'].covers(K.Z.bounded_disk({'x':at[0],'y':at[1]},.255)):continue
     a0=part.intersection(attach);aa=nearest_points(a0,point)[0];beg=[round(aa.x,6),round(aa.y,6)]
     if not part.covers(Point(beg)):continue
     path,search=T.route(part,tuple(beg),tuple(at));body=unary_union([K.A.shape({'kind':'segment','a':a,'b':bb,'w':.2})for a,bb in zip(path,path[1:])]);gap=body.difference(oldrefs['In1.Cu'])
     if not gap.is_empty:continue
     row={'role':role,'via_xy_mm':at,'existing_return_UUID':v['uuid'],'existing_return_xy_mm':[v['x'],v['y']],'spacing_mm':math.dist(at,[v['x'],v['y']]),'F_component':ci,'F_attachment_path_mm':[list(a)for a in path],'F_path_length_mm':LineString(path).length,'strict_before_actual_F_full_body_reference_gap_empty':True,'search':search,'all6_rule_legal_SMD_pitch_nomination':True,'actual_after_all_final_signal_holes_source_reference_contact_SI_current':'OPEN'}
     if not any(r['via_xy_mm']==at for r in rows):rows.append(row)
 nominees[role]=sorted(rows,key=lambda r:r['F_path_length_mm']);print('Q0_RULE_LEGAL_PORT_NOMINEES',role,len(rows),flush=True)
put(out/'actual-existing-ground-return-nominations.json',returnrows);put(out/'signal-source-target-port-path-nominations.json',nominees)
# Peer CM79 F-wall gap request on exact unadopted R289 CM49 packet.
cmfile=P/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/only-new-CM-ordinary-discrete-no-deletes.pkl';cm=pickle.loads(cmfile.read_bytes());axis=LineString([(116,202.715),(120,202.715)]);cmrows=[]
for t in cm.get('tracks',[])+cm.get('vias',[]):
 via='d'in t
 if not via and t['layer']!='F.Cu':continue
 gap=axis.distance(Point(t['x'],t['y'])if via else LineString([t['a'],t['b']]))-.625-(t['d']/2 if via else t['w']/2)
 if gap<.175:cmrows.append({'uuid':t['uuid'],'kind':'via'if via else'track','exact_proposed_geometry':t,'full_width_1p25_F_test_axis_mm':[[116,202.715],[120,202.715]],'true_analytic_gap_mm':gap,'native_required_mm':.15,'planning_required_mm':.175})
put(out/'CM49-own-new-blockers-of-F-power-test-segment.json',cmrows)
result={'verdict':'EXACT_RULE_LEGAL_Q0_PORT_NOMINATION_ONLY','model_sha256':sha(model),'source_sha256':sha(source),'operator_file':str(operator),'operator_sha256':sha(operator),'R368_actual_source_groups_sha256':sha(groupsfile),'eligible_existing_return_count':len(eligible),'source_port_count':len(nominees['source']),'target_port_count':len(nominees['target']),'CM49_F_packet_file':str(cmfile),'CM49_F_packet_sha256':sha(cmfile),'CM49_F_blocker_count':len(cmrows),'Q0_routing_options':'F/B/F or F/In2/F or F/In3/F max3legs; no reserved via exception; transport/body/after-hole source and neighbor proof OPEN','board_written':False,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**result}),flush=True)
