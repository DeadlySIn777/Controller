"""Current no-hole SDO transport nomination; full In4 source gate pending."""
import os,psutil
for name in ('OPENBLAS_NUM_THREADS','OMP_NUM_THREADS','MKL_NUM_THREADS','NUMEXPR_NUM_THREADS'):os.environ[name]='2'
p=psutil.Process();p.cpu_affinity(list(range(16,28)));p.nice(psutil.BELOW_NORMAL_PRIORITY_CLASS)
import sys,json,pickle,hashlib,math,uuid,time
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union
from shapely import STRtree
from shapely.affinity import translate
H=Path(__file__).resolve().parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import R157_native_selected_actual_conversion_r673 as N
import tri_route as T
import guarded_power_projection_r44 as Z
K=N.K;L=N.L;sha=N.sha
OUT=H/'existing-old-In3-port-current-physical-r315-pair2'
NET='/mc_motor_buffers/DIR10_TO_MX4';LY='In3.Cu'
def put(n,x):(OUT/n).write_text(json.dumps(x,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def ds(s):return {'EMPTY':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds':None if s.is_empty else list(s.bounds),'WKB_SHA256':hashlib.sha256(s.wkb).hexdigest()}
def main():
 started=time.monotonic();assert not OUT.exists();OUT.mkdir();N.assert_R157_actual_before()
 base=H/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(base)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';_,h,_,_,_=pickle.loads(base.read_bytes())
 ep=H/'combined-R753-all-Cu-explicit-retained-actual-via-scope-r300/all-copper-expected.json';assert sha(ep)=='13a6a92d39e33f05a38107c7b9348c29847239671ee5b4c0ffa48a89536dead3';e=json.loads(ep.read_bytes())
 pp=H/'combined-R753-one-full-native-fill-cached-DRC-r299/native-full/before-native-all-FP-pad-pose.json';poses=json.loads(pp.read_bytes())['pads'];pads=[]
 for p in h['pads']:
  obs=poses[p['uuid']];assert obs[1]==p['net'];dx=obs[2]/1e6-p['x'];dy=obs[3]/1e6-p['y']
  # Only two rectangular 0603 footprints have moved; their bounding boxes
  # remain conservative under the explicitly attested 180-degree root pose.
  if dx or dy:assert p['ref']in('R10007','R10016')
  shapes=[]
  if LY in obs[4]:
   for s in L.poly(p['layers'].get(LY,[])):
    shapes.append(translate(box(*s.bounds),xoff=dx,yoff=dy)if dx or dy else s)
  pads.append((p,obs,shapes))
 endpoint_uids={'b9498a68-8287-4605-bbaf-8f732d69f2f0', '962ffd3a-8436-4a45-bfc0-9f7aa24e2a42'}
 va=e['copper']['b9498a68-8287-4605-bbaf-8f732d69f2f0'];vb=e['copper']['962ffd3a-8436-4a45-bfc0-9f7aa24e2a42']
 assert va['kind']==vb['kind']=='via' and L.norm(va['raw_net'])==L.norm(vb['raw_net'])==NET
 assert va['chunk_sha256']=='1fc74763e60576821b605c51cbacd816baf2df13bea7be6a33a8ca8af8db4f04' and vb['chunk_sha256']=='79668f5e8dcba8e65f5eba24f833de59305f052327609db97dbcb211c684d4f1'
 a=[v/1e6 for v in va['at_IU']];end=[v/1e6 for v in vb['at_IU']]
 assert a==[95.15, 50.25] and end==[98.75, 42.75]
 left=({'net':va['raw_net']},None,None)
 roi=box(min(a[0],end[0])-12,min(a[1],end[1])-12,max(a[0],end[0])+12,max(a[1],end[1])+12)
 dom=h['domains_normalized'];gap=lambda n:.15 if dom.get(L.norm(n))==dom[NET]else .6
 records=[]
 def add(uid,net,kind,s,extra=0.,local=0.):
  if L.norm(net)==NET or not s.intersects(roi):return
  clear=max(gap(net),local)+.025+extra;records.append({'UUID':uid,'raw_net':net,'kind':kind,'shape':s,'clear':clear,'cut':Z.bounded_buffer(s,.1+clear)})
 holes=[]
 for uid,t in e['copper'].items():
  if t['kind']=='via':
   x,y=[z/1e6 for z in t['at_IU']];radius=t['diameters_IU'][LY]/2e6;add(uid,t['raw_net'],'current_integer_native_via',Point(x,y).buffer(radius,quad_segs=128))
   holes.append((uid,Point(x,y).buffer(t['drill_IU']/2e6,quad_segs=128)))
  elif t['layer']==LY:
   assert t['kind']=='segment';aa=[z/1e6 for z in t['start_IU']];bb=[z/1e6 for z in t['end_IU']];add(uid,t['raw_net'],'current_integer_native_track',LineString([aa,bb]).buffer(t['width_IU']/2e6,quad_segs=128))
 for p,obs,shapes in pads:
  for s in shapes:add(p['uuid'],p['net'],'current_native_pose_pad',s,.005)
  for s in L.poly(p.get('hole')or[]):
   holes.append((p['uuid'],s))
 native=json.loads((N.R157/'actual-full-refill-geometry.json').read_bytes())
 for z in native['zones']:
  for s in L.poly(N.O.polys(z['fills'].get(LY,[]))):add(z['uuid'],z['net'],'FULL_before_surface_fill_hard',s,0.,float(z['clearance_mm']))
 cuts=[r['cut']for r in records]
 for uid,s in holes:
  if uid not in endpoint_uids and s.intersects(roi):cuts.append(Z.bounded_buffer(s,.1+.275+.005))
 reserve,exempt=K.A.reservations()
 for rules,isreserve in ((h['rule_areas'],False),(reserve['keepouts'],True)):
  for r in rules:
   if LY not in r['layers']or(isreserve and NET in exempt.get(r['name'],set()))or(not isreserve and not r.get('no_tracks')):continue
   for s in L.poly(r['outline']):
    if s.intersects(roi):cuts.append(Z.bounded_buffer(s,.125))
 forbidden=unary_union(cuts);board=unary_union(L.poly(h['outline'])).buffer(-.625);attempts=[];accepted=[]
 gp=H/'field-power/R753-actual-FULL-before-FULL-after-independent-source-contact-reference-r763/actual-full-R157-before-all-net-groups.pkl'
 assert sha(gp)=='d808a9bbe54bb24d6232baf4bddddb260db7a82a891c6b50ca6355ed79e6482a'
 groups=pickle.loads(gp.read_bytes());lg=[n for n in groups if L.norm(n)=='/LOGIC_GND'];assert len(lg)==1;ground=K.root(groups[lg[0]],'J11001','2')
 ref=unary_union([q['shape'].intersection(roi)for q in ground if q['kind']=='fill'and q['layer']=='In4.Cu'and q['shape'].intersects(roi)])
 caps=[]
 for uid in endpoint_uids:
  v=e['copper'][uid];radius=v['diameters_IU'][LY]/2e6+.275;caps.append(Point([z/1e6 for z in v['at_IU']]).buffer(radius,quad_segs=256))
 reference_with_ONLY_TWO_inscribed_owncaps=unary_union([ref,*caps]);reference_axis=reference_with_ONLY_TWO_inscribed_owncaps.buffer(-.10002)

 for expansion in(2.,5.,10.):
  window=box(min(a[0],end[0])-expansion,min(a[1],end[1])-expansion,max(a[0],end[0])+expansion,max(a[1],end[1])+expansion);free=window.intersection(board).difference(forbidden).intersection(reference_axis);path=None;search=None
  for face in K.RF.parts(free):
   if face.covers(Point(a))and face.covers(Point(end)):path,search=T.route(face,a,end);break
  if path is None:attempts.append({'expansion_mm':expansion,'physical_AND_actual_BEFORE_source_compatible_no_path_in_this_window':True,'start_free':free.covers(Point(a)),'end_free':free.covers(Point(end))});continue
  path=[[round(x,6),round(y,6)]for x,y in path];body=Z.bounded_buffer(LineString(path),.1);errors=[]
  outside=body.difference(reference_with_ONLY_TWO_inscribed_owncaps)
  if not outside.is_empty:errors.append({'kind':'literal_full_BEFORE_SOURCE_plus_ONLY_TWO_owned_terminal_caps','gap':ds(outside)})

  for r in records:
   if body.distance(r['shape'])<r['clear']:errors.append({k:r[k]for k in('UUID','raw_net','kind','clear')}|{'actual_conservative_gap':body.distance(r['shape'])})
  for uid,s in holes:
   if uid not in endpoint_uids and body.distance(s)<.280:errors.append({'kind':'all_foreign_drill_guard','UUID':uid,'actual_gap':body.distance(s)})
  tracks=[{'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'R315-existing-In3/2/'+str(i))),'net':left[0]['net'],'layer':LY,'w':.2,'a':aa,'b':bb,'locked':False}for i,(aa,bb)in enumerate(zip(path,path[1:]))]
  row={'expansion_mm':expansion,'path':path,'length_mm':LineString(path).length,'true_conservative_Cu_hole_guard_errors':errors,'route_method':search,'whole_body_reference_on_AFTER_actual_J3_In4':'PENDING_FULL_NATIVE_MATCHED_STATE_NO_CAP_OR_SOURCE_WAIVER'};attempts.append(row)
  if not errors:accepted.append({'tracks':tracks,'whole_body_WKB':body.wkb,'current_stage_SHA256':e['board_sha256'],'source_reference_REQUIRED':'actual J11001.2 LG SOURCE In4; exact own two OLD terminal cap and finite transfer plus existing return gates OPEN','no_vias':True,'current_SOURCE_full_body_oldref_native_DRC_SI':'OPEN'});break
 packet=OUT/'only-new-SDO-B-tracks-physical-nominee-NOT_MODEL.pkl';packet.write_bytes(pickle.dumps(accepted,protocol=5));put('bounded-current-route-attempts.json',attempts);put('receipt.json',{'status':'CURRENT_R753_SDO_B_PHYSICAL_NOMINEE_ALL_SOURCE_REFERENCE_GATES_OPEN'if accepted else'CURRENT_R753_SDO_B_BOUNDED_NO_PHYSICAL_NOMINEE','candidate_stage_SHA256':e['board_sha256'],'current_exact_Cu_ledger_SHA256':sha(ep),'actual_native_pad_pose_SHA256':sha(pp),'native_full_before_geometry_SHA256':sha(N.R157/'actual-full-refill-geometry.json'),'nominee_count':len(accepted),'packet_SHA256':sha(packet),'surface_foreign_old_native_fills_hard_no_carve':True,'all_current_discrete_Cu_holes_and_rules_hard':True,'future_full_native_LG_In4_SOURCE_fullbody_reference_not_credited':True,'current_LG_and_original_plane_profile_interactions':'OPEN_NATIVE_R299_SOURCE_REFERENCE_REQUIRED','no_vias_no_old_Cu_removed':True,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started});print('R315_PAIR_DONE',len(accepted),sha(OUT/'receipt.json'),flush=True)
if __name__=='__main__':main()
