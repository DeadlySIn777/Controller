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
NET='/LOGIC_GND';OUT=P/'CM79-actual-R157-retained-CORE-named-ground-handoffs-r418'
BASE=H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
CMP=P/'CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/only-new-CM-ordinary-discrete-no-deletes.pkl'
def put(n,v):(OUT/n).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not OUT.exists();OUT.mkdir();N.assert_R157_actual_before()
 assert sha(BASE)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';g,h,b,q,c=pickle.loads(BASE.read_bytes());cm=pickle.loads(CMP.read_bytes())
 native=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes());flashes=json.loads((N.R157/'actual-full-refill-via-flashes.json').read_bytes())['vias']
 actual,ctx,bindings=N.convert_selected_actual(h,c,native,flashes,{NET},source_pcb=N.R157/'copy/board.kicad_pcb')
 # Foreign-zone guards use the full actual native refill, not old host fills.
 actual['zones']=[{**z,'fills':{ly:N.O.polys(rs)for ly,rs in z['fills'].items()}}for z in native['zones']]
 baselineTrackIds={t['uuid']for t in actual['tracks']};baselineViaIds={v['uuid']for v in actual['vias']};assert not baselineTrackIds&{t['uuid']for t in cm['tracks']};assert not baselineViaIds&{v['uuid']for v in cm['vias']}
 actual['tracks']+=copy.deepcopy(cm['tracks']);actual['vias']+=copy.deepcopy(cm['vias']);rec,trees=F.build(actual)
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
 # F transport remains .20; original full dc1a is a hard foreign obstacle.
 cuts=[]
 for r in rec['F.Cu']:
  if L.norm(r['net'])!=NET and r['shape'].intersects(roi):cuts.append(r['shape'].buffer(.1+max(gap(r['net']),float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15)+.025005,quad_segs=64))
 for z in q:
  if z['layer']=='F.Cu'and L.norm(z['net'])!=NET and z['shape'].intersects(roi):cuts.append(z['shape'].buffer(.1+max(gap(z['net']),float(z.get('clearance_mm',.15)))+.025005,quad_segs=64))
 for rules,isreserve in [(h['rule_areas'],False),(reserve['keepouts'],True)]:
  for rule in rules:
   if 'F.Cu'not in rule['layers']or(isreserve and NET in exempt.get(rule['name'],set()))or(not isreserve and not rule.get('no_tracks')):continue
   for sh in L.poly(rule['outline']):
    if sh.intersects(roi):cuts.append(sh.buffer(.125005,quad_segs=64))
 hard=unary_union(cuts);board=unary_union(L.poly(h['outline'])).buffer(-.625005);reference=refs['F.Cu'].intersection(roi)
 cmids={r['uuid']for kind in ('tracks','vias')for r in cm[kind]};sourceVias={r['uuid']for r in root if r['kind']=='via'and r['layer']=='F.Cu'};groundById={v['uuid']:v for v in actual['vias']};ports=[]
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

if __name__=='__main__':
 try:main()
 except Exception:
  if OUT.exists():put('failure.json',{'traceback':traceback.format_exc(),'adopted':False})
  raise
