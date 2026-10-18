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
NET='/LOGIC_GND';OUT=P/'CM79-actual-R157-retained-CORE-ground-port-census-r417'
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
 def screen(xy):
  point=Point(*xy);bad=[];ops=[]
  for ly in K.LAYERS:
   for j in trees[ly].query(point.buffer(1.2),predicate='intersects'):
    r=rec[ly][int(j)];net=L.norm(r['net'])
    if net==NET:continue
    local=float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15;required=max(local,gap(net))+.025;distance=point.distance(r['shape'])-.25
    if r['kind']=='fill'and r['uuid']in nativeZones and domain.get(net)==domain.get(NET):
     if distance<required:ops.append({'UUID':r['uuid'],'layer':ly,'net':r['net'],'native_antipad_radius_mm':.25+local,'planner_antipad_radius_mm':.25+required,'original_zone_outline_settings_held':True})
     continue
    if distance<required:bad.append({'kind':'full_actual_native_foreign_Cu','UUID':r['uuid'],'layer':ly,'net':r['net'],'gap_mm':distance,'required_mm':required})
   for z in q:
    if z['layer']==ly and L.norm(z['net'])!=NET and point.distance(z['shape'])-.25<max(float(z.get('clearance_mm',.15)),gap(z['net']))+.025:bad.append({'kind':'all_current_owned_foreign_plane_hard','UUID':z['uuid'],'layer':ly})
  for j in ht.query(point.buffer(.4),predicate='intersects'):
   uid,sh=holes[int(j)]
   if point.distance(sh)-.1<.28:bad.append({'kind':'true_all_existing_hole_clearance','UUID':uid})
  for j in st.query(point.buffer(.385),predicate='intersects'):
   uid,sh=smds[int(j)]
   if point.distance(sh)-.1<.28:bad.append({'kind':'SMD_to_new_drill','UUID':uid})
  for j in vt.query(point.buffer(.82),predicate='intersects'):
   if point.distance(vp[int(j)])<.815:bad.append({'kind':'ordinary_via_pitch','UUID':actual['vias'][int(j)]['uuid']})
  for j in ct.query(point.buffer(.275),predicate='intersects'):bad.append({'kind':'real_courtyard_no_D4','ref':courts[int(j)][0]})
  for rules,isreserve in [(h['rule_areas'],False),(reserve['keepouts'],True)]:
   for rule in rules:
    if(isreserve and NET in exempt.get(rule['name'],set()))or(not isreserve and not rule.get('no_vias')):continue
    if any(point.distance(s)<.275 for s in L.poly(rule['outline'])):bad.append({'kind':'native_or_reserved_via_rule','name':rule.get('name',rule.get('uuid'))})
  cut=point.buffer(.1,quad_segs=128);ann=point.buffer(.25,quad_segs=128).difference(cut);annOver={}
  for ly in refPlanes:
   annOver[ly]=ann.intersection(refPlanes[ly]).area
   if annOver[ly]<=0:bad.append({'kind':'no_actual_J1_SOURCE_LG_annulus','layer':ly})
   for j in mt[ly].query(cut,predicate='intersects'):
    r=masks[ly][int(j)];hit=cut.intersection(r['shape'])
    if not hit.is_empty:bad.append({'kind':'held_actual_before_reference_body_role_SOURCE_annulus','UUID':r['UUID'],'layer':ly,'hit_type':hit.geom_type,'hit_area_mm2':hit.area})
  return bad,ops,annOver
 candidates=sorted([[round(110+.2*i,6),round(193+.2*j,6)]for i in range(71)for j in range(81)],key=lambda xy:math.dist(xy,[pad['x'],pad['y']]))
 rows=[];legal=[]
 for xy in candidates:
  if math.dist(xy,[pad['x'],pad['y']])>8:continue
  bad,ops,annOver=screen(xy);row={'xy_mm':xy,'diameter_drill_mm':[.5,.2],'deficits':bad,'explicit_same_domain_native_plane_operations':ops,'actual_SOURCE_LG_annulus_overlap_mm2':annOver};rows.append(row)
  if not bad:legal.append(row)
  if len(rows)%100==0:put('finite-new-LG-ordinary-via-true-native-mask-census.json',rows);print('R417_SCREEN',len(rows),len(legal),flush=True)
 put('finite-new-LG-ordinary-via-true-native-mask-census.json',rows);put('only-eligible-new-LG-source-ports.json',legal)
 # F transport remains .20; original full dc1a is a hard foreign obstacle.
 cuts=[]
 for r in rec['F.Cu']:
  if L.norm(r['net'])!=NET and r['shape'].intersects(roi):cuts.append(r['shape'].buffer(.1+max(gap(r['net']),float(nativeZones[r['uuid']]['clearance_mm'])if r['kind']=='fill'and r['uuid']in nativeZones else .15)+.025005,quad_segs=64))
 for z in q:
  if z['layer']=='F.Cu'and L.norm(z['net'])!=NET and z['shape'].intersects(roi):cuts.append(z['shape'].buffer(.1+max(gap(z['net']),float(z.get('clearance_mm',.15)))+.025005,quad_segs=64))
 for uid,sh in holes:
  if sh.intersects(roi):cuts.append(sh.buffer(.380005,quad_segs=64))
 for rules,isreserve in [(h['rule_areas'],False),(reserve['keepouts'],True)]:
  for rule in rules:
   if 'F.Cu'not in rule['layers']or(isreserve and NET in exempt.get(rule['name'],set()))or(not isreserve and not rule.get('no_tracks')):continue
   for sh in L.poly(rule['outline']):
    if sh.intersects(roi):cuts.append(sh.buffer(.125005,quad_segs=64))
 hard=unary_union(cuts);board=unary_union(L.poly(h['outline'])).buffer(-.625005);reference=refs['F.Cu'].intersection(roi)
 routes=[];winner=None
 for row in legal:
  xy=row['xy_mm'];cap=Point(*xy).buffer(.525,quad_segs=128);allowed=unary_union([reference,padGuard,cap]);free=allowed.buffer(-.100005,quad_segs=64).intersection(region).intersection(board).difference(hard);start=Point(pad['x'],pad['y']);end=Point(*xy);faces=[f for f in RF.parts(free)if f.covers(start)and f.covers(end)];rr={'new_source_LG_via_xy':xy,'full_actual_SOURCE_reference_and_retained_CORE_F_axis_face_count':len(faces),'route':None}
  for face in faces:
   path,method=TR.route(face,list(start.coords[0]),xy);path=[[round(x,6),round(y,6)]for x,y in path];body=unary_union([LineString([a,b]).buffer(.1,quad_segs=128)for a,b in zip(path,path[1:])]);missing=body.difference(allowed)
   if not missing.is_empty or body.intersection(padCu).area<=0:continue
   rr.update({'route':path,'method':method,'fullbody_reference_gap_EMPTY':missing.is_empty,'actual_original_pad_contact_mm2':body.intersection(padCu).area,'length_mm':sum(math.dist(a,b)for a,b in zip(path,path[1:]))});winner={'port':row,'transport':rr};(OUT/'only-nominated-CM79-F-source-connection-body.wkb').write_bytes(body.wkb);break
  routes.append(rr)
  if winner:break
 put('finite-retained-original-CORE-CM79-F-transport-attempts.json',routes);put('only-ground-port-route-nomination.json',winner)
 put('receipt.json',{'status':'ACTUAL_FULL_R157_CM79_RETAINED_CORE_GROUND_PORT_SCREEN','actual_R157_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'R663_receipt_SHA256':sha(N.R663/'receipt.json'),'only49_CM_sparse_SHA256':sha(CMP),'new_only49_CM_tracks_vias':[len(cm['tracks']),len(cm['vias'])],'CM79_actual_original_pad_UUID':pad['uuid'],'CM79_pad_xy_mm':[pad['x'],pad['y']],'site_count':len(rows),'eligible_site_count':len(legal),'route_attempt_count':len(routes),'nomination_count':int(winner is not None),'original_full_CORE_trunk_all_old_Cu_holes_poses_native_rules_held':True,'new_ground_via_SOURCE_annulus_bothplanes_actual':True,'old_SOURCE_contacts_native_all_current_refs_current_thermal':'OPEN','new_CM_via_flashes_not_native_attested_here':True,'native_jobs_or_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R417_COMPLETE',sha(OUT/'receipt.json'),len(legal),bool(winner),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if OUT.exists():put('failure.json',{'traceback':traceback.format_exc(),'adopted':False})
  raise
