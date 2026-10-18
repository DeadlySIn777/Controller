"""Sparse CM routes/normal antipads on exact R364; all inherited FAILs retained.

No old filled-array/model overlay. Every generated role has exact bound grid
metadata replay, canonical new vertices, literal zero-grid strict withdrawal,
and explicit local100nm reserve receipts for any positive operation residue.
"""
import copy,hashlib,json,pickle,sys,traceback,time
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
O=H/'sbc-power/CM-sparse-exact-current-R543-TMR-repaired-only-new-role-withdrawal-inherited-fills-FAIL-r333'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def dig(s):return hashlib.sha256(s.wkb).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def zero(s):a=set_precision(s,0);assert a.wkb==s.wkb;return a
def save(name,s):f=O/(name+'.wkb');f.write_bytes(s.wkb);return {'file':str(f.resolve()),'sha256':sha(f),'area_mm2':s.area,'empty':s.is_empty}
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();(O/'exact-expanded-sparse-constructor.py').write_text(s,encoding='utf-8');mp=H/'field-power/FIELD5-source-plane-exact-owned-edge-negative-redesign-current-r543/model.pkl';rp=mp.parent/'receipt.json';assert sha(mp)=='474949d472a1870320b95cd494d4c96f79735b43632076d237d432d10c006416';assert sha(rp)=='e049f4b72291cba52dab6c14f892c80ae38042919542969483efdc250627b214';g,h0,b0,q0,before=pickle.loads(mp.read_bytes());h=copy.deepcopy(h0);b=copy.deepcopy(b0);q=copy.deepcopy(q0);put(O/'exact-mixed-role-operation-metadata-restoration.json',PS.restore_bound_field_current_precision_states(b,q));tmrAuthority=H/'field-power/FA-IO3-native-TMR-exact-two-zone-sparse-rebase-contract-r519/receipt.json';assert sha(tmrAuthority)=='bf494afa1699ce52e1812b79efe3676d31cb9d25f4a9c6d0f79b55b65bf8440e';tmrQ=next(z for z in q if z['uuid']=='4f297f78-8d11-5be4-910e-9245f73fa249');assert dig(tmrQ['shape'])=='06ef5939f3625df48164f01042bd0f0bdd62ec2c55bab7e86cb766706ed6e04b';assert dig(tmrQ['zone_outline_shape'])=='54d90e0bba440e852b8efe2cc09fa5ba8162c2269aeae75964a83ab1846072ac';put(O/'exact-field-TMR-repaired-q4f-before-role-authority.json',{'R519_contract_sha256':sha(tmrAuthority),'current_R543_model_sha256':sha(mp),'q4f_physical_before_sha256':dig(tmrQ['shape']),'q4f_intended_before_sha256':dig(tmrQ['zone_outline_shape']),'field_TMR_triangle_and_corridor_scope_hard_mm':[324,119,348,134],'only_new_CM_ground_primitives_normal_negative_replay':True,'no_R289_snapshot_overlay':True});oldq={z['uuid']:z for z in q};oldrole={(z['uuid'],r):z[r]for z in q for r in('shape','zone_outline_shape')}
 dp=H/'sbc-power/CM51-final-two-real-positive-cap-land-edge-nominations-r281/only-nominated-discrete.pkl';pr=dp.parent/'receipt.json';nom=json.loads(pr.read_text());d=pickle.loads(dp.read_bytes());assert not d['removed_original_track_UUIDs'];assert len(d['vias'])==nom['new_via_count'];assert len(d['tracks'])==nom['new_track_count'];assert all((v['d'],v['drill'])==(.5,.2)for v in d['vias'])and all(t['w']==.2 and t['layer']=='F.Cu'for t in d['tracks']);rounding=[]
 for x in d['tracks']+d['vias']:
  prior=copy.deepcopy(x)
  if'd'in x:x['x']=round(x['x'],6);x['y']=round(x['y'],6)
  else:x['a']=[round(y,6)for y in x['a']];x['b']=[round(y,6)for y in x['b']]
  if x!=prior:rounding.append({'UUID':x['uuid'],'only_new_prospective_coordinates_before':prior,'only_new_integer_nm_coordinates_after':x})
  assert x['net']=='/LOGIC_GND'
 existing={x['uuid']for k in('tracks','vias','pads')for x in h[k]};assert all(x['uuid']not in existing for x in d['tracks']+d['vias']);h['tracks']+=d['tracks'];h['vias']+=d['vias'];items=d['tracks']+d['vias'];dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6
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
   gs=save(key+'-'+str(it)+'-literal-raw-positive-component',gain);reserve=Z.bounded_buffer(gain,.0001);cs=save(key+'-'+str(it)+'-explicit-local100nm-negative-reserve',reserve);prev=current;current=current.difference(reserve);ns=save(key+'-'+str(it)+'-actual-negative-delta',zero(prev).difference(zero(current)));steps.append({'iteration':it,'raw_gain':gs,'nominal_local_negative_reserve_mm':.0001,'cutter':cs,'actual_negative':ns,'no_magnitude_waiver':True})
  assert zero(current).difference(a).is_empty,('generated_literal_gain',key)
  canonical=set_precision(current,get_precision(before_shape),mode='pointwise');assert canonical.wkb==current.wkb,('generated_canonical_vertices',key)
  return current,steps
 roles=[];masks=[];changed=set()
 for z in q:
  for role in('shape','zone_outline_shape'):
   prev=z[role];active=[x for x in cutters(z['net'],z['layer'],float(z['clearance_mm']),role=='zone_outline_shape')if x['shape'].intersects(prev)]
   if not active:continue
   cut=unary_union([x['shape']for x in active]);key=z['uuid']+'-'+role;normal=save(key+'-normal-new-primitives-cutter',cut);raw=prev.difference(cut);first=save(key+'-first-mask-after',raw);curr,steps=repair(prev,raw,key);z[role]=curr;changed.add(z['uuid']);row={'UUID':z['uuid'],'raw_net':z['net'],'layer':z['layer'],'role':role,'exact_before_WKB_sha256':dig(prev),'operation_grid_mm':get_precision(prev),'normal_mask':normal,'first_after':first,'only_new_primitive_cuts':[{k:v for k,v in x.items()if k!='shape'}for x in active],'ordered_local_negative_reserve_steps':steps,'exact_after_WKB_sha256':dig(curr),'literal_zero_metadata_gain_empty':True,'new_generated_vertices_exact_canonical_in_bound_profile':True};roles.append(row)
  if z['uuid']in changed:
   for it in range(16):
    outside=zero(z['shape']).difference(zero(z['zone_outline_shape']))
    if outside.is_empty:break
    step={'UUID':z['uuid'],'role':'shape','kind':'explicit_physical_inside_actual_intended_local_negative','outside':save(z['uuid']+'-'+str(it)+'-physical-outside-intended',outside)};mask=Z.bounded_buffer(outside,.0001);step['local100nm_negative_mask']=save(z['uuid']+'-'+str(it)+'-physical-local100nm-mask',mask);raw=z['shape'].difference(mask);z['shape'],extra=repair(oldrole[z['uuid'],'shape'],raw,z['uuid']+'-inside-intent-'+str(it));step['literal_local_gain_negative_steps']=extra;roles.append(step)
   assert zero(z['shape']).difference(zero(z['zone_outline_shape'])).is_empty
 for z in q:
  for role in('shape','zone_outline_shape'):
   prev=oldrole[z['uuid'],role];curr=z[role]
   assert zero(curr).difference(zero(prev)).is_empty
   if prev.wkb!=curr.wkb:masks.append({'uuid':z['uuid'],'role':role,'raw_net':z['net'],'layer':z['layer'],'before_WKB_sha256':dig(prev),'after_WKB_sha256':dig(curr),'exact_negative_mask':zero(prev).difference(zero(curr))})
 b['generated_precision_state_ledger']=[{'new_generated_UUID':z['uuid'],'role':r,'grid_mm':get_precision(z[r]),'mode':'pointwise','unchanged_WKB_SHA256':dig(z[r])}for z in q for r in('shape','zone_outline_shape')];b['CM_sparse_R333_diagnostic']={'bound_parent_model_sha256':sha(mp),'only_new_CM_discrete_local_antipads':True,'fullbody_reference_failure_nominations_retained':True,'current_capacity_fault_native_manufacturing':'OPEN'}
 inherited_outside=[];filled=[];out=[];affected={'/LOGIC_GND'};qmap={z['uuid']:z for z in q}
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
   nr,ledger=IM.subtract(rs,cuts,O,z['uuid']+'-'+l+'-new-CM-local-negative');nz['fills'][l]=nr;affected.add(L.norm(z['net']));filled.append({'zone_UUID':z['uuid'],'raw_net':z['net'],'layer':l,'original_native_definition_all_settings_exact':{k:v for k,v in nz.items()if k!='fills'}=={k:v for k,v in z.items()if k!='fills'},'only_new_primitive_cuts':[{k:v for k,v in x.items()if k!='shape'}for x in active],'role_actual_fill_alignment':role_alignment,'strict_literal_per_original_record_operations':ledger})
  out.append(nz)
 after={**before,'tracks':h['tracks'],'vias':h['vias'],'zones':out};assert g==pickle.loads(mp.read_bytes())[0];put(O/'inherited-owned-filled-outside-before-physical-FAIL-retained.json',inherited_outside);put(O/'only-new-CM-generated-role-ordered-operations.json',roles);put(O/'only-new-CM-current-filled-record-operations.json',filled);put(O/'all-unrelated-native-settings-and-owned-role-preservation.json',{'all_native_zone_definition_settings_unchanged':all({k:v for k,v in a.items()if k!='fills'}=={k:v for k,v in bb.items()if k!='fills'}for a,bb in zip(before['zones'],after['zones'])),'untouched_owned_role_WKB_exact':all(z[r].wkb==oldrole[z['uuid'],r].wkb for z in q if z['uuid']not in changed for r in('shape','zone_outline_shape')),'affected_nets':sorted(affected)})
 (O/'only-new-CM-ordinary-discrete-no-deletes.pkl').write_bytes(pickle.dumps(d,protocol=5));assert sha(O/'only-new-CM-ordinary-discrete-no-deletes.pkl')=='72321f8b75794e2cf2bd5d4ba6788da7bbdb8eaa4ba692cf9a121d4c3bde3207';(O/'only-mutated-generated-role-negative-masks.pkl').write_bytes(pickle.dumps(masks,protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,q,after),protocol=5));source=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';identity=A.N.SourceNets(source.read_bytes());native={};ops=[]
 for x in items:
  assert identity.raw('/LOGIC_GND')==x['net'];via='d'in x
  if via:ch='\t(via\n\t\t(at %.6f %.6f)\n\t\t(size .5)\n\t\t(drill .2)\n\t\t(layers "F.Cu" "B.Cu")\n\t\t(net "/LOGIC_GND")\n\t\t(uuid %s)\n\t)\n'%(x['x'],x['y'],json.dumps(x['uuid']))
  else:ch='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width .2)\n\t\t(layer "F.Cu")\n\t\t(net "/LOGIC_GND")\n\t\t(uuid %s)\n\t)\n'%(*x['a'],*x['b'],json.dumps(x['uuid']))
  file=O/(x['uuid']+('.via-chunk'if via else'.segment-chunk'));file.write_text(ch,encoding='utf-8',newline='');native[x['uuid']]=ch.encode();ops.append({'action':'add','uuid':x['uuid'],'kind':'via'if via else'segment','exact_chunk_path':str(file.resolve()),'exact_chunk_sha256':sha(file),'exact_geometry':x,'native_all6_flash_PENDING':via})
 identity.assert_chunks(native);put(O/'exact-sparse-new-CM-native-operation-ledger.json',ops)
 manifest={str(p.resolve()):sha(p)for p in O.iterdir()if p.is_file()and p.suffix in('.wkb','.json','.pkl')};put(O/'exact-owned-operation-artifact-manifest.json',manifest);put(O/'receipt.json',{'verdict':'EXPLORATORY_CM_SPARSE_CURRENT_CONSTRUCTOR_ONLY_NEW_CU_ALL_FULL_SOURCE_REFERENCE_CURRENT_NATIVE_GATES_OPEN','exact_current_parent_model_file':str(mp.resolve()),'exact_current_parent_model_sha256':sha(mp),'exact_current_parent_receipt_sha256':sha(rp),'nomination_receipt_sha256':sha(pr),'nomination_discrete_sha256':sha(dp),'nominated_pad_count':nom['accepted_count'],'required_CM_ground_candidate_count':51,'new_segment_count':len(d['tracks']),'new_ordinary_via_count':len(d['vias']),'exact_old_deletes':0,'changed_generated_UUIDs':sorted(changed),'changed_generated_role_count':len(masks),'current_filled_layer_scope_count':len(filled),'affected_nets':sorted(affected),'all_original_native_source_rules_pads_poses_zone_definitions_exact':True,'all_generated_and_current_filled_literal_remove_only':True,'no_whole_older_model_or_fill_overlay':True,'all_new_generated_grid_roles_bound_and_WKB_canonical':True,'model_sha256':sha(O/'model.pkl'),'sparse_discrete_sha256':sha(O/'only-new-CM-ordinary-discrete-no-deletes.pkl'),'negative_role_mask_sha256':sha(O/'only-mutated-generated-role-negative-masks.pkl'),'artifact_manifest_sha256':sha(O/'exact-owned-operation-artifact-manifest.json'),'inherited_owned_fill_outside_physical_FAIL_count':len(inherited_outside),'only_exact_new_role_withdrawal_applied_no_global_old_outside_clip':True,'signed_CM_return_A':3.5593046439628484,'no_equal_share_capacity_derating_or_zero_return_credit':True,'inherited_CORE93_fullbody_R7_six_extra_planner_full_current_fault_native':'FAIL_OR_OPEN_RETAINED','new_fullbody_reference_failures_contact_source_fullcurrent_native':'FAIL_OR_OPEN_PENDING','native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)});print('R333_COMPLETE',nom['accepted_count'],len(d['tracks']),len(d['vias']),sha(O/'receipt.json'),sha(O/'model.pkl'),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
