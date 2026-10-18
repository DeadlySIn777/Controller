"""Sparse CM routes/normal antipads on exact R364; all inherited FAILs retained.

No old filled-array/model overlay. Every generated role has exact bound grid
metadata replay, canonical new vertices, literal zero-grid strict withdrawal,
and explicit local100nm reserve receipts for any positive operation residue.
"""
import copy,hashlib,json,pickle,sys,traceback,time,uuid,math
from pathlib import Path
from shapely import set_precision,get_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import guarded_power_projection_r44 as Z
import restore_field_current_mixed_precision_states_r366 as PS
import immutable_local_fill_subtraction_r254 as IM
import physical_reference_losses_r3_zero_r208 as RF
import audit_aux_exact_raw as A
O=H/'sbc-power/CM79-exact-R333-larger-power-port-local-q053-sparse-current-diagnostic-r338'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def zero(s):a=set_precision(s,0);assert a.wkb==s.wkb;return a
def save(name,s):f=O/(name+'.wkb');f.write_bytes(s.wkb);return {'file':str(f.resolve()),'sha256':sha(f),'area_mm2':s.area,'empty':s.is_empty}
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();(O/'exact-expanded-sparse-constructor.py').write_text(s,encoding='utf-8');(O/'exact-expanded-constructor.py').write_text(s,encoding='utf-8');mp=H/'sbc-power/CM-sparse-exact-current-R543-TMR-repaired-only-new-role-withdrawal-inherited-fills-FAIL-r333/model.pkl';rp=mp.parent/'receipt.json';assert sha(mp)=='f9df66060a0f45959c4234f698500070c1ba2b4837894eee644cec36891dce9b';assert sha(rp)=='ce105c4fd985d3f90159bc425877217883035c57c27e4a4f2ca1144d43192daf';g,h0,b0,q0,before=pickle.loads(mp.read_bytes());h=copy.deepcopy(h0);b=copy.deepcopy(b0);q=copy.deepcopy(q0);put(O/'exact-mixed-role-operation-metadata-restoration.json',PS.restore_bound_field_current_precision_states(b,q));oldq={z['uuid']:z for z in q};oldrole={(z['uuid'],r):z[r]for z in q for r in('shape','zone_outline_shape')}
 pr=H/'sbc-power/CM79-exact-R333-q4f-q053-only-local-coupled-In2-corridor-nominations-source-embed100um-r337/receipt.json';assert sha(pr)=='c747819a9cb79bd7a4ad7395549db740706b8eca9b74ef2a00d879658647334c';proposal=json.loads((pr.parent/'only-full1p25-In2-actual-source-route-proposals.json').read_text())[0];ip=proposal['In2_nomination'];assert ip['endpoint_embedded_in_actual_source_Cu']and ip['actual_source_endpoint_boundary_distance_mm']>=.10 and ip['source_Cu_finite_overlap_mm2']>.5;uid='dc1a0d7a-0d99-4e6e-872b-2ddca9166fe1';old=next(t for t in h['tracks']if t['uuid']==uid);assert old['net']=='/mc_local_power{slash}CORE_5V'and old['layer']=='F.Cu'and old['w']==1.25;source=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';raw=source.read_bytes();iv=A.C.inventory(raw);oldchunk=iv[3][uid];assert hashlib.sha256(oldchunk).hexdigest()=='191f77c745a09f3083e5f0afac04439c853245e4362681b1bf3a1cd5af81e14e';parsed=A.G.parse(uid,oldchunk,{});assert(parsed['net'],parsed['layer'],parsed['w'],parsed['a'],parsed['b'])==(L.norm(old['net']),old['layer'],old['w'],old['a'],old['b']);(O/(uid+'.exact-original-source-delete-chunk')).write_bytes(oldchunk);nom={'accepted_count':50};d={'tracks':[],'vias':[],'removed_original_track_UUIDs':[uid]};ground=[[117.452,201.175],[117.452,201.805],[118.652,201.805],[118.652,201.175]]
 def track(tag,net,layer,width,aa,bb):
  assert all(round(y,6)==y for y in aa+bb);d['tracks'].append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R338:'+tag)),'net':net,'layer':layer,'w':width,'a':aa,'b':bb})
 for i,(aa,bb)in enumerate(zip(ground,ground[1:])):track('ground-'+str(i),'/LOGIC_GND','F.Cu',.2,aa,bb)
 for tag,aa,bb in(('pre',old['a'],[116.2,202.35]),('post',[120.1,202.35],old['b'])):track('fullwidth-'+tag,old['net'],'F.Cu',1.25,aa,bb)
 for tag,layer,path in(('external-F','F.Cu',proposal['fullwidth_F_spur']['full1p25_F_spur_path']),('source-In2','In2.Cu',ip['full1p25_In2_path'])):
  for i,(aa,bb)in enumerate(zip(path,path[1:])):track(tag+'-'+str(i),old['net'],layer,1.25,aa,bb)
 pv=proposal['screen']['power_xy_mm'];diam,drill=proposal['screen']['diameter_drill_mm'];assert(diam,drill)==(1.0,.5);port=proposal['fullwidth_F_spur']['exact_existing_source_LG_port']['via'];assert any(v==port for v in h['vias']);d['vias'].append({'uuid':str(uuid.uuid5(uuid.NAMESPACE_URL,'CM79-R338:ordinary-larger-power-port')),'net':old['net'],'x':pv[0],'y':pv[1],'d':diam,'drill':drill,'flashed':['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']});assert .9<=proposal['screen']['actual_ordinary_ground_pair_distance_mm']<=1.0;dp=O/'only-CM79-fullwidth-tracks-one-larger-power-via-one-exact-old-delete.pkl';dp.write_bytes(pickle.dumps(d,protocol=5));rounding=[];put(O/'bound-current-existing-return-fullwidth-source-embed-proposal.json',proposal);put(O/'exact-old-delete-authority.json',{'UUID':uid,'raw_net':old['net'],'exact_chunk_sha256':sha(O/(uid+'.exact-original-source-delete-chunk')),'full1p25_original_pre_post_F_anchor_geometry_retained':True,'only_original_F_middle_axis_removed':[[116.2,202.35],[120.1,202.35]],'new_fullwidth_F_path':proposal['fullwidth_F_spur']['full1p25_F_spur_path'],'new_fullwidth_In2_path':ip['full1p25_In2_path'],'new_power_port_diameter_drill_mm':[diam,drill],'ordinary_existing_source_GND_pair_UUID':port['uuid'],'actual_source_embed_mm':ip['actual_source_endpoint_boundary_distance_mm'],'actual_source_Cu_overlap_mm2':ip['source_Cu_finite_overlap_mm2'],'all49_CM_source_tracks_vias_source_masks_hard_unchanged':True,'no_D4_power_permission_aperture_or_capacity_credit':True});allowedOwned={'053e747d-d229-5488-b123-0bd7612fb8ef','4f297f78-8d11-5be4-910e-9245f73fa249'};localCorridor=zero(__import__('shapely.geometry',fromlist=['box']).box(116,169,139,208));q53=oldq['053e747d-d229-5488-b123-0bd7612fb8ef'];assert dig(q53['shape'])=='f1c8dff8cb02f72d2893bdacdce7f2d3d7a4c1a7606eb8dc064c27c3769c6524'and dig(q53['zone_outline_shape'])=='f80c55c22c79838f74ab15afb5a8a7fb361874350528921fe5d53ae9756ea89c';normalScopes={};extraScopes={};put(O/'exact-field-before-q53-two-role-authority.json',{'before_physical_sha256':dig(q53['shape']),'before_intended_sha256':dig(q53['zone_outline_shape']),'signed_full_FB_return_A':4.76859682896,'FB_buck_negative_CURRENT_A':-.09036666667,'separate_saved_FA_FB24_and_return_budget_V':.48,'actual_local_coupled_scope_mm':[116,169,139,208],'full_postcut_signed_current_and_loop_mesh':'OPEN'})
 existing={x['uuid']for k in('tracks','vias','pads')for x in h[k]};assert all(x['uuid']not in existing for x in d['tracks']+d['vias']);h['tracks']=[t for t in h['tracks']if t['uuid']!=uid]+d['tracks'];h['vias']+=d['vias'];items=d['tracks']+d['vias'];dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6
 put(O/'only-new-prospective-coordinate-canonicalization.json',rounding);cache={}
 def cutters(net,l,local,intent=False):
  key=(net,l,local,intent)
  if key in cache:return cache[key]
  rows=[]
  for x in items:
   via='d'in x;same=L.norm(net)==L.norm(x['net'])
   if via:
    if same and intent:continue
    radius=x['drill']/2+.00000002 if same else max(x['drill']/2+.275,x['d']/2+max(local,gap(net,x['net']))+.025)
    cut=Z.bounded_disk(x,radius);kind='own_actual_physical_drill_void_only'if same else'ordinary_foreign_Cu_drill_normal_antipad'
   else:
    if same or x['layer']!=l:continue
    radius=x['w']/2+max(local,gap(net,x['net']))+.025;cut=Z.bounded_buffer(LineString([x['a'],x['b']]),radius);kind='ordinary_new_fullwidth_track_normal_antipad'
   rows.append({'new_UUID':x['uuid'],'kind':kind,'same_net':same,'analytic_radius_mm':radius,'shape':cut})
  cache[key]=rows;return rows
 def repair(before_shape,current,key):
  steps=[];a=zero(before_shape)
  for it in range(16):
   gain=zero(current).difference(a)
   if gain.is_empty:break
   gs=save(key+'-'+str(it)+'-literal-raw-positive-component',gain);reserve=Z.bounded_buffer(gain,.0001);scope=normalScopes.get(key);assert scope is not None;outsideReserve=zero(reserve).difference(zero(Z.bounded_buffer(scope,.0002)));assert outsideReserve.is_empty,('local negative reserve outside actual new primitive guard plus200nm',key,outsideReserve.geom_type,outsideReserve.area);extraScopes.setdefault(key,[]).append(zero(reserve));cs=save(key+'-'+str(it)+'-explicit-local100nm-negative-reserve',reserve);prev=current;current=current.difference(reserve);ns=save(key+'-'+str(it)+'-actual-negative-delta',zero(prev).difference(zero(current)));steps.append({'iteration':it,'raw_gain':gs,'nominal_local_negative_reserve_mm':.0001,'cutter':cs,'actual_negative':ns,'no_magnitude_waiver':True})
  assert zero(current).difference(a).is_empty,('generated_literal_gain',key)
  canonical=set_precision(current,get_precision(before_shape),mode='pointwise');assert canonical.wkb==current.wkb,('generated_canonical_vertices',key)
  return current,steps
 roles=[];masks=[];changed=set()
 for z in q:
  for role in('shape','zone_outline_shape'):
   prev=z[role];active=[x for x in cutters(z['net'],z['layer'],float(z['clearance_mm']),role=='zone_outline_shape')if x['shape'].intersects(prev)]
   if not active:continue
   cut=unary_union([x['shape']for x in active]);key=z['uuid']+'-'+role;normalScopes[key]=zero(cut);normal=save(key+'-normal-new-primitives-cutter',cut);raw=prev.difference(cut);first=save(key+'-first-mask-after',raw);curr,steps=repair(prev,raw,key);z[role]=curr;changed.add(z['uuid']);row={'UUID':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'role':role,'exact_before_WKB_sha256':dig(prev),'operation_grid_mm':get_precision(prev),'normal_mask':normal,'first_after':first,'only_new_primitive_cuts':[{k:v for k,v in x.items()if k!='shape'}for x in active],'ordered_local_negative_reserve_steps':steps,'exact_after_WKB_sha256':dig(curr),'literal_zero_metadata_gain_empty':True,'new_generated_vertices_exact_canonical_in_bound_profile':True};roles.append(row)
  if z['uuid']in changed:
   for it in range(16):
    outside=zero(z['shape']).difference(zero(z['zone_outline_shape']))
    if outside.is_empty:break
    step={'UUID':z['uuid'],'role':'shape','kind':'explicit_physical_inside_actual_intended_local_negative','outside':save(z['uuid']+'-'+str(it)+'-physical-outside-intended',outside)};mask=Z.bounded_buffer(outside,.0001);step['local100nm_negative_mask']=save(z['uuid']+'-'+str(it)+'-physical-local100nm-mask',mask);normalScopes[z['uuid']+'-inside-intent-'+str(it)]=normalScopes.get(z['uuid']+'-shape',zero(mask));outsideMask=zero(mask).difference(zero(Z.bounded_buffer(normalScopes[z['uuid']+'-inside-intent-'+str(it)],.0002)));assert outsideMask.is_empty,('physical inside intent negative beyond new primitive local guard',z['uuid'],outsideMask.geom_type,outsideMask.area);raw=z['shape'].difference(mask);z['shape'],extra=repair(oldrole[z['uuid'],'shape'],raw,z['uuid']+'-inside-intent-'+str(it));step['literal_local_gain_negative_steps']=extra;roles.append(step)
   assert zero(z['shape']).difference(zero(z['zone_outline_shape'])).is_empty
 for z in q:
  for role in('shape','zone_outline_shape'):
   prev=oldrole[z['uuid'],role];curr=z[role]
   assert zero(curr).difference(zero(prev)).is_empty
   if prev.wkb!=curr.wkb:
    removedRole=zero(prev).difference(zero(curr));normal=normalScopes[z['uuid']+'-'+role];negativeScope=zero(Z.bounded_buffer(normal,.0002));outside=removedRole.difference(negativeScope);assert outside.is_empty,('generated role loss beyond new primitive normal+200nm nominated scope',z['uuid'],role,outside.geom_type,outside.area);
    if z['uuid']in allowedOwned:assert removedRole.difference(zero(Z.bounded_buffer(localCorridor,.0002))).is_empty,('owned coupled loss outside local corridor',z['uuid'],role)
    masks.append({'uuid':z['uuid'],'role':role,'raw_net':z['net'],'layer':z['layer'],'before_WKB_sha256':dig(prev),'after_WKB_sha256':dig(curr),'exact_negative_mask':zero(prev).difference(zero(curr))})
 b['generated_precision_state_ledger']=[{'new_generated_UUID':z['uuid'],'role':r,'grid_mm':get_precision(z[r]),'mode':'pointwise','unchanged_WKB_SHA256':dig(z[r])}for z in q for r in('shape','zone_outline_shape')];b['CM_sparse_R338_diagnostic']={'bound_parent_model_sha256':sha(mp),'only_new_CM_discrete_local_antipads':True,'fullbody_reference_failure_nominations_retained':True,'current_capacity_fault_native_manufacturing':'OPEN'}
 inherited_outside=[];filled=[];out=[];affected={'/LOGIC_GND',L.norm(old['net'])};qmap={z['uuid']:z for z in q}
 for z in before['zones']:
  nz=copy.deepcopy(z)
  for l,rs in z['fills'].items():
   ps=L.poly(rs);active=[x for x in cutters(z['net'],l,float(z['clearance_mm']))if any(x['shape'].intersects(p)for p in ps)];cuts=[zero(x['shape'])for x in active];role_alignment=[]
   if z['uuid']in changed and l==qmap[z['uuid']]['layer']:
    oldphysical=zero(oldrole[z['uuid'],'shape']);newphysical=zero(qmap[z['uuid']]['shape'])
    for i,p in enumerate(ps):
     prevoutside=zero(p).difference(oldphysical)
     if not prevoutside.is_empty:inherited_outside.append({'generated_UUID':z['uuid'],'raw_net':z['net'],'layer':l,'record':i,'inherited_literal_before_actual_filled_outside_bound_physical_FAIL':save(z['uuid']+'-'+l+'-'+str(i)+'-inherited-literal-outside-before-physical',prevoutside),'not_globally_clipped_or_waived':True})
     extra=zero(p).intersection(oldphysical.difference(newphysical))
     if not extra.is_empty:cuts.append(extra);role_alignment.append({'record':i,'explicit_negative_inside_new_owned_physical':save(z['uuid']+'-'+l+'-'+str(i)+'-owned-physical-alignment-cutter',extra)})
   if not cuts:continue
   nr,ledger=IM.subtract(rs,cuts,O,z['uuid']+'-'+l+'-new-CM-local-negative');sourceScope=zero(Z.bounded_buffer(zero(unary_union(cuts)),.0002));
   for row in ledger['per_original_record_operations']:
    for reserve in row.get('reserves',[]):
     mask=zero(__import__('shapely',fromlist=['from_wkb']).from_wkb(Path(reserve['reserve_file']).read_bytes()));remote=mask.difference(sourceScope);assert remote.is_empty,('actual current record reserve beyond explicit normal plus200nm',z['uuid'],l,row['record'],remote.geom_type,remote.area)
   nz['fills'][l]=nr;affected.add(L.norm(z['net']));filled.append({'zone_UUID':z['uuid'],'raw_net':z['net'],'layer':l,'original_native_definition_all_settings_exact':{k:v for k,v in nz.items()if k!='fills'}=={k:v for k,v in z.items()if k!='fills'},'only_new_primitive_cuts':[{k:v for k,v in x.items()if k!='shape'}for x in active],'role_actual_fill_alignment':role_alignment,'strict_literal_per_original_record_operations':ledger})
  out.append(nz)
 after={**before,'tracks':h['tracks'],'vias':h['vias'],'zones':out};assert all({k:v for k,v in z.items()if k not in('shape','zone_outline_shape')}=={k:v for k,v in oldq[z['uuid']].items()if k not in('shape','zone_outline_shape')}for z in q);put(O/'exact-two-owned-final-role-local-negative-ledger.json',[{'UUID':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'roles':{role:{'before_WKB_sha256':dig(oldrole[z['uuid'],role]),'after_WKB_sha256':dig(z[role]),'actual_local_removed_mm2':zero(oldrole[z['uuid'],role]).difference(zero(z[role])).area,'literal_gain_EMPTY':zero(z[role]).difference(zero(oldrole[z['uuid'],role])).is_empty}for role in('shape','zone_outline_shape')}}for z in q if z['uuid']in allowedOwned]);assert g==pickle.loads(mp.read_bytes())[0];put(O/'inherited-owned-filled-outside-before-physical-FAIL-retained.json',inherited_outside);put(O/'only-new-CM-generated-role-ordered-operations.json',roles);put(O/'only-new-CM-current-filled-record-operations.json',filled);put(O/'all-unrelated-native-settings-and-owned-role-preservation.json',{'all_native_zone_definition_settings_unchanged':all({k:v for k,v in a.items()if k!='fills'}=={k:v for k,v in bb.items()if k!='fills'}for a,bb in zip(before['zones'],after['zones'])),'untouched_owned_role_WKB_exact':all(z[r].wkb==oldrole[z['uuid'],r].wkb for z in q if z['uuid']not in changed for r in('shape','zone_outline_shape')),'affected_nets':sorted(affected)})
 (O/'only-CM79-fullwidth-tracks-one-larger-power-via-one-exact-old-delete.pkl').write_bytes(pickle.dumps(d,protocol=5));(O/'only-mutated-generated-role-negative-masks.pkl').write_bytes(pickle.dumps(masks,protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,q,after),protocol=5));source=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';identity=A.N.SourceNets(source.read_bytes());native={};ops=[]
 for x in items:
  assert identity.raw(L.norm(x['net']))==x['net'];via='d'in x
  if via:ch='\t(via\n\t\t(at %.6f %.6f)\n\t\t(size %.6f)\n\t\t(drill %.6f)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net %s)\n\t\t(uuid %s)\n\t)\n'%(x['x'],x['y'],x['d'],x['drill'],json.dumps(x['net']),json.dumps(x['uuid']))
  else:ch='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.6f)\n\t\t(layer %s)\n\t\t(net %s)\n\t\t(uuid %s)\n\t)\n'%(*x['a'],*x['b'],x['w'],json.dumps(x['layer']),json.dumps(x['net']),json.dumps(x['uuid']))
  file=O/(x['uuid']+('.via-chunk'if via else'.segment-chunk'));file.write_text(ch,encoding='utf-8',newline='');native[x['uuid']]=ch.encode();ops.append({'action':'add','uuid':x['uuid'],'kind':'via'if via else'segment','exact_chunk_path':str(file.resolve()),'exact_chunk_sha256':sha(file),'exact_geometry':x,'native_all6_flash_PENDING':via})
 identity.assert_chunks(native);ops.insert(0,{'action':'delete','uuid':uid,'kind':'segment','exact_old_native_source_chunk_path':str((O/(uid+'.exact-original-source-delete-chunk')).resolve()),'exact_old_native_source_chunk_sha256':sha(O/(uid+'.exact-original-source-delete-chunk'))});put(O/'exact-sparse-new-CM-native-operation-ledger.json',ops)
 manifest={str(p.resolve()):sha(p)for p in O.iterdir()if p.is_file()and p.suffix in('.wkb','.json','.pkl')};put(O/'exact-owned-operation-artifact-manifest.json',manifest);put(O/'receipt.json',{'verdict':'ISOLATED_CM79_EXACT_R333_LARGER_POWER_PORT_LOCAL_q053_SPARSE_DIAGNOSTIC_ALL_FRESH_GATES_OPEN','exact_current_parent_model_file':str(mp.resolve()),'exact_current_parent_model_sha256':sha(mp),'exact_current_parent_receipt_sha256':sha(rp),'nomination_receipt_sha256':sha(pr),'nomination_discrete_sha256':sha(dp),'nominated_pad_count':nom['accepted_count'],'required_CM_ground_candidate_count':51,'new_segment_count':len(d['tracks']),'new_ordinary_via_count':len(d['vias']),'exact_old_deletes':1,'changed_generated_UUIDs':sorted(changed),'changed_generated_role_count':len(masks),'current_filled_layer_scope_count':len(filled),'affected_nets':sorted(affected),'all_original_native_source_rules_pads_poses_zone_definitions_exact':True,'all_generated_and_current_filled_literal_remove_only':True,'no_whole_older_model_or_fill_overlay':True,'all_new_generated_grid_roles_bound_and_WKB_canonical':True,'model_sha256':sha(O/'model.pkl'),'sparse_discrete_sha256':sha(O/'only-CM79-fullwidth-tracks-one-larger-power-via-one-exact-old-delete.pkl'),'negative_role_mask_sha256':sha(O/'only-mutated-generated-role-negative-masks.pkl'),'artifact_manifest_sha256':sha(O/'exact-owned-operation-artifact-manifest.json'),'inherited_owned_fill_outside_physical_FAIL_count':len(inherited_outside),'only_exact_new_role_withdrawal_no_global_old_outside_clip':True,'signed_CM_return_A':3.5593046439628484,'signed_CORE5_output_A':7.882034293398379,'signed_SBC_common_branch_A':4.396304643962848,'fullwidth_F_plus_In2_one_larger_single_barrel_bottleneck_plating_drop_current_thermal_and_fullreturn':'OPEN','signed_FB_full_return_A':4.76859682896,'FB_buck_negative_CURRENT_A':-.09036666667,'saved_FA_FB24_and_return_budget_V':.48,'two_owned_local_source_direct_reference_and_fullsigned_mesh_native_gates':'OPEN','R336_near_tangent_source_contact_failure_preserved':True,'no_equal_share_capacity_derating_or_zero_return_credit':True,'inherited_CORE93_fullbody_R7_six_extra_planner_full_current_fault_native':'FAIL_OR_OPEN_RETAINED','new_fullbody_reference_failures_contact_source_fullcurrent_native':'FAIL_OR_OPEN_PENDING','native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R338_COMPLETE',nom['accepted_count'],len(d['tracks']),len(d['vias']),sha(O/'receipt.json'),sha(O/'model.pkl'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
