"""Retained-trunk exact handoffs and contact-face blocker attribution.

Original actual SOURCE terminals and only-new CM terminals are reported
separately. A new CM annulus overlapping BEFORE source fill is conditional,
never represented as a native-attested SOURCE port or accepted repair.
"""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'screen_actual_R157_CM79_retained_CORE_ground_ports_r417.py').read_text(encoding='utf-8')
s=s.replace('CM79-actual-R157-retained-CORE-ground-port-census-r417','CM79-actual-R157-retained-CORE-named-ground-handoffs-r418')
a=s.index(' def screen(xy):');b=s.index(' # F transport',a)
s=s[:a]+s[b:]
a=s.index(' for uid,sh in holes:');b=s.index(' for rules,isreserve',a)
s=s[:a]+s[b:]
a=s.index(' routes=[];winner=None');b=s.index('\nif __name__',a)
tail=''' cmids={r['uuid']for kind in ('tracks','vias')for r in cm[kind]};sourceVias={r['uuid']for r in root if r['kind']=='via'and r['layer']=='F.Cu'};groundById={v['uuid']:v for v in actual['vias']};ports=[]
 for uid in sourceVias|{v['uuid']for v in cm['vias']if L.norm(v['net'])==NET}:
  v=groundById[uid];point=Point(v['x'],v['y'])
  if point.distance(Point(pad['x'],pad['y']))>8:continue
  ann=point.buffer(v['d']/2,quad_segs=128).difference(point.buffer(v['drill']/2,quad_segs=128));over={ly:ann.intersection(refPlanes[ly]).area for ly in refPlanes}
  if not all(x>0 for x in over.values()):continue
  if uid in sourceVias:
   ann=next(r['shape']for r in root if r['kind']=='via'and r['uuid']==uid and r['layer']=='F.Cu')
   bothActual=all(any(r['kind']=='via'and r['uuid']==uid and r['layer']==ly for r in root)for ly in refPlanes)
  else:bothActual=False
  ports.append({'via':v,'ann':ann,'source_class':'ORIGINAL_ACTUAL_NATIVE_SOURCE'if uid in sourceVias else'ONLY_NEW_CM_CONDITIONAL_BEFORE_SOURCE_ANNULUS','both_plane_actual_SOURCE_keys':bothActual,'actual_before_SOURCE_annulus_overlap_mm2':over})
 ports.sort(key=lambda p:math.dist([p['via']['x'],p['via']['y']],[pad['x'],pad['y']]))
 holeShapes={uid:sh.buffer(.380005,quad_segs=64)for uid,sh in holes if sh.intersects(roi)};allHoles=unary_union(list(holeShapes.values()));baseAllowed=unary_union([reference,padGuard]);baseFree=baseAllowed.buffer(-.100005,quad_segs=64).intersection(region).intersection(board).difference(hard).difference(allHoles);start=Point(pad['x'],pad['y']);startFaces=[p for p in RF.parts(baseFree)if p.covers(start)]
 blocker=[]
 nearby=start.buffer(1.5);faceBoundary=unary_union([f.boundary for f in startFaces]).buffer(.00001)if startFaces else start
 for r in rec['F.Cu']:
  if L.norm(r['net'])==NET or not r['shape'].intersects(nearby):continue
  obstacle=r['shape'].buffer(.1+max(gap(r['net']),float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15)+.025005,quad_segs=64);hit=obstacle.intersection(faceBoundary)
  if not hit.is_empty:blocker.append({'UUID':r['uuid'],'kind':r['kind'],'raw_net':r['net'],'only_new_CM':r['uuid']in cmids,'blocks_start_point':obstacle.covers(start),'contacts_original_start_face_boundary':True,'bounds_mm':list(r['shape'].bounds)})
 for i,f in enumerate(startFaces):(OUT/('CM79-F-start-axis-face-'+str(i)+'.wkb')).write_bytes(f.wkb)
 put('exact-CM79-retained-CORE-F-start-contact-face-and-blockers.json',{'actual_original_pad_UUID':pad['uuid'],'actual_original_pad_xy_mm':[pad['x'],pad['y']],'strict_SOURCE_reference_start_point_free':bool(startFaces),'start_face_count':len(startFaces),'start_faces_area_mm2':[f.area for f in startFaces],'nearest_local_true_foreign_body_boundary_blockers':blocker,'original_full_CORE_trunk_held':True})
 routes=[];winner=None
 for port in ports:
  v=port['via'];xy=[v['x'],v['y']];cap=Point(*xy).buffer(v['d']/2+.275,quad_segs=128);allowed=unary_union([reference,padGuard,cap]);otherHoles=unary_union([sh for uid,sh in holeShapes.items()if uid!=v['uuid']]);free=allowed.buffer(-.100005,quad_segs=64).intersection(region).intersection(board).difference(hard).difference(otherHoles);end=Point(*xy);startFs=[f for f in RF.parts(free)if f.covers(start)];targetFs=[f for f in RF.parts(free)if f.covers(end)];faces=[f for f in startFs if f.covers(end)];rr={'named_terminal_UUID':v['uuid'],'xy_mm':xy,'source_class':port['source_class'],'both_plane_actual_SOURCE_keys':port['both_plane_actual_SOURCE_keys'],'actual_before_SOURCE_annulus_overlap_mm2':port['actual_before_SOURCE_annulus_overlap_mm2'],'only_exact_own_terminal_guard_mm':v['d']/2+.275,'start_face_count':len(startFs),'target_face_count':len(targetFs),'common_face_count':len(faces),'route':None}
  for face in faces:
   path,method=TR.route(face,list(start.coords[0]),xy);path=[[round(x,6),round(y,6)]for x,y in path];body=unary_union([LineString([a,b]).buffer(.1,quad_segs=128)for a,b in zip(path,path[1:])]);missing=body.difference(allowed);annContact=body.intersection(port['ann']).area
   if not missing.is_empty or body.intersection(padCu).area<=0 or annContact<=0:continue
   rr.update({'route':path,'method':method,'fullbody_reference_gap_EMPTY':missing.is_empty,'actual_original_pad_contact_mm2':body.intersection(padCu).area,'finite_named_terminal_annulus_contact_mm2':annContact,'length_mm':sum(math.dist(a,b)for a,b in zip(path,path[1:]))});winner=rr;(OUT/'only-nominated-CM79-named-F-handoff-body.wkb').write_bytes(body.wkb);break
  routes.append(rr)
  if winner:break
 put('finite-named-existing-actual-or-conditional-CM-ground-handoffs.json',routes);put('only-CM79-retained-CORE-named-ground-handoff-nomination.json',winner)
 put('receipt.json',{'status':'ACTUAL_R157_CM79_RETAINED_CORE_NAMED_HANDOFF_AND_BLOCKER_SCREEN','actual_R157_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'R663_receipt_SHA256':sha(N.R663/'receipt.json'),'only49_CM_sparse_SHA256':sha(CMP),'CM79_original_pad_UUID':pad['uuid'],'CM79_original_pad_xy_mm':[pad['x'],pad['y']],'eligible_original_or_conditional_terminal_count':len(ports),'route_attempt_count':len(routes),'nomination_count':int(winner is not None),'original_full_CORE_trunk_all_old_Cu_holes_poses_native_rules_held':True,'no_unrelated_caps_no_newholes_no_NEW_CM_source_credit':True,'fresh_all_CM_source_oldref_native_current_thermal':'OPEN','native_jobs_or_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R418_COMPLETE',sha(OUT/'receipt.json'),len(ports),bool(winner),flush=True)
'''
s=s[:a]+tail+s[b:]
E=P/'exact-expanded-CM79-retained-CORE-named-handoffs-r418.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8')
exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
