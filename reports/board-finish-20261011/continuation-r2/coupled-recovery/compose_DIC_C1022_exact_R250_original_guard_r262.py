"""One exact R250 plus sparse C1022/DIC operation; no board or native job."""
import sys,json,pickle,copy,time,math,re
from pathlib import Path
H=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import contact_layout as L
import complete_geometry_r2 as GE
import guarded_power_projection_r44 as Z
import restore_SAFE_generated_precision_states_r168 as PS
import immutable_local_fill_subtraction_r254 as IM
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
C=A.C;LAYERS=['F.Cu','In1.Cu','In2.Cu','In3.Cu','In4.Cu','B.Cu']
PROFILE=('net','layer','clearance_mm','min_thickness_mm','pad_connect_mode','priority','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm')
O=H/'DIC-C1022-exact-R250-original-guard-construction-r262'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();base=H/'CORE-R112-per-polygon-immutable-owned-construction-r250';raw=A.read(base/'model.pkl');assert C.sha(raw)=='96d3f55a95b770a2a7f46e3b25274723946fe1572c6c82d81b7355b660360868';base_receipt=A.read(base/'receipt.json');assert C.sha(base_receipt)=='9de23083359b26f15e8d7b9f8e3692e940fec1ed1e8feb54015318eb45013a96';g,h0,b0,q0,before=pickle.loads(raw);h=copy.deepcopy(h0);b=copy.deepcopy(b0);q=copy.deepcopy(q0);precision=PS.restore_bound_generated_precision_states(b,q);put(O/'bound-unchanged-generated-role-precision.json',precision)
 sourcefile=H.parent/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';source=A.read(sourcefile);assert C.sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';identity=A.N.SourceNets(source);iv=C.inventory(source)
 joint=H/'DIC-C1022-one-R214-joint-native-integration-delta-r222/receipt.json';joint_raw=A.read(joint);assert C.sha(joint_raw)=='bbf14c6887829a93d50fbf285aad61353dbc60eb30eaad1485036d410c89be0f';authority=json.loads(joint_raw);assert authority['counts']=={'exact_original_eedf_segment_deletes':4,'new_segments':21,'new_ordinary_vias':5,'relative_base_FP_zone_rule_project_retags':0}
 incremental=H/'CORE-R250-vs-actual-R214-independent-r252/receipt.json';ar=A.read(incremental);assert C.sha(ar)=='db5c57276f9dfc385b8a195daa178d36af296a3be24b226370c936d2442df560';ir=json.loads(ar);assert not(ir['all77_actual_drilled_contact_losses']or ir['true_all6_geometry_errors']or ir['nine_prior_source_bank_layer_key_loss_count']or ir['three_bank_strict_ZERO_retained_reference_loss_count']);assert ir['new_CORE_fullbody_actual_J1_reference']['actual_J1_In1_full_reference_gap_mm2']==93.04195929171794
 dp=H/'DIC-native-owned-ledger-r212/receipt.json';dr=json.loads(A.read(dp));assert C.sha(A.read(dp))=='9e63e595cbea54c90b4e340fbb68cfd5e920a25dee0ae4c40a94b6e555bfb543';assert dr['source_parent_sha256']==C.sha(source);deleted={};added={};oprows=[]
 for row in dr['rows']:
  ch=A.read(row['exact_chunk_path']);assert C.sha(ch)==row['exact_chunk_sha256'];uid=row['uuid'];assert uid not in deleted and uid not in added;oprows.append({**row,'packet_file':str(dp),'packet_sha256':C.sha(A.read(dp))})
  if row['action']=='remove':assert source.count(ch)==1 and iv[3][uid]==ch;deleted[uid]=ch
  else:assert row['action']=='add' and uid not in iv[3];added[uid]=ch
 assert len(deleted)==4 and len(added)==25
 cp=H.parent/'sbc-power/C1022-validated-native-integration-packet-r222/receipt.json';cr=json.loads(A.read(cp));assert C.sha(A.read(cp))=='ab63866ae63e1aff6da41f96630346989bdc4d92e9eb2feee499173b37f3ab02';assert cr['positive_R214_parent_sha256']=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e' and not(cr['delete_rows'] or cr['footprint_replacement_rows'] or cr['owned_new_zone_replacement_rows']);assert len(cr['add_rows'])==1
 for row in cr['add_rows']:
  ch=A.read(row['chunk_path']);assert C.sha(ch)==row['chunk_sha256'];uid=row['uuid'];assert uid not in added and uid not in iv[3];added[uid]=ch;oprows.append({'action':'add','uuid':uid,'kind':'segment','exact_chunk_path':row['chunk_path'],'exact_chunk_sha256':C.sha(ch),'packet_file':str(cp),'packet_sha256':C.sha(A.read(cp))})
 identity.assert_chunks(added);oldtracks={t['uuid']:t for t in h['tracks']};oldvias={v['uuid']:v for v in h['vias']};assert set(deleted)<=set(oldtracks);assert not set(added)&(set(oldtracks)|set(oldvias));nt=[];nv=[]
 for uid,ch in deleted.items():
  p=A.G.parse(uid,ch,{});t=oldtracks[uid];assert(p['kind'],p['net'],p['layer'],p['w'],p['a'],p['b'])==('segment',L.norm(t['net']),t['layer'],t['w'],t['a'],t['b'])
 for uid,ch in added.items():
  p=A.G.parse(uid,ch,{})
  if p['kind']=='segment':nt.append({'uuid':uid,'net':identity.raw(p['net']),'layer':p['layer'],'w':p['w'],'a':p['a'],'b':p['b']})
  else:assert p['kind']=='via' and(p['d'],p['drill'])==(.5,.2);assert not any(x in ch for x in(b'remove_unused_layers',b'keep_end_layers',b'zone_connection'));nv.append({'uuid':uid,'net':identity.raw(p['net']),'x':p['at'][0],'y':p['at'][1],'d':p['d'],'drill':p['drill'],'flashed':list(LAYERS)})
 assert len(nt)==21 and len(nv)==5;h['tracks']=[t for t in h['tracks'] if t['uuid'] not in deleted]+nt;h['vias']+=nv
 for key,value in h0.items():
  if key not in('tracks','vias'):assert h[key]==value,key
 assert {v['uuid']:v for v in h['vias'] if v['uuid'] not in added}==oldvias;assert {t['uuid']:t for t in h['tracks'] if t['uuid'] not in added}=={u:t for u,t in oldtracks.items() if u not in deleted};assert b==b0
 # Generated physical/intended role bytes and explicit settings stay exact.
 # Any new cut of an owned proposal is an explicit joint correction, never an
 # implicit stale model overlay; the existing independent mutual gate says0.
 domains=h['domains_normalized'];gap=lambda a,b:.15 if domains.get(L.norm(a))==domains.get(L.norm(b)) else .6;held_errors=[];profiles=[]
 for z,old in zip(q,q0):
  assert z['uuid']==old['uuid'] and all(z[role].wkb==old[role].wkb for role in('shape','zone_outline_shape'));assert {k:v for k,v in z.items() if k not in('shape','zone_outline_shape')}=={k:v for k,v in old.items() if k not in('shape','zone_outline_shape')};assert all(k in z for k in('net','layer','clearance_mm'));profiles.append({'UUID':z['uuid'],'explicit_settings':{k:z[k] for k in PROFILE if k in z},'missing_inherited_profile_fields_OPEN':[k for k in PROFILE if k not in z]})
  for item in nt+nv:
   via='d'in item
   if not via and item['layer']!=z['layer']:continue
   same=L.norm(item['net'])==L.norm(z['net']);req=max(float(z['clearance_mm']),gap(item['net'],z['net']))+.025;radius=item['drill']/2 if via and same else max(item['drill']/2+.275,item['d']/2+req) if via else item['w']/2+req;cut=Z.bounded_disk(item,radius) if via else Z.bounded_buffer(LineString([item['a'],item['b']]),radius)
   if same and not via:continue
   for role in('shape','zone_outline_shape'):
    overlap=cut.intersection(z[role])
    if not overlap.is_empty:held_errors.append({'new_UUID':item['uuid'],'owned_UUID':z['uuid'],'role':role,'exact_role_WKB_sha256':C.sha(z[role].wkb),'proposed_cut_WKB_sha256':C.sha(cut.wkb),'intersection_mm2':overlap.area})
 assert not held_errors,held_errors
 # Increment only actual BEFORE fills. Original h/g design definitions and
 # every generated intended outline remain untouched. Physical pieces split.
 zones=[];cuts=[]
 for old in before['zones']:
  assert 'clearance_mm'in old;local=float(old['clearance_mm']);z={**old,'fills':{}}
  if old['uuid'] in iv[3]:
   match=re.search(rb'\(connect_pads(?:\s+[^()\s]+)?\s*\(clearance\s+([0-9.]+)\)',iv[3][old['uuid']]);assert match and float(match.group(1))==local
  for layer,rs in old['fills'].items():
   shape=unary_union(L.poly(rs));cutters=[];rows=[]
   for item in nt+nv:
    via='d'in item;same=L.norm(item['net'])==L.norm(z['net'])
    if not via and(item['layer']!=layer or same):continue
    req=max(local,gap(item['net'],z['net']))+.025;radius=item['drill']/2 if via and same else max(item['drill']/2+.275,item['d']/2+req) if via else item['w']/2+req;cut=Z.bounded_disk(item,radius) if via else Z.bounded_buffer(LineString([item['a'],item['b']]),radius)
    if not cut.intersects(shape):continue
    mask=O/(z['uuid']+'-'+layer+'-'+item['uuid']+'-exact-new-primitive-cut.wkb');mask.write_bytes(cut.wkb)
    cutters.append(cut);rows.append({'new_UUID':item['uuid'],'kind':'via' if via else'track','same_net_actual_physical_drill_only':bool(same),'analytic_radius_mm':radius,'exact_outward_cutter_WKB_sha256':C.sha(cut.wkb),'exact_cutter_file':str(mask)})
   if cutters:
    result_records,strict=IM.subtract(rs,cutters,O,z['uuid']+'-'+layer);z['fills'][layer]=result_records;cuts.append({'zone_UUID':z['uuid'],'raw_net':z['net'],'layer':layer,'exact_native_or_owned_local_mm':local,'before_WKB_sha256':C.sha(shape.wkb),'after_WKB_sha256':strict['after_WKB_sha256'],'removed_mm2':strict['exact_removed_mm2'],'physical_piece_count':len(result_records),'cutters':rows,'immutable_per_record_proof':strict})
   else:z['fills'][layer]=rs
  zones.append(z)
 after={**h,'zones':zones};assert all(q['uuid'] not in {r['zone_UUID'] for r in cuts} for q in q0),'All generated roles are held unchanged, including physical drilled roles'
 rotations=H.parent/'two-rotated-FP-native-collector-contract-r87/frozen-rotation-rows.json';rot=A.read(rotations);assert C.sha(rot)=='c79354f60f6fba0e38cd5f3df774876c4fc541ede3a2f27109d1a236f9c448d3';legacy=H.parent/'sbc-power/r17031-final-emitter-authorization-r88/binding-recipe.json';legacy_rows=json.loads(A.read(legacy));assert len(json.loads(rot))==2
 put(O/'exact-sparse-operation-ledger.json',oprows);put(O/'incremental-original-fill-cut-ledger.json',cuts);put(O/'unchanged-owned-native-profile-ledger.json',profiles);put(O/'preserved-root-pose-owner-authorities.json',{'R87_full_file':str(rotations),'R87_full_file_sha256':C.sha(rot),'frozen_two_rows':json.loads(rot),'legacy_R17031_binding_file':str(legacy),'legacy_R17031_binding_sha256':C.sha(A.read(legacy)),'legacy_authority_rows':legacy_rows,'no_regeneration_or_pose_flag_change':True})
 (O/'new-owned-discrete.pkl').write_bytes(pickle.dumps({'tracks':nt,'vias':nv,'removed':sorted(deleted)},protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,q,after),protocol=5));result={'verdict':'EXACT_ONE_R250_C1022_DIC_MINIMAL_HOST_COMPOSITION_INDEPENDENT_FULL_GATES_OPEN','base_model_file':str(base/'model.pkl'),'base_model_sha256':C.sha(raw),'base_receipt_sha256':C.sha(base_receipt),'DIC_sparse_packet_sha256':C.sha(A.read(dp)),'C1022_sparse_packet_sha256':C.sha(A.read(cp)),'source_parent_file':str(sourcefile),'source_parent_sha256':C.sha(source),'new_tracks':21,'new_ordinary_all6_prospective_vias':5,'original_exact_track_deletes':4,'FP_project_rule_design_zone_or_pad_changes':0,'all_other_R250_discrete_metadata_exact':True,'all_R250_generated_role_WKB_and_native_settings_exact':True,'exact_source_raw_net_tokens_no_aliases':True,'model_file':str(O/'model.pkl'),'model_sha256':C.sha(A.read(O/'model.pkl')),'delta_file':str(O/'new-owned-discrete.pkl'),'delta_sha256':C.sha(A.read(O/'new-owned-discrete.pkl')),'exact_operation_file':str(O/'exact-sparse-operation-ledger.json'),'exact_operation_sha256':C.sha(A.read(O/'exact-sparse-operation-ledger.json')),'incremental_cut_file':str(O/'incremental-original-fill-cut-ledger.json'),'incremental_cut_sha256':C.sha(A.read(O/'incremental-original-fill-cut-ledger.json')),'owned_role_precision_restorations_file':str(O/'bound-unchanged-generated-role-precision.json'),'owned_role_precision_restorations_sha256':C.sha(A.read(O/'bound-unchanged-generated-role-precision.json')),'root_pose_owner_authorities_file':str(O/'preserved-root-pose-owner-authorities.json'),'root_pose_owner_authorities_sha256':C.sha(A.read(O/'preserved-root-pose-owner-authorities.json')),'inherited_R250_CORE_whole_DC_reference_gap_mm2':93.04195929171794,'R250_independent_overall_FAIL_and_ROOT42_current_native_preserved':True,'host_retained_relationships_pass':False,'host_all_supply_pad_and_proposed_components_rooted':False,'original_ROOT42_raw_power_reference_current_native_failures_not_waived':'OPEN/FAIL separate inherited evidence; no production flags flipped','independent_ALL77_physical_layer_contacts_seven_sources_zero_reference_newbody_guard_and_native':'OPEN','native_jobs':0,'board_written':False,'source_or_project_written':False,'adopted':False,'read_files_sha256':A.READS,'elapsed_seconds':time.monotonic()-started};put(O/'receipt.json',result);print(json.dumps({'receipt_sha256':C.sha(A.read(O/'receipt.json')),'model_sha256':result['model_sha256'],'original_fill_cuts':len(cuts),'generated_role_changes':0}),flush=True)
if __name__=='__main__':main()
