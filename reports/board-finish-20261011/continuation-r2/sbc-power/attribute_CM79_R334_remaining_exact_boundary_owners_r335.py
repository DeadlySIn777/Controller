"""Read-only exact free-component boundary attribution, no routing waiver."""
import hashlib,json,pickle,sys,time,traceback,collections
from pathlib import Path
from shapely import from_wkb,set_precision
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
import physical_reference_losses_r3_zero_r208 as RF
O=H/'sbc-power/CM79-R334-exact-remaining-boundary-owner-counterfactual-attribution-r335'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def buf(s,r):return zero(Z.bounded_buffer(s,r))
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();r=H/'sbc-power/CM79-exact-R333-owned-q4f-only-local-coupled-In2-corridor-nominations-r334';assert sha(r/'receipt.json')=='5f5ddabf01c07d4b72d44a4f7ff321e0babff70db33db681da9d0732e4c49961';mp=H/'sbc-power/CM-sparse-exact-current-R543-TMR-repaired-only-new-role-withdrawal-inherited-fills-FAIL-r333/model.pkl';assert sha(mp)=='f9df66060a0f45959c4234f698500070c1ba2b4837894eee644cec36891dce9b';g,h,b,q,c=pickle.loads(mp.read_bytes());NET='/mc_local_power/CORE_5V';dom=h['domains_normalized'];gap=lambda n:.15 if dom.get(L.norm(n))==dom[NET]else .6;region=box(104,158,144,214);wide=region.buffer(3);corridor=box(116,169,139,208);free=zero(from_wkb((r/'exact-full1p25-In2-centre-free-native-fill-retreat-pending.wkb').read_bytes()));target=zero(from_wkb((r/'actual-source-rooted-In2-spatial-target.wkb').read_bytes()));faces=RF.parts(free);pt=Point(123.560945,206.750243);startFace=next(face for face in faces if face.covers(pt));sourceFaces=[face for face in faces if not face.intersection(buf(target,.624995)).is_empty];assert sourceFaces;bridges=[]
 for i,face in enumerate(sourceFaces):
  aa,bb=nearest_points(startFace,face);line=LineString([aa,bb]);bridges.append({'source_component_index':i,'distance_mm':line.length,'axis_mm':[list(aa.coords[0]),list(bb.coords[0])],'shape':line,'source_component_bounds_mm':list(face.bounds)})
 bridges.sort(key=lambda x:x['distance_mm']);chosen=bridges[0];(O/'exact-nearest-reachable-to-source-component-axis.wkb').write_bytes(chosen['shape'].wkb);put(O/'exact-reachable-and-source-component-authority.json',{'R334_receipt_sha256':sha(r/'receipt.json'),'R333_model_sha256':sha(mp),'frozen_free_WKB_sha256':sha(r/'exact-full1p25-In2-centre-free-native-fill-retreat-pending.wkb'),'start_axis_endpoint_mm':list(pt.coords[0]),'actual_start_component_bounds_mm':list(startFace.bounds),'source_component_count':len(sourceFaces),'nearest_component_axes':[{k:v for k,v in x.items()if k!='shape'}for x in bridges],'no_actual_Cu_or_source_acceptance_from_counterfactuals':True})
 records,trees=F.build({**c,'zones':[]});obs=[]
 def add(key,shape,meta):obs.append({'key':key,'shape':shape,**meta})
 for j in trees['In2.Cu'].query(wide,predicate='intersects'):
  rr=records['In2.Cu'][int(j)]
  if L.norm(rr['net'])==NET:continue
  req=gap(rr['net'])+.025003
  if rr['kind']=='track'and not rr['source'].get('m'):tt=rr['source'];base=LineString([tt['a'],tt['b']]);rad=tt['w']/2
  elif rr['kind']=='via':vv=rr['source'];base=Point(vv['x'],vv['y']);rad=vv['d']/2
  else:base=rr['shape'];rad=0
  add('discrete:'+rr['uuid'],buf(base,rad+.625+req),{'kind':'actual_native_or_owned_discrete_Cu','UUID':rr['uuid'],'raw_net':rr['net'],'source_kind':rr['kind'],'native_clearance_mm':gap(rr['net']),'planner_reserve_mm':.025,'original_actual_shape_bounds_mm':list(rr['shape'].bounds)})
 for z in q:
  if z['layer']!='In2.Cu'or L.norm(z['net'])==NET or not z['shape'].intersects(wide):continue
  req=max(gap(z['net']),float(z['clearance_mm']))+.025003;shape=zero(z['shape']).difference(corridor)if z['uuid']=='4f297f78-8d11-5be4-910e-9245f73fa249'else zero(z['shape']);assert .625+req<3;add('owned_q:'+z['uuid'],buf(shape.intersection(wide),.625+req),{'kind':'owned_positive_role_q4f_only_soft_in_exact_R334_corridor','UUID':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'physical_before_WKB_sha256':hashlib.sha256(z['shape'].wkb).hexdigest(),'physical_before_bounds_mm':list(z['shape'].bounds),'normal_new_track_guard_radius_mm':.625+req})
 for v in h['vias']:
  if L.norm(v['net'])==NET:continue
  sh=Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)
  if sh.intersects(wide):add('discrete:'+v['uuid'],buf(sh,.905003),{'kind':'actual_old_foreign_drill','UUID':v['uuid'],'raw_net':v['net'],'drill_mm':v['drill'],'hole_to_new_Cu_guard_mm':.280003})
 for p in h['pads']:
  if L.norm(p['net'])==NET:continue
  for sh in L.poly(p.get('hole')or[]):
   if sh.intersects(wide):add('discrete:'+p['uuid'],buf(sh,.905003),{'kind':'actual_old_foreign_PTH_or_NPTH_drill','UUID':p['uuid'],'raw_net':p['net'],'reference':p['ref'],'pin':p['num']})
 reserve,exempt=A.reservations()
 for rules,ex in((h['rule_areas'],False),(reserve['keepouts'],True)):
  for rr in rules:
   if'In2.Cu'not in rr['layers']or(ex and NET in exempt.get(rr['name'],set()))or(not ex and not rr.get('no_tracks')):continue
   for sh in L.poly(rr['outline']):
    if sh.intersects(wide):add('rule:'+rr.get('name',rr.get('uuid')),buf(sh,.650003),{'kind':'native_or_frozen_no_new_Cu_rule','name':rr.get('name',rr.get('uuid')),'actual_outline_bounds_mm':list(sh.bounds)})
 boundary=buf(chosen['shape'],.00000001);selected=[x for x in obs if x['shape'].intersects(boundary)];put(O/'exact-nearest-source-component-boundary-owners.json',[{k:v for k,v in x.items()if k!='shape'}for x in selected]);by=collections.defaultdict(list)
 for x in obs:by[x['key']].append(x['shape'])
 board=zero(unary_union(L.poly(h['outline'])));base=region.intersection(board.buffer(-1.150003));rebuilt=base.difference(unary_union([x['shape']for x in obs]));(O/'literal-rebuilt-minus-frozen-free.wkb').write_bytes(rebuilt.difference(free).wkb);(O/'literal-frozen-minus-rebuilt-free.wkb').write_bytes(free.difference(rebuilt).wkb);assert rebuilt.difference(free).is_empty and free.difference(rebuilt).is_empty
 # Each probe is explicitly a counterfactual owner attribution. It deletes
 # neither source Cu nor a rule and emits no path/model or routing approval.
 keys=list(dict.fromkeys([x['key']for x in selected]+['owned_q:4f297f78-8d11-5be4-910e-9245f73fa249']));tests=[]
 for key in keys:
  probe=base.difference(unary_union([x['shape']for x in obs if x['key']!=key]));cf=[face for face in RF.parts(probe)if face.covers(pt)];touch=any(not face.intersection(buf(target,.624995)).is_empty for face in cf);row={'counterfactual_omitted_owner_key':key,'only_attribution_no_delete_or_waiver':True,'reachable_component_count':len(cf),'hypothetical_actual_source_touch':touch,'hypothetical_reachable_source_distance_mm':min((face.distance(target)for face in cf),default=None)};tests.append(row);print('R335_OWNER',key,touch,row['hypothetical_reachable_source_distance_mm'],flush=True)
 put(O/'exact-single-owner-topology-counterfactuals-NOT_ROUTING_APPROVAL.json',tests);put(O/'receipt.json',{'verdict':'EXACT_BOUNDARY_OWNER_ATTRIBUTION_ONLY_NO_SOURCE_OR_CU_ACCEPTANCE','R333_model_sha256':sha(mp),'R334_receipt_sha256':sha(r/'receipt.json'),'nearest_component_gap_mm':chosen['distance_mm'],'named_nearest_boundary_owner_count':len(set(x['key']for x in selected)),'single_owner_counterfactual_count':len(tests),'q4f_only_omission_hypothetically_connects_source':next(x['hypothetical_actual_source_touch']for x in tests if x['counterfactual_omitted_owner_key'].startswith('owned_q:4f297')),'original_native_IO354921_boundary_TMR_FAIL_separate_unchanged':True,'original_Cu_holes_native_definitions_rules_current_reference_gates_not_modified_or_waived':True,'emitted_positive_Cu_or_model':False,'native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R335_COMPLETE',sha(O/'receipt.json'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
