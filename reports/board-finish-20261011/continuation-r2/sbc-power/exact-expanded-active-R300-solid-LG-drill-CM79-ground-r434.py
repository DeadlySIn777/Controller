"""Actual-R157 CM79 ground-port screen with original CORE5 trunk held.

All only-new CM copper is an explicit hard obstacle for foreign nets and
its holes/pitch remain held. Old native same-domain plane clearance is an
explicit normal-fill operation; foreign owned roles are never carved.
"""
import sys,json,pickle,math,time,traceback,copy
from pathlib import Path
from shapely.geometry import Point,box,LineString
from shapely.ops import unary_union
from shapely import STRtree
P=Path(__file__).resolve().parent;H=P.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import fast_contacts as F
import tri_route as TR
import physical_reference_losses_r3_zero_r208 as RF
K=N.K;L=N.L;A=K.A;sha=N.sha
NET='/LOGIC_GND';OUT=P/'CM79-active-R300-minimal-CDONE-one-new-ordinary-ground-return-r434'
BASE=H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
CMP=P/'CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/only-new-CM-ordinary-discrete-no-deletes.pkl'
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not OUT.exists();OUT.mkdir();N.assert_R157_actual_before()
 prev=P/'CM79-R300-all-native-intents-and-local-unchanged-definition-binding-r431';rr=json.loads((prev/'receipt.json').read_bytes());pf=prev/'only-active-current-Cu-native-poses-all-native-intents-BEFORE-fill-context.pkl';assert sha(pf)==rr['packet_SHA256'];packet=pickle.loads(pf.read_bytes());actual=packet['current_Cu_and_local_native_pads'];h=packet['actual_BEFORE_model'];domain=h['domains_normalized'];beforeUIDs={z['uuid']for z in h['zones']};allq=packet['all_current_native_intents'];nativeRules=[{**r,'outline':N.O.polys(r['outline'])}for r in packet['all_current_native_rule_areas']];q=[z for z in allq if z['uuid']not in beforeUIDs or domain.get(L.norm(z['net']))!=domain.get(NET)];cm={'tracks':[],'vias':[]};native=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes());rec,trees=F.build(actual)
 source,_=N.bound_R663_before_groups({NET});groups=source[NET];root=K.root(groups,'J11001','2');refs=K.source_refs(root);pad=next(p for p in actual['pads']if(p['ref'],str(p['num']))==('J15002','79'));padCu=unary_union(L.poly(pad['layers']['F.Cu']));padGuard=padCu.buffer(.275,quad_segs=128)
 region=box(110,193,124,209);roi=region.buffer(2);domain=h['domains_normalized'];gap=lambda n:.15 if domain.get(L.norm(n))==domain.get(NET)else .6
 refPlanes={ly:unary_union([r['shape']for r in root if r['kind']=='fill'and r['layer']==ly and r['shape'].intersects(roi)])for ly in ('In1.Cu','In4.Cu')}
 nativeZones={z['uuid']:z for z in native['zones']};holes=[(v['uuid'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in actual['vias']]+[(p['uuid'],sh)for p in actual['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([s for uid,s in holes]);vp=[Point(v['x'],v['y'])for v in actual['vias']];vt=STRtree(vp)
 smds=[(p['uuid'],sh)for p in actual['pads']if not p.get('hole')for ly in('F.Cu','B.Cu')for sh in L.poly(p['layers'].get(ly,[]))];st=STRtree([s for uid,s in smds]);courts=[(f['ref'],sh)for f in h['footprints']for ss in f['courtyard'].values()for sh in L.poly(ss)];ct=STRtree([s for ref,s in courts]);reserve,exempt=A.reservations()
 masks={ly:[]for ly in refPlanes}
 for layer,rlayer in [('F.Cu','In1.Cu'),('In2.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')]:
  for r in rec[layer]:
   if r['kind']=='fill'or domain.get(L.norm(r['net']))!=domain.get(NET)or not r['shape'].intersects(roi):continue
   mask=r['shape'].intersection(refPlanes[rlayer])
   if not mask.is_empty:masks[rlayer].append({'UUID':r['uuid'],'kind':r['kind'],'shape':mask})
  for z in q:
   if z['layer']==layer and domain.get(L.norm(z['net']))==domain.get(NET)and z['shape'].intersects(roi):
    mask=z['shape'].intersection(refPlanes[rlayer])
    if not mask.is_empty:masks[rlayer].append({'UUID':z['uuid'],'kind':'held_owned_before_reference_mask','shape':mask})
 for ly in refPlanes:
  for r in root:
   if r['kind']=='via'and r['layer']==ly and r['shape'].intersects(roi):masks[ly].append({'UUID':r['uuid'],'kind':'actual_J1_SOURCE_annulus','shape':r['shape'].intersection(refPlanes[ly])})
 mt={ly:STRtree([r['shape']for r in masks[ly]])for ly in masks}
 policy=Path('Z:/pcb-runs/OPERATOR-DECISIONS-2026-10-03.md');assert sha(policy)=='392e2155400e156d180ac5a786b2d7e4a41c2dcc945bfc7a8de9b9e21b02dde5';policytext=policy.read_text(encoding='utf-8');assert "A new signal via's return requirement"in policytext
 # F transport remains .20; original full dc1a is a hard foreign obstacle.
 cuts=[]
 for r in rec['F.Cu']:
  if L.norm(r['net'])!=NET and r['shape'].intersects(roi):cuts.append(r['shape'].buffer(.1+max(gap(r['net']),float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15)+.025005,quad_segs=64))
 for z in q:
  if z['layer']=='F.Cu'and L.norm(z['net'])!=NET and z['shape'].intersects(roi):cuts.append(z['shape'].buffer(.1+max(gap(z['net']),float(z.get('clearance_mm',.15)))+.025005,quad_segs=64))
 for uid,sh in holes:
  if sh.intersects(roi):cuts.append(sh.buffer(.380005,quad_segs=64))
 for rules,isreserve in [(nativeRules,False)]:
  for rule in rules:
   if 'F.Cu'not in rule['layers']or(isreserve and NET in exempt.get(rule['name'],set()))or(not isreserve and not rule.get('no_tracks')):continue
   for sh in L.poly(rule['outline']):
    if sh.intersects(roi):cuts.append(sh.buffer(.125005,quad_segs=64))
 hard=unary_union(cuts);board=unary_union(L.poly(h['outline'])).buffer(-.625005);reference=refs['F.Cu'].intersection(roi)
 import uuid
 SIG='/fpga_core/FPGA_CDONE';uid='b1e550d5-047a-447c-a64c-45c2a92c14b0';original=next(v for v in actual['vias']if v['uuid']==uid);assert (original['x'],original['y'],original['d'],original['drill'])==(117.45,200.05,.6,.3);ownTracks={'b7dc346a-8a46-4b4c-ae3d-c5990ddefc96','490ef90c-4585-48f9-8331-37af95c295c8'};scope=P/'CM79-actual-CDONE-original-barrel-source-and-incident-scope-r422';scopeR=json.loads((scope/'receipt.json').read_bytes());assert sha(scope/'only-exact-original-CDONE-barrel-native-source-scope.pkl')==scopeR['scope_packet_SHA256'];sourceScope=pickle.loads((scope/'only-exact-original-CDONE-barrel-native-source-scope.pkl').read_bytes());producerR=json.loads((P/'CM79-CDONE-fresh-producer-and-actual-native-group-binding-r424/receipt.json').read_bytes());assert producerR['producer']['ref']=='U1001'and producerR['producer']['pin']=='R1';cmids={r['uuid']for kind in ('tracks','vias')for r in cm[kind]}
 returns=[]
 rv={'uuid':'31a0cdf9-98e1-5e65-8573-5a1327438cda','net':NET,'x':117.164998,'y':199.28645,'d':.5,'drill':.2,'span':K.LAYERS,'flashed':K.LAYERS,'locked':False,'mask_provenance':'PROSPECTIVE ordinary via, actual native masks OPEN'}
 assert rv['uuid']not in {v['uuid']for v in actual['vias']}
 rp=Point(rv['x'],rv['y']);ann=rp.buffer(.25,quad_segs=128).difference(rp.buffer(.1,quad_segs=128));over={ly:ann.intersection(refPlanes[ly]).area for ly in refPlanes};assert all(x>0 for x in over.values());returns.append({'via':rv,'ann':ann,'before_actual_J1_source_plane_annulus_overlap_mm2':over,'native_SOURCE_before':False})
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
  for rules,isreserve in [(nativeRules,False)]:
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
   if r['kind']=='fill'and r['uuid']in beforeUIDs and domain.get(L.norm(r['net']))==domain.get(SIG):continue
   local=float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15;cuts.append(r['shape'].buffer(.1+max(local,gap(r['net']))+.025005,quad_segs=64))
  for z in q:
   if z['layer']==layer and L.norm(z['net'])!=SIG and z['shape'].intersects(roi):cuts.append(z['shape'].buffer(.1+max(gap(z['net']),float(z.get('clearance_mm',.15)))+.025005,quad_segs=64))
  for u,sh in holes:
   if u!=uid and sh.intersects(roi):cuts.append(sh.buffer(.380005,quad_segs=64))
  for rules,isreserve in [(nativeRules,False)]:
   for rule in rules:
    if layer not in rule['layers']or(isreserve and SIG in exempt.get(rule['name'],set()))or(not isreserve and not rule.get('no_tracks')):continue
    cuts.extend(sh.buffer(.125005,quad_segs=64)for sh in L.poly(rule['outline'])if sh.intersects(roi))
  return region.intersection(board).difference(unary_union(cuts))
 from bind_R300_all_native_intents_CM_context_r431 import fields
 inv=A.C.inventory(Path(packet['active_board']).read_bytes());solidProfiles=[]
 for zuid in ('58c55cd5-98e6-4467-88e3-146ceeee361a','c1d27fa1-452b-4e27-985d-5ad23644d800'):
  f=fields(inv[3][zuid]);cp=next(x for x in f if x.startswith('(connect_pads'));assert cp.startswith('(connect_pads yes');solidProfiles.append({'UUID':zuid,'exact_current_native_fields':[x for x in f if not x.startswith('(polygon')],'LOGIC_GND_via_connection':'FULL_SOLID','own_plane_prospective_subtraction':'actual .10 mm physical drill only; no foreign signal antipad or thermal gap authority'})
 put('exact-current-original-LG-solid-connection-profile-and-drill-authority.json',solidProfiles)
 groundBad=[];groundOps=[];groundRawRefs=[]
 for ly in K.LAYERS:
  for j in trees[ly].query(rp.buffer(1.2),predicate='intersects'):
   r=rec[ly][int(j)];n=L.norm(r['net'])
   if n==NET or r['uuid']==uid:continue
   local=float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15;req=max(local,gap(n))+.025
   if r['kind']=='fill'and r['uuid']in beforeUIDs and domain.get(n)==domain.get(NET):
    if rp.distance(r['shape'])-.25<req:groundOps.append({'UUID':r['uuid'],'layer':ly,'native_normal_same_domain_antipad_radius_mm':.25+local,'outline_unchanged':True})
    continue
   if rp.distance(r['shape'])-.25<req:groundBad.append({'kind':'ground_return_actual_foreign_Cu','UUID':r['uuid'],'layer':ly,'net':r['net']})
  for z in q:
   if z['layer']==ly and L.norm(z['net'])!=NET and rp.distance(z['shape'])-.25<max(gap(z['net']),z['clearance_mm'])+.025:groundBad.append({'kind':'ground_return_current_foreign_intent','UUID':z['uuid'],'layer':ly})
 for j in ht.query(rp.buffer(.6),predicate='intersects'):
  u,sh=holes[int(j)]
  if u!=uid and rp.distance(sh)-.1<.28:groundBad.append({'kind':'ground_return_drill','UUID':u})
 for j in st.query(rp.buffer(.4),predicate='intersects'):
  u,sh=smds[int(j)]
  if rp.distance(sh)-.1<.28:groundBad.append({'kind':'ground_return_SMD_drill','UUID':u})
 for j in vt.query(rp.buffer(.82),predicate='intersects'):
  u=actual['vias'][int(j)]['uuid']
  if u!=uid and rp.distance(vp[int(j)])<.815:groundBad.append({'kind':'ground_return_pitch','UUID':u})
 for rule in nativeRules:
  if rule['no_vias']and any(rp.distance(sh)<.275 for sh in L.poly(rule['outline'])):groundBad.append({'kind':'ground_return_native_rule','UUID':rule['uuid']})
 for ly in refPlanes:
  for j in mt[ly].query(rp.buffer(.1,quad_segs=128),predicate='intersects'):
   r=masks[ly][int(j)];hit=rp.buffer(.1,quad_segs=128).intersection(r['shape'])
   if hit.is_empty:continue
   sr=next((rr for ll in ('F.Cu','In2.Cu','B.Cu','In3.Cu')for rr in rec[ll]if rr['uuid']==r['UUID']),None);n=L.norm(sr['net'])if sr else None
   row={'UUID':r['UUID'],'layer':ly,'kind':r['kind'],'hit_mm2':hit.area,'own_original_signal_terminal':r['UUID']in ownTracks|{uid},'DC_ground_shadow_only':n==NET};groundRawRefs.append(row)
   if not row['own_original_signal_terminal']and not row['DC_ground_shadow_only']:groundBad.append({'kind':'ground_return_nonLG_old_source_reference_mask','UUID':r['UUID'],'layer':ly,'hit_mm2':hit.area})
 put('one-new-ground-return-current-guards-and-raw-old-reference-hits.json',{'ground_return':rv,'deficits':groundBad,'normal_native_fill_operations':groundOps,'raw_old_reference_hits':groundRawRefs,'before_actual_J1_source_annuli_mm2':over,'no_current_AFTER_SOURCE_claim':True})
 helperRaw=[]
 for rule in reserve['keepouts']:
  if SIG in exempt.get(rule['name'],set()):continue
  for sh in L.poly(rule['outline']):
   hit=LineString([[117.45,200.05],[117.7,200.025]]).buffer(.1,quad_segs=128).intersection(sh)
   if not hit.is_empty:helperRaw.append({'name':rule['name'],'owned_F_stub_overlap_mm2':hit.area,'rule_conditional_disallow_tracks_vias':True,'native_authority_applicability':'OPEN_design_intent_review'})
 put('helper-escape-reservation-raw-FAIL-preserved.json',helperRaw)
 stubFreeSpace={ly:stubFree(ly)for ly in ('F.Cu','B.Cu')};groundFixed=[]
 for r in rec['F.Cu']:
  if r['uuid']==uid or L.norm(r['net'])==NET or not r['shape'].intersects(roi):continue
  local=float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15;groundFixed.append(r['shape'].buffer(.1+max(local,gap(r['net']))+.025005,quad_segs=64))
 for z in q:
  if z['layer']=='F.Cu'and L.norm(z['net'])!=NET and z['shape'].intersects(roi):groundFixed.append(z['shape'].buffer(.1+max(gap(z['net']),float(z.get('clearance_mm',.15)))+.025005,quad_segs=64))
 for rules,isreserve in [(nativeRules,False)]:
  for rule in rules:
   if 'F.Cu'not in rule['layers']or(isreserve and NET in exempt.get(rule['name'],set()))or(not isreserve and not rule.get('no_tracks')):continue
   groundFixed.extend(sh.buffer(.125005,quad_segs=64)for sh in L.poly(rule['outline'])if sh.intersects(roi))
 groundFixed=unary_union(groundFixed);vectors=[(.25,-.025)];results=[];winner=None
 for dx,dy in vectors:
  xy=[round(original['x']+dx,6),round(original['y']+dy,6)];point=Point(*xy);pairs=[r for r in returns if .90<=point.distance(Point(r['via']['x'],r['via']['y']))<=1.0];row={'delta_mm':[dx,dy],'moved_original_barrel_xy_mm':xy,'ordinary_real_before_source_return_count':len(pairs),'deficits':[],'route':None}
  if not pairs:results.append(row);continue
  bad,operations,rawRefs=viaScreen(xy);row.update({'deficits':bad,'explicit_native_normal_hole_operations':operations,'raw_before_reference_hits_retained':rawRefs})
  if bad or groundBad:row['ground_return_deficits']=groundBad;results.append(row);continue
  axis=LineString([[original['x'],original['y']],xy]);cap=point.buffer(.575,quad_segs=128);stubBody=axis.buffer(.1,quad_segs=128);stubOK=all(stubFreeSpace[ly].covers(axis)for ly in stubFreeSpace)and stubBody.difference(cap).is_empty;row['two_owned20_F_B_stub_Cu_hole_and_exact_moved_owncap_PASS']=stubOK
  if not stubOK:results.append(row);continue
  for ret in pairs:
   rv=ret['via'];holes2=unary_union([sh.buffer(.380005,quad_segs=64)for u,sh in holes if u not in {uid,rv['uuid']}and sh.intersects(roi)]);moving=point.buffer(.575005,quad_segs=64);stubObstacle=stubBody.buffer(.275005,quad_segs=64);gf=region.intersection(board).difference(groundFixed).difference(holes2).difference(moving).difference(stubObstacle);start=Point(pad['x'],pad['y']);end=Point(rv['x'],rv['y']);faces=[f for f in RF.parts(gf)if f.covers(start)and f.covers(end)]
   if not faces:continue
   path,method=TR.route(faces[0],list(start.coords[0]),list(end.coords[0]));path=[[round(x,6),round(y,6)]for x,y in path];body=unary_union([LineString([a,b]).buffer(.1,quad_segs=128)for a,b in zip(path,path[1:])]);contact=body.intersection(ret['ann']).area
   if not faces[0].covers(LineString(path))or contact<=0 or body.intersection(padCu).area<=0:continue
   row.update({'route':path,'ground_method':method,'ground_length_mm':sum(math.dist(a,b)for a,b in zip(path,path[1:])),'ordinary_return_UUID':rv['uuid'],'ordinary_return_distance_mm':point.distance(end),'return_native_SOURCE_before':ret['native_SOURCE_before'],'return_before_actual_J1_SOURCE_annulus_bothplanes_mm2':ret['before_actual_J1_source_plane_annulus_overlap_mm2'],'ground_finite_annulus_contact_mm2':contact});moved={**original,'x':xy[0],'y':xy[1]};tracks=[]
   for ly in ('F.Cu','B.Cu'):tracks.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R434-CDONE-owned-stub:'+ly+':'+str(xy))),'net':original['net'],'layer':ly,'w':.2,'a':[original['x'],original['y']],'b':xy})
   for i,(a,bp)in enumerate(zip(path,path[1:])):tracks.append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R434-ground:'+str(xy)+':'+str(i))),'net':NET,'layer':'F.Cu','w':.2,'a':a,'b':bp})
   winner={'moved_original_barrel':moved,'exact_original_barrel':original,'only_new_tracks':tracks,'ordinary_ground_return':ret['via'],'ground_return_unchanged':False,'only_new_ground_via':rv,'all_current_native_intents_binding':rr,'helper_reservation_policy':'RAW_FAIL_RETAINED_PENDING_NARROW_SCOPE_REVIEW','result':row,'CDONE_producer_before_binding':producerR,'all_other_original_Cu_holes_and_full_CORE_trunk_held':True,'native_current_all_source_oldrefs':'OPEN'};(OUT/'only-qualified-minimal-pose-and-new-tracks.pkl').write_bytes(pickle.dumps(winner,protocol=5));(OUT/'only-ground-direct-DC-body.wkb').write_bytes(body.wkb);(OUT/'two-owned-SIGNAL-stub-body.wkb').write_bytes(stubBody.wkb);break
  results.append(row)
  if winner:break
  if len(results)%50==0:put('finite-original-CDONE-pose-ordinary-return-direct-ground-screen.json',results);print('R425_POSES',len(results),flush=True)
 put('finite-original-CDONE-pose-ordinary-return-direct-ground-screen.json',results);put('only-minimal-real-CDONE-move-and-DC-ground-nomination.json',winner)
 put('receipt.json',{'status':'MINIMAL_REAL_ORIGINAL_CDONE_BARREL_OWNED_STUBS_DIRECT_GROUND_NOMINATION_ONLY','retained_R432_failure':'Native polyset guard schema was [outer,hole...] rather than host [outer,[holes...]]; no candidate output/adoption','active_R300_native_intent_binding':rr,'actual_R157_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'operator_SHA256':sha(policy),'R422_scope_packet_SHA256':sha(scope/'only-exact-original-CDONE-barrel-native-source-scope.pkl'),'R424_source_binding_SHA256':sha(P/'CM79-CDONE-fresh-producer-and-actual-native-group-binding-r424/receipt.json'),'candidate_count':len(results),'nomination_count':int(winner is not None),'original_full_CORE_all_MIPI_other_original_Cu_holes_poses_held':True,'original_barrel_UUID_size_span_lock_functions_preserve_pending_exact_native':True,'ordinary90to100_return_no_D4_or_radius_waiver':True,'helper_raw_FAIL_preserved_count':len(helperRaw),'one_new_ground_return_deficit_count':len(groundBad),'new_LG_same_plane_physical_drill_radius_mm':.1,'R433_signal_style_525_cap_raw_reference_FAIL_preserved':True,'actual_current_original_LG_full_solid_profile_file':'exact-current-original-LG-solid-connection-profile-and-drill-authority.json','all49_prospective_CM_EXCLUDED':True,'ground_to_SIGNAL_stub_axis_extra_buffer_mm':.275005,'CDONE_producer_SOURCE_and_ground_return_AFTER_SOURCE_all_native_flash_rawoldrefs_current_thermal':'OPEN','native_jobs_or_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R434_COMPLETE',sha(OUT/'receipt.json'),bool(winner),flush=True)

if __name__=='__main__':
 try:main()
 except Exception:
  if OUT.exists():put('failure.json',{'traceback':traceback.format_exc(),'adopted':False})
  raise
