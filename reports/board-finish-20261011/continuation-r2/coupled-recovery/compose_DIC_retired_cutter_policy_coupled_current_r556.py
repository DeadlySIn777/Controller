"""Sparse current composition after exact retired-DIC source cache replay.

Immutable actual current arrays are cut per original record only. Generated
role WKB/settings and every unrelated discrete/source entity remain exact.
All inherited and raw constructor failures remain explicit, never adoption.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time,copy,re
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import immutable_local_fill_subtraction_r254 as IM
import restore_field_current_mixed_precision_states_r366 as MS
import audit_ao1_positive_operation_r4 as SERIAL
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def info(s):return {'empty':s.is_empty,'type':s.geom_type,'area_mm2':s.area,'bounds_mm':None if s.is_empty else list(s.bounds),'WKB_SHA256':K.C.sha(s.wkb)}
R554_SHA='05975d1790d6454860394bf439db2fa0550f9ddfad13c804f6ff5b26fd8c1e1a'

def main():
 st=time.monotonic();out=H/'DIC-retired-cutter-policy-coupled-current-r556';assert not out.exists();out.mkdir()
 rp=H/'DIC-exact-retired-cutter-two-locked-G0-FAULT-policy-route-r554/receipt.json';assert sha(rp)==R554_SHA;rr=json.loads(rp.read_bytes());assert rr['constructor_routes_positive'];pf=rp.with_name('exact-coupled-operation-NOT_ACCEPTED_MODEL.pkl');assert sha(pf)==rr['output_SHA256'][str(pf.resolve())];op=pickle.loads(pf.read_bytes())
 mp=H/'DIC-only-NEW55ab-retired-cutter-exact-source-restoration-r552/exact-retired-NEW55ab-only-cache-restoration-INTERMEDIATE_NOT_ADOPTED.pkl';assert sha(mp)=='fe1e8dfb04083ffb2084f37da0702280a654011cc090f3bd7b4bc9de93e7af85';g,h0,b0,q0,before=pickle.loads(mp.read_bytes());h=copy.deepcopy(h0);b=copy.deepcopy(b0);q=copy.deepcopy(q0);precision=MS.restore_bound_field_current_precision_states(b,q)
 sp=P/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(sp)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';source=sp.read_bytes();iv=K.C.inventory(source);identity=K.A.N.SourceNets(source);deleted=op['only_exact_native_deletes'];retired=set(op['only_unaccepted_NEW_track_withdrawals']);assert set(deleted)=={'2baae30c-8553-42e8-95d4-0fb985c24070','3eb0b0e1-5064-4fc4-9191-b1b9d35840f4'};assert len(retired)==8 and retired.isdisjoint(iv[3]);assert all(iv[3][u]==ch and source.count(ch)==1 and b'(locked yes)'in ch for u,ch in deleted.items());removed=set(deleted)|retired;assert removed<={t['uuid']for t in h['tracks']}
 nt=copy.deepcopy(op['new_locked_fault_and_DIC_tracks']);changed=copy.deepcopy(op['changed_only_NEW_via_definitions']);assert len(changed)==3;viaids={v['uuid']for v in changed};assert viaids=={'55ab5777-4032-59ab-94d1-d5a4478c7a72','99cc6bf8-836e-5f19-983a-c3724b1062a5','0330815c-1d94-5c79-9932-3d491fb10d15'};assert viaids.isdisjoint(iv[3]);h['tracks']=[t for t in h['tracks']if t['uuid']not in removed]+nt;h['vias']=[v for v in h['vias']if v['uuid']not in viaids]+changed;chunks=dict(op['exact_new_track_chunks'])
 for t in nt:
  ch=chunks[t['uuid']];p=K.A.G.parse(t['uuid'],ch,{});assert(p['net'],p['layer'],p['w'],p['a'],p['b'])==(K.L.norm(t['net']),t['layer'],t['w'],t['a'],t['b']);assert t['uuid']not in iv[3]
  if K.L.norm(t['net'])=='/motherboard_io_control/DI_SENSOR_G0_FAULT':assert t.get('locked')is True and b'(locked yes)'in ch
 for v in changed:
  assert(v['d'],v['drill'],v['flashed'])==(.5,.2,list(K.LAYERS));gen,ch=SERIAL.serial_via(identity,K.L.norm(v['net']),[v['x'],v['y']]);assert ch.count(gen.encode())==1;ch=ch.replace(gen.encode(),v['uuid'].encode());chunks[v['uuid']]=ch;p=K.A.G.parse(v['uuid'],ch,{});assert(p['net'],p['at'],p['d'],p['drill'])==(K.L.norm(v['net']),[v['x'],v['y']],.5,.2);assert not any(x in ch for x in(b'remove_unused_layers',b'keep_end_layers',b'zone_connection'))
 identity.assert_chunks(chunks);profile={'via':.5,'drill':.2,'hard_pair_min_mm':.90,'hard_pair_max_mm':1.0,'signal_layer_legs':3,'max_signal_layer_legs':3};put(out/'exact-sparse-native-delete-new-retirement-and-add-ledger.json',{'only_eedf_native_deletes':{u:{'chunk':ch.decode(),'SHA256':K.C.sha(ch)}for u,ch in deleted.items()},'only_unaccepted_current_NEW_track_retirements':sorted(retired),'exact_add_chunks':{u:{'chunk':ch.decode(),'SHA256':K.C.sha(ch)}for u,ch in chunks.items()},'ordinary_policy':profile,'no_original_native_via_or_FP_rule_outline_changes':True})
 for k,v in h0.items():
  if k not in('tracks','vias'):assert h[k]==v
 assert {t['uuid']:t for t in h['tracks']if t['uuid']not in chunks}=={t['uuid']:t for t in h0['tracks']if t['uuid']not in removed};assert {v['uuid']:v for v in h['vias']if v['uuid']not in viaids}=={v['uuid']:v for v in h0['vias']if v['uuid']not in viaids}
 domains=h['domains_normalized'];gap=lambda a,n:.15 if domains[K.L.norm(a)]==domains[K.L.norm(n)]else .6;held=[]
 for z in q:
  for item in nt+changed:
   via='d'in item;same=K.L.norm(item['net'])==K.L.norm(z['net'])
   if not via and(item['layer']!=z['layer']or same):continue
   req=max(float(z['clearance_mm']),gap(item['net'],z['net']))+.025;rad=item['drill']/2 if via and same else max(item['drill']/2+.275,item['d']/2+req)if via else item['w']/2+req;cut=K.Z.bounded_disk(item,rad)if via else K.Z.bounded_buffer(LineString([item['a'],item['b']]),rad)
   for role in('shape','zone_outline_shape'):
    hit=cut.intersection(z[role])
    if not hit.is_empty:held.append({'new_UUID':item['uuid'],'owned_UUID':z['uuid'],'same_raw_net':same,'role':role,'analytic_radius_mm':rad,'exact_hit':info(hit)})
 put(out/'any-required-owned-role-cut-REQUIRES-SEPARATE-EXACT-AUTHORITY.json',held);assert not held,'No blanket generated-role edit; freeze explicit required cut before successor'
 zones=[];ledger=[];changednets={K.L.norm(t['net'])for t in nt+changed}
 for zold in before['zones']:
  local=float(zold['clearance_mm']);z={**zold,'fills':{}}
  for ly,rs in zold['fills'].items():
   body=unary_union(K.L.poly(rs));cuts=[];rows=[]
   for item in nt+changed:
    via='d'in item;same=K.L.norm(item['net'])==K.L.norm(z['net'])
    if not via and(item['layer']!=ly or same):continue
    req=max(local,gap(item['net'],z['net']))+.025;rad=item['drill']/2 if via and same else max(item['drill']/2+.275,item['d']/2+req)if via else item['w']/2+req;cut=K.Z.bounded_disk(item,rad)if via else K.Z.bounded_buffer(LineString([item['a'],item['b']]),rad)
    if not cut.intersects(body):continue
    f=out/(z['uuid']+'-'+ly+'-'+item['uuid']+'-exact-new-primitive-cut.wkb');f.write_bytes(cut.wkb);cuts.append(cut);rows.append({'new_UUID':item['uuid'],'kind':'via'if via else'track','raw_net':item['net'],'same_raw_net_physical_drill_only':same,'analytic_radius_mm':rad,'exact_cutter_file':str(f.resolve()),'exact_cutter_SHA256':K.C.sha(cut.wkb)})
   if cuts:
    rs2,proof=IM.subtract(rs,cuts,out,z['uuid']+'-'+ly);z['fills'][ly]=rs2;ledger.append({'zone_UUID':z['uuid'],'layer':ly,'raw_net':z['net'],'native_or_owned_local_clearance_mm':local,'before_WKB_SHA256':K.C.sha(body.wkb),'after_WKB_SHA256':proof['after_WKB_sha256'],'immutable_per_record_proof':proof,'cutters':rows});changednets.add(K.L.norm(z['net']))
   else:z['fills'][ly]=rs
  zones.append(z)
 after={**h,'zones':zones};assert all(a['uuid']==o['uuid']and all(a[role].wkb==o[role].wkb for role in('shape','zone_outline_shape'))for a,o in zip(q,q0));assert b==b0;assert g==pickle.loads(mp.read_bytes())[0]
 model=out/'model.pkl';model.write_bytes(pickle.dumps((g,h,b,q,after),protocol=5));delta=out/'only-exact-coupled-discrete-and-new-native-fill-negative-delta.pkl';delta.write_bytes(pickle.dumps({'new_tracks':nt,'changed_only_NEW_vias':changed,'native_deleted_chunks':deleted,'retired_current_NEW_track_UUIDs':retired,'exact_new_chunks':chunks,'actual_fill_cut_ledger':ledger,'explicit_source_cache_restoration_parent_R552':sha(mp),'all_generated_roles_and_settings_exact':True},protocol=5));put(out/'incremental-immutable-current-native-filled-cut-ledger.json',ledger);put(out/'exact-current-role-precision-restoration.json',precision)
 rec={'verdict':'EXACT_CURRENT_DIC_POLICY_COUPLED_COMPOSITION_CONSTRUCTIVE_INDEPENDENT_ALL_GATES_OPEN','constructor_receipt_SHA256':sha(rp),'constructor_raw_old_reference_expression_failures_preserved':rr['strict_retained_reference_losses'],'only_retired_DIC_source_cache_parent_model_SHA256':sha(mp),'source_native_parent_SHA256':sha(sp),'model_file':str(model.resolve()),'model_SHA256':sha(model),'sparse_discrete_and_current_fill_delta_file':str(delta.resolve()),'sparse_delta_SHA256':sha(delta),'native_original_deletes':2,'retired_unaccepted_NEW_target_transport_tracks':8,'changed_only_NEW_ordinary_vias':3,'new_track_count':len(nt),'all_current_q_g_b_FP_header_source_rules_and_unrelated_Cu_exact':True,'actual_current_fill_records_changed_only_scoped_NEW_primitive_subtractions_with_local_no_gain_reserves':True,'changed_net_list_for_full_contact_audit':sorted(changednets),'native_effective_true_Cu_all6_hole_SMD_cap_ordinary_policy_native_keepouts':'OPEN','all81_plus_FAULT_actual_contact_layer_source_return_reference_newbody_minfeature_current':'OPEN','all_inherited_CORE_ROOT42_R368_28ref_R7_loop_capacity_native_raw_failures_preserved':True,'native_jobs':0,'board_source_project_written':False,'adopted':False,'input_SHA256':{str(f.resolve()):sha(f)for f in(Path(__file__),rp,pf,mp,sp,Path(MS.__file__),Path(IM.__file__))},'output_SHA256':{str(f.resolve()):sha(f)for f in out.iterdir()if f.is_file()},'elapsed_seconds':time.monotonic()-st};put(out/'receipt.json',rec);print('R556_COMPLETE',sha(out/'receipt.json'),rec['model_SHA256'],len(ledger),flush=True)
if __name__=='__main__':main()
