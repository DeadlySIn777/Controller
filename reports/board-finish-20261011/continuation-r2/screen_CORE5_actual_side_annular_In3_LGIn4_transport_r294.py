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
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import tri_route as TR
import physical_reference_losses_r3_zero_r208 as RF
K=N.K;L=N.L;sha=N.sha
OUT=H/'CORE5-current-new-transport-full1p25-In3-real-LGIn4-screen-r294'
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
  anchor={**original,'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CORE5-R294-source-test-anchor-'+str(a))), 'a':a,'b':bp};anchors.append(anchor)
 actual={**actual,'tracks':[t for t in actual['tracks']if t['uuid']!=original['uuid']]+anchors}
 # Only the original middle is withdrawn in this independent physical
 # source graph. Every native fill, pad, barrel, hole and mask is unchanged.
 coregroups=K.physical(actual,NET,ctx)[1];(OUT/'actual-full-R157-CORE5-middle-withdrawn-all-drilled-groups.pkl').write_bytes(pickle.dumps(coregroups,protocol=5));coreroot=K.root(coregroups,'R11022','2')
 put('exact-original-middle-withdrawal-physical-source-ledger.json',{'old_track':original,'two_full_width_source_test_anchors':anchors,'withdrawn_middle_only_mm':[[116.2,202.35],[120.1,202.35]],'native_fills_pads_holes_masks_unchanged':True,'actual_post_withdrawal_root_keys':len(K.keys(coreroot))})
 lg,_=N.bound_R663_before_groups({LG});reference=K.source_refs(K.root(lg[LG],'J11001','2'))['In3.Cu']
 put('source-binding.json',{'native_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'CORE5_actual_groups_SHA256':sha(OUT/'actual-full-R157-CORE5-middle-withdrawn-all-drilled-groups.pkl'),'CORE5_root_keys':len(K.keys(coreroot)),'CORE5_root_selector':['R11022','2'],'LG_root_selector':['J11001','2'],'all_actual_holes':len(ctx[0]),'native_CORE5_pad_bindings':len(pads)})
 print('R294_ACTUAL_CORE5_SOURCE_BOUND',len(K.keys(coreroot)),flush=True)
 start=next(v for v in h['vias']if v['uuid']=='63677f16-9cb3-5144-a82d-69a2c7fb8b3d');assert(start['d'],start['drill'])==(1.,.5)
 startpoint=(123.560945,206.750243);startcap=Point(start['x'],start['y']).buffer(.775,quad_segs=128)
 targets=[]
 for r in coreroot:
  if r['kind']=='via'and r['layer']=='In3.Cu':
   v=next(v for v in actual['vias']if v['uuid']==r['uuid']); targets.append((v,r['shape']))
 # Keep native endpoint provenance; no unrelated neighbour cap is admitted.
 distinct={v['uuid']:(v,s)for v,s in targets};targets=list(distinct.values())
 region=box(10,145,215,228);roi=region.buffer(3);domain=h['domains_normalized'];gap=lambda n:.15 if domain.get(L.norm(n))==domain.get(NET)else .6
 withdrawn={r['exact_current_track']['uuid']for r in json.loads((H/'sbc-power/CM79-R371-exact-CORE5-new-body-gap-parallel-handoff-r390/exact-CORE5-new-tracks-and-raw-body-reference-gaps.json').read_bytes())}
 obstacles=[];ledger=[]
 def add(uid,net,kind,shape,clear):
  if L.norm(net)==NET or not shape.intersects(roi):return
  obstacles.append(shape.buffer(.625+clear+.025005,quad_segs=64));ledger.append({'UUID':uid,'net':net,'kind':kind,'clearance_mm':clear})
 for t in h['tracks']:
  if t['layer']=='In3.Cu'and t['uuid']not in withdrawn:add(t['uuid'],t['net'],'fixed_current_track',K.A.shape({'kind':'segment',**t}),gap(t['net']))
 for v in h['vias']:
  if 'In3.Cu'in v['flashed']:add(v['uuid'],v['net'],'fixed_current_via',Point(v['x'],v['y']).buffer(v['d']/2,quad_segs=128),gap(v['net']))
 for p in h['pads']:
  for s in L.poly(p['layers'].get('In3.Cu',[])):add(p['uuid'],p['net'],'fixed_current_pad',s,gap(p['net']))
 for z in native['zones']:
  for s in L.poly(N.O.polys(z['fills'].get('In3.Cu',[]))):add(z['uuid'],z['net'],'actual_full_native_foreign_fill',s,max(gap(z['net']),float(z['clearance_mm'])))
 for z in q:
  if z['layer']=='In3.Cu':add(z['uuid'],z['net'],'current_owned_plane',z['shape'],max(gap(z['net']),float(z.get('clearance_mm',.15))))
 for v in h['vias']:
  if L.norm(v['net'])!=NET:
   sh=Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)
   if sh.intersects(roi):obstacles.append(sh.buffer(.905005,quad_segs=64))
 for p in h['pads']:
  if L.norm(p['net'])!=NET:
   for s in L.poly(p.get('hole')or[]):
    if s.intersects(roi):obstacles.append(s.buffer(.905005,quad_segs=64))
 reserve,exempt=K.A.reservations()
 for rules,isreserve in ((h['rule_areas'],False),(reserve['keepouts'],True)):
  for rule in rules:
   if 'In3.Cu'not in rule['layers']or(isreserve and NET in exempt.get(rule['name'],set()))or(not isreserve and not rule.get('no_tracks')):continue
   for s in L.poly(rule['outline']):
    if s.intersects(roi):obstacles.append(s.buffer(.650005,quad_segs=64))
 hard=unary_union(obstacles);board=unary_union(L.poly(h['outline'])).buffer(-1.150005);put('hard-current-native-foreign-obstacle-ledger.json',ledger)
 results=[];accepted=[]
 for target,ann in targets:
  targetcap=Point(target['x'],target['y']).buffer(target['d']/2+.275,quad_segs=128)
  allowed=unary_union([reference,startcap,targetcap]);free=allowed.buffer(-.625005,quad_segs=64).intersection(region).intersection(board).difference(hard)
  endpoint=(target['x'],target['y']);a=Point(startpoint);e=Point(endpoint);target_axis_contact=ann.buffer(.624995,quad_segs=128);faces=[p for p in RF.parts(free)if p.covers(a)and not p.intersection(target_axis_contact).is_empty]
  row={'target_UUID':target['uuid'],'target_xy':list(endpoint),'actual_observed_In3_Cu':True,'start_cap_exact_inner_nominal_mm':.775,'target_cap_exact_inner_nominal_mm':target['d']/2+.275,'start_free':free.covers(a),'target_free':free.covers(e),'common_component_count':len(faces),'route':None}
  for face in faces:
   available=face.intersection(target_axis_contact).buffer(-.000005)
   if available.is_empty:continue
   endpoint=list(nearest_points(a,available)[1].coords[0]);row['actual_target_side_contact_axis_endpoint']=endpoint
   path,method=TR.route(face,startpoint,endpoint);path=[[round(x,6),round(y,6)]for x,y in path];body=unary_union([LineString([aa,bb]).buffer(.625,quad_segs=128)for aa,bb in zip(path,path[1:])])
   missing=body.difference(allowed)
   if not missing.is_empty:row['raw_post_rounding_reference_gap_area_mm2']=missing.area;continue
   row['route']=path;row['route_length_mm']=sum(math.dist(aa,bb)for aa,bb in zip(path,path[1:]));row['method']=method;row['whole_body_minus_actual_source_and_only_endpoint_inner_caps_EMPTY']=True;row['actual_target_annular_overlap_mm2']=body.intersection(ann).area;row['actual_start_annular_overlap_mm2']=body.intersection(Point(start['x'],start['y']).buffer(.5,quad_segs=128).difference(Point(start['x'],start['y']).buffer(.25,quad_segs=128))).area
   if row['actual_target_annular_overlap_mm2']<=0 or row['actual_start_annular_overlap_mm2']<=0:row['route']=None;continue
   accepted.append(row);(OUT/(target['uuid']+'-full-new-body.wkb')).write_bytes(body.wkb);break
  results.append(row);put('per-actual-source-barrel-full-current-In3-LGIn4-tests.json',results);print('R294_TARGET',target['uuid'],row['start_free'],row['target_free'],len(faces),bool(row['route']),flush=True)
 put('only-full-width-actual-source-reference-route-nominations.json',accepted);put('receipt.json',{'status':'ACTUAL_FULL_NATIVE_CORE5_LGIn4_CURRENT_NEW_TRANSPORT_CONSTRUCTIVE_SCREEN_COMPLETE','model_SHA256':sha(MP),'actual_native_source_binding_receipt_SHA256':sha(OUT/'source-binding.json'),'target_count':len(targets),'proposal_count':len(accepted),'only_NEW_CORE5_transport_withdrawable':sorted(withdrawn),'source_is_actual_R157_AFTER_exact_original_middle_withdrawal':True,'width_mm':1.25,'actual_foreign_planes_discrete_and_holes_hard':True,'only_route_endpoint_caps_permitted':True,'positive_source_reference_not_synthetic':True,'F_spur_reference_return_pair_signed_current_native_DRC_SI_thermal':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started})
 print('R294_COMPLETE',sha(OUT/'receipt.json'),len(accepted),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if OUT.exists():put('failure.json',{'traceback':traceback.format_exc(),'adopted':False})
  raise
