"""Constructive current full-width CORE5 transport screen on real LG In4.

Only NEW CORE5 transport is withdrawable. Native source/group and endpoint
aperture scope are explicit; successful routes remain unaccepted proposals.
"""
import os,psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
proc=psutil.Process();proc.cpu_affinity(list(range(16,28)));proc.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,math,time,traceback
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely import STRtree
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import tri_route as TR
import physical_reference_losses_r3_zero_r208 as RF
K=N.K;L=N.L;sha=N.sha
OUT=H/'sbc-power/CORE5-actual-new-In2-source-port-reachability-only-new-CM-counterfactual-r408'
MP=H/'sbc-power/CM79-R369-one-positive-LG-nine-settings-exact-native-outline-profile-r371/model.pkl'
BASE=H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl'
LG='/LOGIC_GND';NET='/mc_local_power/CORE_5V'
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def main():
 started=time.monotonic();assert not OUT.exists();OUT.mkdir();N.assert_R157_actual_before()
 assert sha(MP)=='ee6697512303f8be14aa404b75094dba75e2461d17c25396827523837c162b1b';g,h,b,q,c=pickle.loads(MP.read_bytes())
 assert sha(BASE)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';_,bh,_,_,bc=pickle.loads(BASE.read_bytes())
 native=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes());flashes=json.loads((N.R157/'actual-full-refill-via-flashes.json').read_bytes())['vias']
 actual,ctx,pads=N.convert_selected_actual(bh,bc,native,flashes,{NET},source_pcb=N.R157/'copy/board.kicad_pcb')
 original=next(t for t in actual['tracks']if t['uuid']=='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1')
 assert(original['a'],original['b'],original['w'],original['layer'])==([112.95,202.35],[133.549999,202.35],1.25,'F.Cu')
 import copy,uuid
 anchors=[]
 for a,bp in (([112.95,202.35],[116.2,202.35]),([120.1,202.35],[133.549999,202.35])):
  anchor={**original,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CORE5-R295-source-test-anchor-'+str(a))), 'a':a,'b':bp};anchors.append(anchor)
 actual={**actual,'tracks':[t for t in actual['tracks']if t['uuid']!=original['uuid']]+anchors}
 # Only the original middle is withdrawn in this independent physical
 # source graph. Every native fill, pad, barrel, hole and mask is unchanged.
 saved=H/'CORE5-current-new-transport-full1p25-In3-real-LGIn4-screen-r295'; sr=json.loads((saved/'source-binding.json').read_bytes()); sf=saved/'actual-full-R157-CORE5-middle-withdrawn-all-drilled-groups.pkl'; assert sha(sf)==sr['CORE5_actual_groups_SHA256'];coregroups=pickle.loads(sf.read_bytes());(OUT/'actual-full-R157-CORE5-middle-withdrawn-all-drilled-groups.pkl').write_bytes(pickle.dumps(coregroups,protocol=5));coreroot=K.root(coregroups,'R11022','2')
 put('exact-original-middle-withdrawal-physical-source-ledger.json',{'old_track':original,'two_full_width_source_test_anchors':anchors,'withdrawn_middle_only_mm':[[116.2,202.35],[120.1,202.35]],'native_fills_pads_holes_masks_unchanged':True,'actual_post_withdrawal_root_keys':len(K.keys(coreroot))})
 lg,_=N.bound_R663_before_groups({LG});reference=K.source_refs(K.root(lg[LG],'J11001','2'))['In3.Cu']
 put('source-binding.json',{'native_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'CORE5_actual_groups_SHA256':sha(OUT/'actual-full-R157-CORE5-middle-withdrawn-all-drilled-groups.pkl'),'CORE5_root_keys':len(K.keys(coreroot)),'CORE5_root_selector':['R11022','2'],'LG_root_selector':['J11001','2'],'all_actual_holes':len(ctx[0]),'native_CORE5_pad_bindings':len(pads)})
 print('R295_ACTUAL_CORE5_SOURCE_BOUND',len(K.keys(coreroot)),flush=True)
 start=next(v for v in h['vias']if v['uuid']=='63677f16-9cb3-5144-a82d-69a2c7fb8b3d');assert(start['d'],start['drill'])==(1.,.5)
 startpoint=(123.560945,206.750243);startcap=Point(start['x'],start['y']).buffer(.775,quad_segs=128)
 targets=[]
 for r in coreroot:
  if r['kind']=='via'and r['layer']=='In3.Cu':
   v=next(v for v in actual['vias']if v['uuid']==r['uuid']); targets.append((v,r['shape']))
 # Keep native endpoint provenance; no unrelated neighbour cap is admitted.
 distinct={v['uuid']:(v,s)for v,s in targets};targets=list(distinct.values())
 region=box(10,145,215,228);roi=region.buffer(3);full_reference=reference;reference=reference.intersection(roi);targets=[(v,a)for v,a in targets if roi.covers(Point(v['x'],v['y']))];domain=h['domains_normalized'];gap=lambda n:.15 if domain.get(L.norm(n))==domain.get(NET)else .6
 withdrawn={r['exact_current_track']['uuid']for r in json.loads((H/'sbc-power/CM79-R371-exact-CORE5-new-body-gap-parallel-handoff-r390/exact-CORE5-new-tracks-and-raw-body-reference-gaps.json').read_bytes())}
 cmfile=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/only-new-CM-ordinary-discrete-no-deletes.pkl';cm=pickle.loads(cmfile.read_bytes()); cmids={x['uuid']for kind in('tracks','vias')for x in cm[kind]};obstacles=[];ledger=[];cmObstacles=[];allFixed=[]
 def add(uid,net,kind,shape,clear):
  if L.norm(net)==NET or not shape.intersects(roi):return
  expanded=shape.buffer(.625+clear+.025005,quad_segs=64);obstacles.append(expanded);(cmObstacles if uid in cmids else allFixed).append(expanded);ledger.append({'UUID':uid,'net':net,'kind':kind,'clearance_mm':clear,'only_new_CM_counterfactual_withdrawable':uid in cmids})
 for t in h['tracks']:
  if t['layer']=='In3.Cu'and t['uuid']not in withdrawn:add(t['uuid'],t['net'],'fixed_current_track',K.A.shape({'kind':'segment',**t}),gap(t['net']))
 for v in h['vias']:
  if 'In3.Cu'in v['flashed']:add(v['uuid'],v['net'],'fixed_current_via',Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128),gap(v['net']))
 for p in h['pads']:
  for s in L.poly(p['layers'].get('In3.Cu',[])):add(p['uuid'],p['net'],'fixed_current_pad',s,gap(p['net']))
 for z in native['zones']:
  # Only original native LG In3 may undergo its normal automatic clearance
  # retreat. Exact per-record old source/contact/reference gates remain OPEN.
  # No original outline or filled polygon is edited or fabricated by this screen.
  if L.norm(z['net'])==LG:continue
  for s in L.poly(N.O.polys(z['fills'].get('In3.Cu',[]))):add(z['uuid'],z['net'],'actual_full_native_foreign_fill',s,max(gap(z['net']),float(z['clearance_mm'])))
 for z in q:
  if z['layer']=='In3.Cu':add(z['uuid'],z['net'],'current_owned_plane',z['shape'],max(gap(z['net']),float(z.get('clearance_mm',.15))))
 for v in h['vias']:
  if L.norm(v['net'])!=NET:
   sh=Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)
   if sh.intersects(roi):
    expanded=sh.buffer(.905005,quad_segs=64);obstacles.append(expanded);(cmObstacles if v['uuid']in cmids else allFixed).append(expanded)
 for p in h['pads']:
  if L.norm(p['net'])!=NET:
   for s in L.poly(p.get('hole')or[]):
    if s.intersects(roi):
     expanded=s.buffer(.905005,quad_segs=64);obstacles.append(expanded);allFixed.append(expanded)
 reserve,exempt=K.A.reservations()
 for rules,isreserve in ((h['rule_areas'],False),(reserve['keepouts'],True)):
  for rule in rules:
   if 'In3.Cu'not in rule['layers']or(isreserve and NET in exempt.get(rule['name'],set()))or(not isreserve and not rule.get('no_tracks')):continue
   for s in L.poly(rule['outline']):
    if s.intersects(roi):
     expanded=s.buffer(.650005,quad_segs=64);obstacles.append(expanded);allFixed.append(expanded)
 hard=unary_union(obstacles);board=unary_union(L.poly(h['outline'])).buffer(-1.150005);put('hard-current-native-foreign-obstacle-ledger.json',ledger)
 sourceRows=[r for r in coreroot if r['layer']=='In2.Cu']; sourceCu=unary_union([r['shape'].intersection(roi)for r in sourceRows if r['shape'].intersects(roi)]);put('actual-In2-source-spatial-target-authority.json',{'source_selector':['R11022','2'],'after_middle_withdrawal_source_keys':len(K.keys(coreroot)),'source_records':[{'UUID':r['uuid'],'kind':r['kind'],'layer':r['layer'],'area_mm2':r['shape'].area}for r in sourceRows if r['shape'].intersects(roi)],'source_group_cache_SHA256':sha(sf)});(OUT/'actual-CORE5-In2-source-Cu.wkb').write_bytes(sourceCu.wkb)
 results=[]
 for name,obstacle in [('all49CMhard',hard),('ONLY_NEW_CM_counterfactual_not_a_nomination',unary_union(allFixed))]:
  allowed=unary_union([reference,startcap]);free=allowed.buffer(-.625005,quad_segs=64).intersection(region).intersection(board).difference(obstacle);face=next((p for p in RF.parts(free)if p.covers(Point(startpoint))),None);row={'scope':name,'start_has_free_face':face is not None,'power1p25_body_and_native_LGIn4_SOURCE_reference_only':True,'no_unrelated_terminal_caps':True}
  if face is not None:
   (OUT/(name+'-right-port-reachable-axis-face.wkb')).write_bytes(face.wkb);near=sourceCu.intersection(face.buffer(1.024995,quad_segs=128));oldFsource=unary_union([r['shape'].intersection(roi)for r in coreroot if r['layer']=='F.Cu'and r['shape'].intersects(roi)]);nearF=oldFsource.intersection(face.buffer(1.024995,quad_segs=128));(OUT/(name+'-reachable-potential-new-In2-source-port-Cu.wkb')).write_bytes(near.wkb);(OUT/(name+'-reachable-potential-new-F-source-port-Cu.wkb')).write_bytes(nearF.wkb);points=nearest_points(face,sourceCu)if not sourceCu.is_empty else None;row.update({'actual_source_In2_Cu_distance_to_reachable_axis_face_mm':face.distance(sourceCu),'actual_SOURCE_In2_Cu_within_fullwidth625_plus_power400_reach_mm2':near.area,'actual_SOURCE_F_Cu_within_reach_mm2':nearF.area,'nearest_actual_source_and_reachable_axis_points_mm':[list(p.coords[0])for p in points]if points else None,'reachable_axis_face_area_mm2':face.area,'new_source_port_requires_ALL6_native_foreign_mask_court_hole_RETURN_guards':'OPEN'})
  results.append(row);print('R408_SCOPE',name,json.dumps(row),flush=True)
 put('only-finite-source-port-reachability-and-new-CM-counterfactual.json',results);put('receipt.json',{'status':'NEW_SOURCE_PORT_REACHABILITY_GEOGRAPHY_AND_ONLY_NEW_CM_COUNTERFACTUAL_NO_NOMINATION','actual_R295_SOURCE_cache_SHA256':sha(sf),'actual_R157_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'source_key_count':len(K.keys(coreroot)),'all_original_field_native_and_current_owned_planes_remain_hard':True,'only_new_CM_sparse_file_SHA256':sha(cmfile),'only_new_CM_UUID_count':len(cmids),'new_CM_In3_Cu_and_hole_expanded_obstacle_count':len(cmObstacles),'no_current_route_search_repeated':True,'all_original_fullwidth_F_anchor_Cu_before_reference_masks_and_source_contacts':'HARD final new-port/reroute gate','counterfactual_is_not_remove_permission_or_a_proposal':True,'result':results,'native_jobs':0,'source_or_board_edits':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R408_COMPLETE',sha(OUT/'receipt.json'),flush=True)

if __name__=='__main__':
 try:main()
 except Exception:
  if OUT.exists():put('failure.json',{'traceback':traceback.format_exc(),'adopted':False})
  raise
