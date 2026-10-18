"""Finite full-width In2 actual-source route nomination; no board/model mutation."""
import hashlib,json,pickle,sys,time,math,traceback
from pathlib import Path
from shapely.geometry import Point,LineString,box
from shapely.ops import unary_union,nearest_points
from shapely import set_precision
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in ('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import guarded_power_projection_r44 as Z
import physical_reference_losses_r3_zero_r208 as RF
import tri_route as TR
O=H/'sbc-power/CM79-exact-R333-q4f-q053-only-local-coupled-In2-corridor-nominations-source-embed100um-r337'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def buf(s,r):return zero(Z.bounded_buffer(s,r))
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();(O/'exact-expanded-coupled-local-nomination.py').write_text(s,encoding='utf-8')
 mp=H/'sbc-power/CM-sparse-exact-current-R543-TMR-repaired-only-new-role-withdrawal-inherited-fills-FAIL-r333/model.pkl';assert sha(mp)=='f9df66060a0f45959c4234f698500070c1ba2b4837894eee644cec36891dce9b';g,h,b,q,c=pickle.loads(mp.read_bytes());old=next(t for t in h['tracks']if t['uuid']=='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1');NET=L.norm(old['net']);dom=h['domains_normalized'];gap=lambda n:.15 if dom.get(L.norm(n))==dom[NET]else .6
 nd=H/'sbc-power/CM79-larger-ordinary-external-right-power-port-native-and-source-mask-screen-r325';assert sha(nd/'receipt.json')=='40723136d7cfeceaa248db243f8cfff953ce686079dce114244395a404a0255c';nom=json.loads((nd/'only-qualified-larger-right-spur-power-port-nominees.json').read_text());nom=sorted(nom,key=lambda r:(-r['screen']['diameter_drill_mm'][0],r['screen']['right_spur_index']));topo=H/'sbc-power/CM79-original-CORE5-native-alternate-path-no-new-hole-topology-r319';assert sha(topo/'receipt.json')=='8bac0960b658176645c9a33842d26913c266d4fdd1cb9aa1a36ce8676457efc1';pre={**old,'uuid':'f7a6a4fe-1e2d-50cd-9d1d-122217cb4016','b':[116.2,202.35]};post={**old,'uuid':'f0009ae2-77c0-524e-a9c6-efbe8de46b7a','a':[120.1,202.35]};provisional={**c,'tracks':[t for t in c['tracks']if t['uuid']!=old['uuid']]+[pre,post]};cacheDir=H/'sbc-power/CM79-exact-R333-owned-q4f-only-local-coupled-In2-corridor-nominations-r334';assert sha(cacheDir/'receipt.json')=='5f5ddabf01c07d4b72d44a4f7ff321e0babff70db33db681da9d0732e4c49961';assert sha(cacheDir/'fresh-actual-CORE5-only-original-middle-withdrawal-groups.pkl')=='7fb5124a8a5fdac9785c7cb1a97b3bc279ffb54399d092e6b9bf5ee3aba2e32b';assert sha(cacheDir/'fresh-actual-R333-LOGIC-ground-groups.pkl')=='cbc0fb58b2764761ae7febe4921081ed3492789c272bf5fc70e35ed337c7aba7';groups=pickle.loads((cacheDir/'fresh-actual-CORE5-only-original-middle-withdrawal-groups.pkl').read_bytes());source=K.root(groups,'R11022','2');(O/'fresh-actual-CORE5-only-original-middle-withdrawal-groups.pkl').write_bytes(pickle.dumps(groups,protocol=5));print('R337_BOUND_BEFORE_CORE5_SOURCE',len(K.keys(source)),flush=True);lgGroups=pickle.loads((cacheDir/'fresh-actual-R333-LOGIC-ground-groups.pkl').read_bytes());lgSource=K.root(lgGroups,'J11001','2');(O/'fresh-actual-R333-LOGIC-ground-groups.pkl').write_bytes(pickle.dumps(lgGroups,protocol=5));lgKeys=K.keys(lgSource);cmPads=[p for p in h['pads']if p['ref']in('J15001','J15002')and p['net']=='/LOGIC_GND'];cmStatus=[{'reference':p['ref'],'pin':p['num'],'UUID':p['uuid'],'source_rooted_actual':any(('pad',p['uuid'],ly)in lgKeys for ly in p['layers'])}for p in cmPads];assert len(cmStatus)==51;put(O/'fresh-R333-CM51-actual-source-status.json',cmStatus);print('R337_BOUND_BEFORE_CM_SOURCE',sum(x['source_rooted_actual']for x in cmStatus),51,flush=True);pairProof={}
 for candidate in nom:
  port=candidate['fullwidth_spur']['exact_existing_source_LG_port']['via'];uid=port['uuid']
  if uid in pairProof:continue
  assert any(v==port for v in h['vias']);rows=[r for r in lgSource if r['kind']=='via'and r['uuid']==uid];contacts={}
  for ly in ('In1.Cu','In4.Cu'):
   ann=zero(unary_union([r['shape']for r in rows if r['layer']==ly]));fills=[r['shape']for r in lgSource if r['kind']=='fill'and r['layer']==ly and r['shape'].envelope.intersects(ann.envelope)];contacts[ly]=ann.intersection(unary_union(fills)).area
  pairProof[uid]={'actual_current_R333_source_rooted_layers':sorted(set(r['layer']for r in rows)),'actual_current_R333_source_fill_contact_mm2':contacts,'both_actual_In1_In4_finite_source_contacts':all(x>0 for x in contacts.values()),'prospective_owned_CM49_native_flash_masks':'OPEN'};assert pairProof[uid]['both_actual_In1_In4_finite_source_contacts']
 put(O/'fresh-actual-R333-existing-LG-power-pair-source-authority.json',pairProof)
 # Native foreign fill is deliberately excluded from the hard free-space
 # obstacle set. Any actual normal retreat still needs a separate strict
 # no-gain/contact/source/reference ledger after construction.
 region=box(104,158,144,214);wide=region.buffer(3);corridor=box(116,169,139,208);q4f=next(z for z in q if z['uuid']=='4f297f78-8d11-5be4-910e-9245f73fa249');q053=next(z for z in q if z['uuid']=='053e747d-d229-5488-b123-0bd7612fb8ef');assert hashlib.sha256(q053['shape'].wkb).hexdigest()=='f1c8dff8cb02f72d2893bdacdce7f2d3d7a4c1a7606eb8dc064c27c3769c6524';fieldSigned=H/'field-signed-port-allocation-r4/receipt.json';assert sha(fieldSigned)=='e49fc7f958f264e552843ca43d1271dd84321dbcd52e27e2460155b2e635bb27';put(O/'exact-current-two-owned-before-role-and-signed-FB-authority.json',{'model_R333_sha256':sha(mp),'unchanged_before_physical_CORE5_and_LG_cache_R334_receipt_sha256':sha(cacheDir/'receipt.json'),'cache_reuse_requires_exact_unchanged_R333_model_and_only_original_middle_topology':True,'field_signed146_term_receipt_sha256':sha(fieldSigned),'FB_signed_full_ground_A':4.76859682896,'FB_positive_load_A':4.85896349563,'FB_buck_negative_CURRENT_A':-.09036666667,'saved_FA_FB24_and_return_budget_V':.48,'FIELD5_qualified_drop_budget':'OPEN','no_equal_sharing_current_capacity_or_derating_credit':True,'two_owned_before_roles':[{'UUID':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'physical_WKB_sha256':hashlib.sha256(z['shape'].wkb).hexdigest(),'intended_WKB_sha256':hashlib.sha256(z['zone_outline_shape'].wkb).hexdigest(),'settings':{k:z[k]for k in('net','layer','priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')}}for z in(q4f,q053)],'only_soft_coupled_scope_mm':[116,169,139,208],'postcut_all_FB_FG_LG_direct_source_oldref_current_loop_mesh_native':'OPEN'});put(O/'exact-TMR-repaired-q4f-current-before-and-coupled-corridor-authority.json',{'exact_R333_model_sha256':sha(mp),'exact_field_R519_sparse_contract_sha256':sha(H/'field-power/FA-IO3-native-TMR-exact-two-zone-sparse-rebase-contract-r519/receipt.json'),'owned_q4f_before_physical_WKB_sha256':hashlib.sha256(q4f['shape'].wkb).hexdigest(),'owned_q4f_before_intended_WKB_sha256':hashlib.sha256(q4f['zone_outline_shape'].wkb).hexdigest(),'all_nine_settings':{k:q4f[k]for k in('net','layer','priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')},'only_soft_owned_scope_mm':[116,169,139,208],'TMR_triangle_corridor_scope_hard_unchanged_mm':[324,119,348,134],'original_native_IO3_54921_area_zero_TMR_nozone_FAIL_distinct_untouched':True,'coupled_local_cut_not_yet_constructed':'OPEN'});(O/'only-nominated-owned-q4f-soft-corridor-authority.wkb').write_bytes(corridor.wkb);target=zero(unary_union([r['shape'].intersection(region)for r in source if r['layer']=='In2.Cu'and r['shape'].intersects(region)]));assert not target.is_empty;(O/'actual-source-rooted-In2-spatial-target.wkb').write_bytes(target.wkb)
 targetLedger=[{'kind':r['kind'],'UUID':r['uuid'],'layer':r['layer'],'shape_WKB_sha256':hashlib.sha256(r['shape'].wkb).hexdigest(),'area_mm2':r['shape'].area}for r in source if r['layer']=='In2.Cu'and r['shape'].intersects(region)];put(O/'actual-native-source-spatial-target-authority.json',{'R319_receipt_sha256':sha(topo/'receipt.json'),'actual_root_selector':['R11022','2'],'actual_root_group_layer_keys':len(K.keys(source)),'target_literal_WKB_sha256':sha(O/'actual-source-rooted-In2-spatial-target.wkb'),'real_physical_target_rows':targetLedger,'nominal_net_identity_is_not_a_source_path':True})
 records,trees=F.build({**c,'zones':[]});obstacles=[];ledger=[]
 for j in trees['In2.Cu'].query(wide,predicate='intersects'):
  r=records['In2.Cu'][int(j)]
  if L.norm(r['net'])==NET:continue
  req=gap(r['net'])+.025003
  if r['kind']=='track'and not r['source'].get('m'):t=r['source'];base=LineString([t['a'],t['b']]);radius=t['w']/2
  elif r['kind']=='via':v=r['source'];base=Point(v['x'],v['y']);radius=v['d']/2
  else:base=r['shape'];radius=0
  obstacles.append(buf(base,radius+.625+req));ledger.append({'kind':r['kind'],'UUID':r['uuid'],'raw_net':r['net'],'hard_layer':'In2.Cu','native_domain_clearance_mm':gap(r['net']),'new_Cu_planner_reserve_mm':.025})
 for z in q:
  if z['layer']!='In2.Cu'or L.norm(z['net'])==NET or not z['shape'].intersects(wide):continue
  req=max(gap(z['net']),float(z['clearance_mm']))+.025003;hardShape=zero(z['shape']).difference(corridor)if z['uuid']in(q4f['uuid'],q053['uuid'])else zero(z['shape']);assert .625+req<3;obstacles.append(buf(hardShape.intersection(wide),.625+req));ledger.append({'kind':'existing_owned_positive_q_hard_except_exact_q4f_q053_declared_local_coupled_scope','UUID':z['uuid'],'raw_net':z['net'],'native_domain_or_plane_local_mm':max(gap(z['net']),float(z['clearance_mm'])),'new_Cu_planner_reserve_mm':.025})
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
   if 'In2.Cu'not in r['layers']or(ex and NET in exempt.get(r['name'],set()))or(not ex and not r.get('no_tracks')):continue
   for sh in L.poly(r['outline']):
    if sh.intersects(wide):obstacles.append(buf(sh,.650003));ledger.append({'kind':'native_or_frozen_no_new_Cu_rule','name':r.get('name',r.get('uuid'))})
 board=zero(unary_union(L.poly(h['outline'])));free=region.intersection(board.buffer(-1.150003)).difference(unary_union(obstacles));(O/'exact-full1p25-In2-centre-free-native-fill-retreat-pending.wkb').write_bytes(free.wkb);put(O/'exact-In2-hard-primitive-owned-positive-hole-rule-obstacles.json',ledger);faces=RF.parts(free);tests=[];accepted=[]
 for row in nom:
  screen=row['screen'];spur=row['fullwidth_spur'];pv=screen['power_xy_mm'];start=spur['fullwidth_spur_side_contact_axis_endpoint_mm'];pt=Point(start);relevant=[face for face in faces if face.covers(pt)];test={'right_spur_index':screen['right_spur_index'],'diameter_drill_mm':screen['diameter_drill_mm'],'power_xy_mm':pv,'side_contact_axis_endpoint_mm':start,'same_free_face_count':len(relevant),'route_to_actual_rooted_In2_source':False}
  for face in relevant:
   available=face.intersection(zero(target.buffer(-.10))).buffer(-.000005)
   if available.is_empty:continue
   end=list(nearest_points(pt,available)[1].coords[0]);path,method=TR.route(face,start,end);path=[[round(x,6),round(y,6)]for x,y in path]
   if not face.covers(LineString(path)):continue
   body=zero(unary_union([buf(LineString([aa,bb]),.625)for aa,bb in zip(path,path[1:])]));tap=body.intersection(target);power=Point(pv);diam,drill=screen['diameter_drill_mm'];ann=buf(power,diam/2).difference(buf(power,drill/2+.00000002));contact=body.intersection(ann)
   if tap.is_empty or tap.area<=0 or contact.is_empty or contact.area<=0 or not target.covers(Point(path[-1]))or Point(path[-1]).distance(target.boundary)<.10:continue
   test.update({'route_to_actual_rooted_In2_source':True,'full1p25_In2_path':path,'full1p25_In2_length_mm':sum(math.dist(aa,bb)for aa,bb in zip(path,path[1:])),'source_Cu_finite_overlap_mm2':tap.area,'endpoint_embedded_in_actual_source_Cu':target.covers(Point(path[-1])),'actual_source_endpoint_boundary_distance_mm':Point(path[-1]).distance(target.boundary),'required_actual_source_embed_depth_mm':.10,'new_power_annulus_to_In2_finite_contact_mm2':contact.area,'route_method':method,'full_new_In2_body_WKB_sha256':hashlib.sha256(body.wkb).hexdigest()});coupledCut=buf(LineString(path),.625+max(float(q4f['clearance_mm']),.15)+.025);localWithdraw=zero(q4f['shape']).intersection(coupledCut);outside=localWithdraw.difference(corridor);assert outside.is_empty,('q4f local coupled nomination outside declared scope',outside.geom_type,outside.area);(O/'only-nominated-q4f-fullwidth-corridor-normal-cutter.wkb').write_bytes(coupledCut.wkb);(O/'only-nominated-q4f-local-physical-withdrawal.wkb').write_bytes(localWithdraw.wkb);test['owned_q4f_only_local_withdrawal_nomination_mm2']=localWithdraw.area;test['owned_q4f_local_withdrawal_outside_declared_corridor_empty']=True;ownedProposals=[]
   for owner in(q4f,q053):
    radius=.625+max(float(owner['clearance_mm']),gap(owner['net']))+.025;normal=buf(LineString(path),radius);rows={}
    for role in('shape','zone_outline_shape'):
     removed=zero(owner[role]).intersection(normal);assert removed.difference(corridor).is_empty,('explicit owned corridor scope',owner['uuid'],role);fn=O/(owner['uuid']+'-'+role+'-only-nominated-normal-negative-intersection.wkb');fn.write_bytes(removed.wkb);rows[role]={'exact_before_WKB_sha256':hashlib.sha256(owner[role].wkb).hexdigest(),'only_nominal_local_removed_mm2':removed.area,'only_nominal_local_removed_type':removed.geom_type,'removed_WKB_file':str(fn.resolve()),'removed_WKB_sha256':sha(fn),'native_minimum_and_local_guard_retained':True,'strict_literal_no_gain_and_local100nm_constructor_proof':'OPEN'}
    fn=O/(owner['uuid']+'-only-nominated-fullwidth-normal-cutter.wkb');fn.write_bytes(normal.wkb);ownedProposals.append({'UUID':owner['uuid'],'raw_net':owner['net'],'layer':owner['layer'],'native_domain_clearance_mm':gap(owner['net']),'native_plane_local_mm':float(owner['clearance_mm']),'planner_reserve_mm':.025,'track_cut_radius_mm':radius,'normal_cutter_file':str(fn.resolve()),'normal_cutter_sha256':sha(fn),'exact_role_nomination':rows,'all_original_source_contact_direct_reference_current_return_loop_mesh_native':'OPEN'})
   put(O/'exact-two-owned-local-normal-cutter-proposals-NO_HEAD_EMITTED.json',ownedProposals);accepted.append({'screen':screen,'fullwidth_F_spur':spur,'In2_nomination':test,'current_existing_LG_pair_source_proof':pairProof[spur['exact_existing_source_LG_port']['via']['uuid']]});(O/('right-'+str(screen['right_spur_index'])+'-diam-'+str(diam)+'-full-new-In2-body.wkb')).write_bytes(body.wkb);print('R337_ROUTE',screen['right_spur_index'],screen['diameter_drill_mm'],test['full1p25_In2_length_mm'],flush=True);break
  tests.append(test);put(O/'finite-eight-port-six-size-actual-source-route-tests.json',tests)
  if accepted:break
 put(O/'only-full1p25-In2-actual-source-route-proposals.json',accepted);put(O/'receipt.json',{'verdict':'EXACT_R333_OWNED_q4f_q053_ONLY_LOCAL_COUPLED_FULL1P25_In2_SOURCE_ROUTE_NOMINATION_ALL_FRESH_GATES_OPEN'if accepted else'FINITE_EXTERNAL_RIGHT_PORT_NO_FULL1P25_In2_ROUTE_TO_ACTUAL_SOURCE_WITH_ALL_OWNED_POSITIVE_HARD','parent_R289_model_sha256':sha(mp),'larger_port_R325_receipt_sha256':sha(nd/'receipt.json'),'actual_source_R319_receipt_sha256':sha(topo/'receipt.json'),'finite_region_mm':[104,158,144,214],'full_new_track_width_mm':1.25,'required_actual_source_endpoint_embed_depth_mm':.10,'near_tangent_R336_source_contact_not_qualified':True,'tested_port_size_combinations':len(tests),'actual_source_nominees':len(accepted),'native_foreign_fill_normal_retreat_only_pending_strict_per_record_contact_source_reference_proof':True,'all_old_discrete_holes_native_rules_and_owned_positive_Cu_hard_except_explicit_local_q4f_q053_coupled_corridor':True,'only_soft_q4f_q053_coupled_scope_mm':[116,169,139,208],'owned_q4f_original_nine_settings_unchanged':True,'original_native_IO354921_TMR_closed_boundary_nozone_FAIL_distinct_retained':True,'IO3_CORE5_ground_old_contacts_source_directrefs_wholebody_loop_current_thermal_native':'OPEN','all49_CM_tracks_vias_hard_unchanged':True,'only_original_fullwidth_F_middle_withdrawal_scope':[[116.2,202.35],[120.1,202.35]],'actual_native_LG_local_clearance_025_unchanged':True,'old_supported_reference_no_ownhole_D4_power_or_aperture_waiver':True,'new_F_In2_fullbody_signed_current_drop_plating_thermal_loop_allold_source_native':'OPEN','signed_CORE5_output_A':7.882034293398379,'signed_SBC_common_branch_A':4.396304643962848,'no_capacity_equalshare_or_derating_inferred':True,'model_source_native_board_adoption_changes':0,'native_jobs':0,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R337_COMPLETE',sha(O/'receipt.json'),len(accepted),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
