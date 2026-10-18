"""Minimal original CDONE move plus owned stubs; CORE and MIPI remain exact."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'exact-expanded-CM79-direct-DC-ground-r420.py').read_text(encoding='utf-8')
s=s.replace('CM79-actual-R157-direct-DC-ground-retained-CORE-r420','CM79-minimal-real-CDONE-move-ordinary-source-return-r425')
a=s.index(' routes=[];winner=None');b=s.index('\nif __name__',a)
tail=''' import uuid
 SIG='/fpga_core/FPGA_CDONE';uid='b1e550d5-047a-447c-a64c-45c2a92c14b0';original=next(v for v in actual['vias']if v['uuid']==uid);assert (original['x'],original['y'],original['d'],original['drill'])==(117.45,200.05,.6,.3);ownTracks={'b7dc346a-8a46-4b4c-ae3d-c5990ddefc96','490ef90c-4585-48f9-8331-37af95c295c8'};scope=P/'CM79-actual-CDONE-original-barrel-source-and-incident-scope-r422';scopeR=json.loads((scope/'receipt.json').read_bytes());assert sha(scope/'only-exact-original-CDONE-barrel-native-source-scope.pkl')==scopeR['scope_packet_SHA256'];sourceScope=pickle.loads((scope/'only-exact-original-CDONE-barrel-native-source-scope.pkl').read_bytes());producerR=json.loads((P/'CM79-CDONE-fresh-producer-and-actual-native-group-binding-r424/receipt.json').read_bytes());assert producerR['producer']['ref']=='U1001'and producerR['producer']['pin']=='R1';cmids={r['uuid']for kind in ('tracks','vias')for r in cm[kind]}
 returns=[]
 for v in actual['vias']:
  if L.norm(v['net'])!=NET or math.dist([v['x'],v['y']],[original['x'],original['y']])>1.5:continue
  p=Point(v['x'],v['y']);ann=p.buffer(v['d']/2,quad_segs=128).difference(p.buffer(v['drill']/2,quad_segs=128));over={ly:ann.intersection(refPlanes[ly]).area for ly in refPlanes}
  if all(x>0 for x in over.values()):returns.append({'via':v,'ann':ann,'before_actual_J1_source_plane_annulus_overlap_mm2':over,'native_SOURCE_before':v['uuid']not in cmids and all(any(r['kind']=='via'and r['uuid']==v['uuid']and r['layer']==ly for r in root)for ly in refPlanes)})
 def viaScreen(xy):
  point=Point(*xy);bad=[];operations=[];rawRefs=[]
  for ly in K.LAYERS:
   for j in trees[ly].query(point.buffer(1.4),predicate='intersects'):
    r=rec[ly][int(j)];n=L.norm(r['net'])
    if r['uuid']==uid or n==SIG:continue
    local=float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15;req=max(local,gap(n))+.025
    if r['kind']=='fill'and r['uuid']in nativeZones and domain.get(n)==domain.get(SIG):
     if point.distance(r['shape'])-.3<req:operations.append({'UUID':r['uuid'],'layer':ly,'net':r['net'],'actual_native_antipad_radius_mm':.3+local,'planner_guard_radius_mm':.3+req,'original_definition_outline_held':True})
     continue
    if point.distance(r['shape'])-.3<req:bad.append({'kind':'actual_foreign_Cu','UUID':r['uuid'],'layer':ly,'net':r['net']})
   for z in q:
    if z['layer']==ly and L.norm(z['net'])!=SIG and point.distance(z['shape'])-.3<max(gap(z['net']),float(z.get('clearance_mm',.15)))+.025:bad.append({'kind':'foreign_current_owned_role','UUID':z['uuid'],'layer':ly})
  for j in ht.query(point.buffer(.6),predicate='intersects'):
   u,sh=holes[int(j)]
   if u!=uid and point.distance(sh)-.15<.28:bad.append({'kind':'actual_other_drill','UUID':u})
  for j in st.query(point.buffer(.435),predicate='intersects'):
   u,sh=smds[int(j)]
   if point.distance(sh)-.15<.28:bad.append({'kind':'original_SMD_to_moved_drill','UUID':u})
  for j in vt.query(point.buffer(.82),predicate='intersects'):
   u=actual['vias'][int(j)]['uuid']
   if u!=uid and point.distance(vp[int(j)])<.815:bad.append({'kind':'ordinary_global_via_pitch','UUID':u})
  for rules,isreserve in [(h['rule_areas'],False),(reserve['keepouts'],True)]:
   for rule in rules:
    if(isreserve and SIG in exempt.get(rule['name'],set()))or(not isreserve and not rule.get('no_vias')):continue
    if any(point.distance(sh)<.325 for sh in L.poly(rule['outline'])):bad.append({'kind':'native_or_reserved_no_via','name':rule.get('name',rule.get('uuid'))})
  for ly in refPlanes:
   cut=point.buffer(.575,quad_segs=128)
   for j in mt[ly].query(cut,predicate='intersects'):
    r=masks[ly][int(j)];hit=cut.intersection(r['shape'])
    if hit.is_empty:continue
    sourceRec=next((rr for layer in ('F.Cu','In2.Cu','B.Cu','In3.Cu')for rr in rec[layer]if rr['uuid']==r['UUID']),None);n=L.norm(sourceRec['net'])if sourceRec else None;owned=r['UUID']in ownTracks|{uid};dcGround=n==NET;row={'UUID':r['UUID'],'layer':ly,'kind':r['kind'],'hit_mm2':hit.area,'owned_original_incident_terminal':owned,'DC_ground_shadow_only':dcGround};rawRefs.append(row)
    if not owned and not dcGround:bad.append({'kind':'held_nonLG_old_source_reference_mask','UUID':r['UUID'],'layer':ly,'hit_mm2':hit.area})
  return bad,operations,rawRefs
 def stubFree(layer):
  cuts=[]
  for r in rec[layer]:
   if r['uuid']==uid or L.norm(r['net'])==SIG or not r['shape'].intersects(roi):continue
   local=float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15;cuts.append(r['shape'].buffer(.1+max(local,gap(r['net']))+.025005,quad_segs=64))
  for z in q:
   if z['layer']==layer and L.norm(z['net'])!=SIG and z['shape'].intersects(roi):cuts.append(z['shape'].buffer(.1+max(gap(z['net']),float(z.get('clearance_mm',.15)))+.025005,quad_segs=64))
  for u,sh in holes:
   if u!=uid and sh.intersects(roi):cuts.append(sh.buffer(.380005,quad_segs=64))
  for rules,isreserve in [(h['rule_areas'],False),(reserve['keepouts'],True)]:
   for rule in rules:
    if layer not in rule['layers']or(isreserve and SIG in exempt.get(rule['name'],set()))or(not isreserve and not rule.get('no_tracks')):continue
    cuts.extend(sh.buffer(.125005,quad_segs=64)for sh in L.poly(rule['outline'])if sh.intersects(roi))
  return region.intersection(board).difference(unary_union(cuts))
 stubFreeSpace={ly:stubFree(ly)for ly in ('F.Cu','B.Cu')};groundFixed=[]
 for r in rec['F.Cu']:
  if r['uuid']==uid or L.norm(r['net'])==NET or not r['shape'].intersects(roi):continue
  local=float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15;groundFixed.append(r['shape'].buffer(.1+max(local,gap(r['net']))+.025005,quad_segs=64))
 for z in q:
  if z['layer']=='F.Cu'and L.norm(z['net'])!=NET and z['shape'].intersects(roi):groundFixed.append(z['shape'].buffer(.1+max(gap(z['net']),float(z.get('clearance_mm',.15)))+.025005,quad_segs=64))
 for rules,isreserve in [(h['rule_areas'],False),(reserve['keepouts'],True)]:
  for rule in rules:
   if 'F.Cu'not in rule['layers']or(isreserve and NET in exempt.get(rule['name'],set()))or(not isreserve and not rule.get('no_tracks')):continue
   groundFixed.extend(sh.buffer(.125005,quad_segs=64)for sh in L.poly(rule['outline'])if sh.intersects(roi))
 groundFixed=unary_union(groundFixed);vectors=sorted([(round(i*.025,6),round(j*.025,6))for i in range(-18,19)for j in range(-18,19)if 0<math.hypot(i*.025,j*.025)<=.45],key=lambda d:(math.hypot(*d),d[1],d[0]));results=[];winner=None
 for dx,dy in vectors:
  xy=[round(original['x']+dx,6),round(original['y']+dy,6)];point=Point(*xy);pairs=[r for r in returns if .90<=point.distance(Point(r['via']['x'],r['via']['y']))<=1.0];row={'delta_mm':[dx,dy],'moved_original_barrel_xy_mm':xy,'ordinary_real_before_source_return_count':len(pairs),'deficits':[],'route':None}
  if not pairs:results.append(row);continue
  bad,operations,rawRefs=viaScreen(xy);row.update({'deficits':bad,'explicit_native_normal_hole_operations':operations,'raw_before_reference_hits_retained':rawRefs})
  if bad:results.append(row);continue
  axis=LineString([[original['x'],original['y']],xy]);cap=point.buffer(.575,quad_segs=128);stubBody=axis.buffer(.1,quad_segs=128);stubOK=all(stubFreeSpace[ly].covers(axis)for ly in stubFreeSpace)and stubBody.difference(cap).is_empty;row['two_owned20_F_B_stub_Cu_hole_and_exact_moved_owncap_PASS']=stubOK
  if not stubOK:results.append(row);continue
  for ret in pairs:
   rv=ret['via'];holes2=unary_union([sh.buffer(.380005,quad_segs=64)for u,sh in holes if u not in {uid,rv['uuid']}and sh.intersects(roi)]);moving=point.buffer(.575005,quad_segs=64);stubObstacle=stubBody.buffer(.175005,quad_segs=64);gf=region.intersection(board).difference(groundFixed).difference(holes2).difference(moving).difference(stubObstacle);start=Point(pad['x'],pad['y']);end=Point(rv['x'],rv['y']);faces=[f for f in RF.parts(gf)if f.covers(start)and f.covers(end)]
   if not faces:continue
   path,method=TR.route(faces[0],list(start.coords[0]),list(end.coords[0]));path=[[round(x,6),round(y,6)]for x,y in path];body=unary_union([LineString([a,b]).buffer(.1,quad_segs=128)for a,b in zip(path,path[1:])]);contact=body.intersection(ret['ann']).area
   if not faces[0].covers(LineString(path))or contact<=0 or body.intersection(padCu).area<=0:continue
   row.update({'route':path,'ground_method':method,'ground_length_mm':sum(math.dist(a,b)for a,b in zip(path,path[1:])),'ordinary_return_UUID':rv['uuid'],'ordinary_return_distance_mm':point.distance(end),'return_native_SOURCE_before':ret['native_SOURCE_before'],'return_before_actual_J1_SOURCE_annulus_bothplanes_mm2':ret['before_actual_J1_source_plane_annulus_overlap_mm2'],'ground_finite_annulus_contact_mm2':contact});moved={**original,'x':xy[0],'y':xy[1]};tracks=[]
   for ly in ('F.Cu','B.Cu'):tracks.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R425-CDONE-owned-stub:'+ly+':'+str(xy))),'net':original['net'],'layer':ly,'w':.2,'a':[original['x'],original['y']],'b':xy})
   for i,(a,bp)in enumerate(zip(path,path[1:])):tracks.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R425-ground:'+str(xy)+':'+str(i))),'net':NET,'layer':'F.Cu','w':.2,'a':a,'b':bp})
   winner={'moved_original_barrel':moved,'exact_original_barrel':original,'only_new_tracks':tracks,'ordinary_ground_return':ret['via'],'ground_return_unchanged':True,'result':row,'CDONE_producer_before_binding':producerR,'all_other_original_Cu_holes_and_full_CORE_trunk_held':True,'native_current_all_source_oldrefs':'OPEN'};(OUT/'only-qualified-minimal-pose-and-new-tracks.pkl').write_bytes(pickle.dumps(winner,protocol=5));(OUT/'only-ground-direct-DC-body.wkb').write_bytes(body.wkb);(OUT/'two-owned-SIGNAL-stub-body.wkb').write_bytes(stubBody.wkb);break
  results.append(row)
  if winner:break
  if len(results)%50==0:put('finite-original-CDONE-pose-ordinary-return-direct-ground-screen.json',results);print('R425_POSES',len(results),flush=True)
 put('finite-original-CDONE-pose-ordinary-return-direct-ground-screen.json',results);put('only-minimal-real-CDONE-move-and-DC-ground-nomination.json',winner)
 put('receipt.json',{'status':'MINIMAL_REAL_ORIGINAL_CDONE_BARREL_OWNED_STUBS_DIRECT_GROUND_NOMINATION_ONLY','actual_R157_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'operator_SHA256':sha(policy),'R422_scope_packet_SHA256':sha(scope/'only-exact-original-CDONE-barrel-native-source-scope.pkl'),'R424_source_binding_SHA256':sha(P/'CM79-CDONE-fresh-producer-and-actual-native-group-binding-r424/receipt.json'),'candidate_count':len(results),'nomination_count':int(winner is not None),'original_full_CORE_all_MIPI_other_original_Cu_holes_poses_held':True,'original_barrel_UUID_size_span_lock_functions_preserve_pending_exact_native':True,'ordinary90to100_return_no_D4_or_radius_waiver':True,'CDONE_producer_SOURCE_and_ground_return_AFTER_SOURCE_all_native_flash_rawoldrefs_current_thermal':'OPEN','native_jobs_or_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R425_COMPLETE',sha(OUT/'receipt.json'),bool(winner),flush=True)
'''
s=s[:a]+tail+s[b:]
E=P/'exact-expanded-minimal-CDONE-move-r425.py';assert not E.exists();compile(s,str(E),'exec');E.write_text(s,encoding='utf-8')
exec(compile(s,str(E),'exec'),{'__name__':'__main__','__file__':str(E)})
