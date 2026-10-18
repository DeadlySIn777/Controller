"""Finite full-width In1 actual-source route nomination; no board/model mutation."""
import hashlib,json,pickle,sys,time,math,traceback
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely import set_precision
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
import physical_reference_losses_r3_zero_r208 as RF
import tri_route as TR
O=H/'sbc-power/CM79-external-larger-power-port-full1p25-In1-actual-source-route-nominations-r332'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def buf(s,r):return zero(Z.bounded_buffer(s,r))
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();(O/'exact-expanded-read-only-layer-screen.py').write_text(EXPANDED,encoding='utf-8')
 mp=H/'sbc-power/CM-sparse-exact-current-R393-only-new-role-withdrawal-inherited-fills-FAIL-r289/model.pkl';assert sha(mp)=='a5340075975ddad925b57663d475978eba7f346c3709e93fa6b67064cbf4ccec';g,h,b,q,c=pickle.loads(mp.read_bytes());old=next(t for t in h['tracks']if t['uuid']=='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1');NET=L.norm(old['net']);dom=h['domains_normalized'];gap=lambda n:.15 if dom.get(L.norm(n))==dom[NET]else .6
 nd=H/'sbc-power/CM79-larger-ordinary-external-right-power-port-native-and-source-mask-screen-r325';assert sha(nd/'receipt.json')=='40723136d7cfeceaa248db243f8cfff953ce686079dce114244395a404a0255c';nom=json.loads((nd/'only-qualified-larger-right-spur-power-port-nominees.json').read_text());nom=sorted(nom,key=lambda r:(-r['screen']['diameter_drill_mm'][0],r['screen']['right_spur_index']));topo=H/'sbc-power/CM79-original-CORE5-native-alternate-path-no-new-hole-topology-r319';assert sha(topo/'receipt.json')=='8bac0960b658176645c9a33842d26913c266d4fdd1cb9aa1a36ce8676457efc1';groups=pickle.loads((topo/'actual-CORE5-with-only-native-middle-removed-groups.pkl').read_bytes());source=K.root(groups,'R11022','2');assert len(K.keys(source))==8179
 # Native foreign fill is deliberately excluded from the hard free-space
 # obstacle set. Any actual normal retreat still needs a separate strict
 # no-gain/contact/source/reference ledger after construction.
 region=box(10,145,215,228);wide=region.buffer(3);target=zero(unary_union([r['shape'].intersection(region)for r in source if r['layer']=='In1.Cu'and r['shape'].intersects(region)]));assert not target.is_empty;(O/'actual-source-rooted-In1-spatial-target.wkb').write_bytes(target.wkb)
 targetLedger=[{'kind':r['kind'],'UUID':r['uuid'],'layer':r['layer'],'shape_WKB_sha256':hashlib.sha256(r['shape'].wkb).hexdigest(),'area_mm2':r['shape'].area}for r in source if r['layer']=='In1.Cu'and r['shape'].intersects(region)];put(O/'actual-native-source-spatial-target-authority.json',{'R319_receipt_sha256':sha(topo/'receipt.json'),'actual_root_selector':['R11022','2'],'actual_root_group_layer_keys':len(K.keys(source)),'target_literal_WKB_sha256':sha(O/'actual-source-rooted-In1-spatial-target.wkb'),'real_physical_target_rows':targetLedger,'nominal_net_identity_is_not_a_source_path':True})
 records,trees=F.build({**c,'zones':[]});print('R332_PHASE_NATIVE_ROWS',flush=True);obstacles=[];ledger=[]
 for j in trees['In1.Cu'].query(wide,predicate='intersects'):
  r=records['In1.Cu'][int(j)]
  if L.norm(r['net'])==NET:continue
  req=gap(r['net'])+.025003
  if r['kind']=='track'and not r['source'].get('m'):t=r['source'];base=LineString([t['a'],t['b']]);radius=t['w']/2
  elif r['kind']=='via':v=r['source'];base=Point(v['x'],v['y']);radius=v['d']/2
  else:base=r['shape'];radius=0
  obstacles.append(buf(base,radius+.625+req));ledger.append({'kind':r['kind'],'UUID':r['uuid'],'raw_net':r['net'],'hard_layer':'In1.Cu','native_domain_clearance_mm':gap(r['net']),'new_Cu_planner_reserve_mm':.025})
 for z in q:
  if z['layer']!='In1.Cu'or L.norm(z['net'])==NET or not z['shape'].intersects(wide):continue
  req=max(gap(z['net']),float(z['clearance_mm']))+.025003;assert .625+req<3;obstacles.append(buf(zero(z['shape']).intersection(wide),.625+req));ledger.append({'kind':'existing_owned_positive_q_hard','UUID':z['uuid'],'raw_net':z['net'],'native_domain_or_plane_local_mm':max(gap(z['net']),float(z['clearance_mm'])),'new_Cu_planner_reserve_mm':.025})
 print('R332_PHASE_OWNED_POSITIVE_LOCAL_GUARDS_COMPLETE',flush=True)
 for v in h['vias']:
  if L.norm(v['net'])==NET:continue
  sh=Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128)
  if sh.intersects(wide):obstacles.append(buf(sh,.905003))
 for p in h['pads']:
  if L.norm(p['net'])==NET:continue
  for sh in L.poly(p.get('hole')or[]):
   if sh.intersects(wide):obstacles.append(buf(sh,.905003))
 reserve,exempt=A.reservations()
 for rules,ex in ((h['rule_areas'],False),(reserve['keepouts'],True)):
  for r in rules:
   if 'In1.Cu'not in r['layers']or(ex and NET in exempt.get(r['name'],set()))or(not ex and not r.get('no_tracks')):continue
   for sh in L.poly(r['outline']):
    if sh.intersects(wide):obstacles.append(buf(sh,.650003));ledger.append({'kind':'native_or_frozen_no_new_Cu_rule','name':r.get('name',r.get('uuid'))})
 audit=H/'sbc-power/CM79-R315-fresh-sparse-current-source-native-reference-audit-r316';assert sha(audit/'receipt.json')=='bb93a32c96d7aab3f624152ae916eb52b128b4c899b4bc97e41cf2c2b230c249';beforeGroups=pickle.loads((audit/'actual-drilled-before-groups.pkl').read_bytes());beforeLG=K.root(beforeGroups['/LOGIC_GND'],'J11001','2');mappedLayers=('F.Cu','In2.Cu');ref=zero(K.source_refs(beforeLG)['F.Cu']).intersection(wide);supported=[]
 for t in c['tracks']:
  if t['layer']not in mappedLayers or dom.get(L.norm(t['net']))!=dom['/LOGIC_GND']:continue
  bodies=[zero(L.body({**t,'a':aa,'b':bb}))for aa,bb in((old['a'],[116.2,202.35]),([120.1,202.35],old['b']))]if t['uuid']==old['uuid']else[zero(L.body(t))]
  for body in bodies:
   if not body.envelope.intersects(wide):continue
   support=body.intersection(ref)
   if support.is_empty:continue
   obstacles.append(buf(support,.900003));supported.append({'old_UUID':t['uuid'],'layer':t['layer'],'kind':'exact_BEFORE_supported_whole_old_track_body_all_dimensions_hard','supported_WKB_sha256':hashlib.sha256(support.wkb).hexdigest(),'actual_native_LG_track_antipad_mm':.900})
 for z in q:
  if z['layer']not in mappedLayers or dom.get(L.norm(z['net']))!=dom['/LOGIC_GND']or not z['shape'].intersects(wide):continue
  support=zero(z['shape']).intersection(ref)
  if support.is_empty:continue
  obstacles.append(buf(support,.900003));supported.append({'old_UUID':z['uuid'],'layer':z['layer'],'kind':'exact_BEFORE_supported_DC_body_no_shadow_over_missing_before','supported_WKB_sha256':hashlib.sha256(support.wkb).hexdigest(),'actual_native_LG_track_antipad_mm':.900})
 print('R332_PHASE_EXACT_SOURCE_SUPPORTED_MASK_COMPLETE',flush=True);put(O/'exact-source-bank-old-reference-hard-mask-ledger.json',{'before_actual_source_audit_receipt_sha256':sha(audit/'receipt.json'),'mapped_old_layers':mappedLayers,'actual_native_LG_local_clearance_mm':.25,'new_fullwidth_track_antipad_radius_mm':.9,'every_old_supported_track_or_DC_body_no_ownhole_or_dimension_waiver':supported})
 board=zero(unary_union(L.poly(h['outline'])));free=region.intersection(board.buffer(-1.150003)).difference(unary_union(obstacles));(O/'exact-full1p25-In1-centre-free-native-fill-retreat-pending.wkb').write_bytes(free.wkb);put(O/'exact-In1-hard-primitive-owned-positive-hole-rule-obstacles.json',ledger);faces=RF.parts(free);put(O/'exact-plus3mm-spatial-broadphase-authority.json',{'region_plus_margin_mm':3,'maximum_owned_positive_obstacle_radius_mm':1.250003,'maximum_source_supported_reference_obstacle_radius_mm':.900003,'all_omitted_remote_geometry_is_disjoint_every_candidate_guard':'EXACT_SPATIAL_SCOPE','every_final_whole_original_body_source_reference_gate':'OPEN_NOT_WAIVED','no_original_WKB_or_model_bytes_changed':True});tests=[];accepted=[]
 for row in nom:
  screen=row['screen'];spur=row['fullwidth_spur'];pv=screen['power_xy_mm'];start=spur['fullwidth_spur_side_contact_axis_endpoint_mm'];pt=Point(start);relevant=[face for face in faces if face.covers(pt)];test={'right_spur_index':screen['right_spur_index'],'diameter_drill_mm':screen['diameter_drill_mm'],'power_xy_mm':pv,'side_contact_axis_endpoint_mm':start,'same_free_face_count':len(relevant),'route_to_actual_rooted_In1_source':False}
  for face in relevant:
   available=face.intersection(buf(target,.624995)).buffer(-.000005)
   if available.is_empty:continue
   end=list(nearest_points(pt,available)[1].coords[0]);path,method=TR.route(face,start,end);path=[[round(x,6),round(y,6)]for x,y in path]
   if not face.covers(LineString(path)):continue
   body=zero(unary_union([buf(LineString([aa,bb]),.625)for aa,bb in zip(path,path[1:])]));tap=body.intersection(target);power=Point(pv);diam,drill=screen['diameter_drill_mm'];ann=buf(power,diam/2).difference(buf(power,drill/2+.00000002));contact=body.intersection(ann)
   if tap.is_empty or tap.area<=0 or contact.is_empty or contact.area<=0:continue
   test.update({'route_to_actual_rooted_In1_source':True,'full1p25_In1_path':path,'full1p25_In1_length_mm':sum(math.dist(aa,bb)for aa,bb in zip(path,path[1:])),'source_Cu_finite_overlap_mm2':tap.area,'new_power_annulus_to_In1_finite_contact_mm2':contact.area,'route_method':method,'full_new_In1_body_WKB_sha256':hashlib.sha256(body.wkb).hexdigest()});accepted.append({'screen':screen,'fullwidth_F_spur':spur,'In1_nomination':test});(O/('right-'+str(screen['right_spur_index'])+'-diam-'+str(diam)+'-full-new-In1-body.wkb')).write_bytes(body.wkb);print('R332_ROUTE',screen['right_spur_index'],screen['diameter_drill_mm'],test['full1p25_In1_length_mm'],flush=True);break
  tests.append(test);put(O/'finite-eight-port-six-size-actual-source-route-tests.json',tests)
  if accepted:break
 put(O/'only-full1p25-In1-actual-source-route-proposals.json',accepted);put(O/'receipt.json',{'verdict':'FULL1P25_In1_ACTUAL_SOURCE_ROUTE_NOMINATION_ALL_FRESH_GATES_OPEN'if accepted else'FINITE_EXTERNAL_RIGHT_PORT_NO_FULL1P25_In1_ROUTE_TO_ACTUAL_SOURCE_WITH_ALL_OWNED_POSITIVE_HARD','parent_R289_model_sha256':sha(mp),'larger_port_R325_receipt_sha256':sha(nd/'receipt.json'),'actual_source_R319_receipt_sha256':sha(topo/'receipt.json'),'finite_region_mm':[10,145,215,228],'full_new_track_width_mm':1.25,'tested_port_size_combinations':len(tests),'actual_source_nominees':len(accepted),'native_foreign_fill_normal_retreat_only_pending_strict_per_record_contact_source_reference_proof':True,'all_old_discrete_holes_native_rules_and_owned_positive_Cu_hard':True,'all49_CM_tracks_vias_hard_unchanged':True,'only_original_fullwidth_F_middle_withdrawal_scope':[[116.2,202.35],[120.1,202.35]],'actual_native_LG_local_clearance_025_unchanged':True,'old_supported_reference_no_ownhole_D4_power_or_aperture_waiver':True,'new_F_In1_fullbody_signed_current_drop_plating_thermal_loop_allold_source_native':'OPEN','signed_CORE5_output_A':7.882034293398379,'signed_SBC_common_branch_A':4.396304643962848,'no_capacity_equalshare_or_derating_inferred':True,'model_source_native_board_adoption_changes':0,'native_jobs':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R332_COMPLETE',sha(O/'receipt.json'),len(accepted),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
