"""Independent no-hole IO3 sparse byte/source/analytic-geometry diagnostic."""
import json,pickle,hashlib,sys,math,time,traceback,collections
from pathlib import Path
from shapely import set_precision
from shapely.geometry import Point,LineString
from shapely.ops import unary_union
from shapely.strtree import STRtree
H=Path(__file__).resolve().parent.parent
for d in('field-power','sbc-power','coupled-recovery'):sys.path.insert(0,str(H/d))
import contact_layout as L
import fast_contacts as F
import audit_aux_exact_raw as A
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import restore_field_current_mixed_precision_states_r366 as PS
import guarded_power_projection_r44 as Z
O=H/'sbc-power/CM79-R353-plus-no-hole-IO3-existing-annulus-current-independent-byte-source-native-proof-r360'
D=H/'sbc-power/CM79-R353-IO3-existing-actual-annulus-no-hole-fixed-Cu-bypass-nomination-r359'
NET='/IO_3V3'
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):Path(p).write_text(json.dumps(v,indent=1,allow_nan=False)+'\n',encoding='utf-8')
def zero(s):z=set_precision(s,0);assert z.wkb==s.wkb;return z
def signature(c,net):return pickle.dumps({k:[x for x in c[k]if L.norm(x['net'])==net]for k in('tracks','vias','pads','zones')},protocol=5)
def main():
 started=time.monotonic();assert not O.exists();O.mkdir();assert sha(D/'receipt.json')=='c31210bc9de28e39b50d08eb6281e268242b0a3e4e06f5b07bbe6dd2ffb4b893';r=json.loads((D/'receipt.json').read_text());assert r['winner'];sp=D/'only-new-IO3-existing-annulus-bypass-tracks-no-hole-no-delete.pkl';assert sha(sp)==r['new_sparse_sha256'];d=pickle.loads(sp.read_bytes());assert not d['vias']and not d['removed_original_UUIDs'];nt=d['tracks'];assert len(nt)==7 and all(t['w']==.5 and t['layer']=='In3.Cu'and t['net']==NET for t in nt);mp=H/'sbc-power/CM79-exact-R333-larger-power-port-local-q053-sparse-current-diagnostic-original-vertex-splice-r353/model.pkl';assert sha(mp)=='de8e2af4143fe43491773e0e0339c39efb17cb1660072bf37ffc6a22c155255e';g,h,b,q,c=pickle.loads(mp.read_bytes());roleBefore={(z['uuid'],rr):z[rr].wkb for z in q for rr in('shape','zone_outline_shape')};put(O/'exact-inherited-role-operation-metadata-restoration-no-coordinate-change.json',PS.restore_bound_field_current_precision_states(b,q));assert all(z[rr].wkb==roleBefore[z['uuid'],rr]for z in q for rr in('shape','zone_outline_shape'));existing={x['uuid']for k in('tracks','vias','pads')for x in h[k]};assert all(t['uuid']not in existing for t in nt);after={**c,'tracks':c['tracks']+nt};newh={**h,'tracks':h['tracks']+nt};source=H/'sbc-native-contract-r1/sbc-owned-native-contract.kicad_pcb';assert sha(source)=='eedf63f2c24346a885cebcabbd7546576663d5cbb29bc8dbd48401921201240a';raw=source.read_bytes();iv=A.C.inventory(raw);ident=A.N.SourceNets(raw);native={};ops=[]
 for t in nt:
  assert all(y==round(y,6)for y in t['a']+t['b']);assert ident.raw(L.norm(t['net']))==t['net'];chunk='\t(segment\n\t\t(start %.6f %.6f)\n\t\t(end %.6f %.6f)\n\t\t(width %.6f)\n\t\t(layer %s)\n\t\t(net %s)\n\t\t(uuid %s)\n\t)\n'%(*t['a'],*t['b'],t['w'],json.dumps(t['layer']),json.dumps(t['net']),json.dumps(t['uuid']));file=O/(t['uuid']+'.segment-chunk');file.write_text(chunk,encoding='utf-8',newline='');native[t['uuid']]=file.read_bytes();p=A.G.parse(t['uuid'],native[t['uuid']],{});assert(p['net'],p['w'],p['layer'],p['a'],p['b'])==(NET,t['w'],t['layer'],t['a'],t['b']);ops.append({'action':'add','kind':'segment','uuid':t['uuid'],'exact_chunk_path':str(file.resolve()),'exact_chunk_sha256':sha(file),'exact_geometry':t})
 ident.assert_chunks(native);put(O/'exact-only-seven-IO3-track-native-operation-ledger.json',ops);portRows=[]
 for key in('source_existing_annulus','detached_existing_annulus'):
  p=r['winner'][key];v=next(v for v in h['vias']if v['uuid']==p['UUID']);chunk=iv[3][v['uuid']];pv=A.G.parse(v['uuid'],chunk,{});assert(pv['net'],pv['d'],pv['drill'],pv['at'])==(NET,v['d'],v['drill'],[v['x'],v['y']]);file=O/(v['uuid']+'.exact-unchanged-native-source-via-chunk');file.write_bytes(chunk);portRows.append({'current_actual_annulus':p,'exact_original_native_chunk_path':str(file.resolve()),'exact_original_native_chunk_sha256':sha(file),'original_mask_unused_flags_pose_diameter_drill_exact':True,'new_route_layer_already_observed_current_native_In3_annulus':True})
 put(O/'exact-existing-source-port-native-identity-and-annulus-ledger.json',portRows);oldpacket=H/'sbc-power/CM79-R353-fresh-IO3-split-source-and-existing-annulus-port-attribution-r355/actual-IO3-before-after-groups.pkl';assert sha(oldpacket)=='be399f407a053b8cfeb6f3eecb41082b43d2663f57b19b1d2c45fed5168bd41d';oldbanks=pickle.loads(oldpacket.read_bytes());ctx=K.hole_context(after);_,fresh=K.physical(after,NET,ctx);currentProof,currentLoss=K.contact_losses(oldbanks['after'],fresh);parentProof,parentLoss=K.contact_losses(oldbanks['before'],fresh);root=K.root(fresh,'R18001','2');parentRoot=K.root(oldbanks['before'],'R18001','2');missing=sorted(K.keys(parentRoot)-K.keys(root));assert len(K.keys(parentRoot))==3689;put(O/'fresh-original-all-3689-and-current-IO3-source-group-proof.json',{'original_ancestor_group_relationships':parentProof,'original_ancestor_group_losses':parentLoss,'current_R353_group_relationships':currentProof,'current_R353_group_losses':currentLoss,'original_full3689_source_key_losses':[list(k)for k in missing]});(O/'fresh-actual-IO3-after-groups.pkl').write_bytes(pickle.dumps(fresh,protocol=5));unchangedBanks=[]
 for net,ref,pin in K.ROOTS+[('/mc_local_power/CORE_5V','R11022','2'),('/motherboard_motors/AUX_5V_B','U11014','6')]:
  if net==NET:continue
  exact=signature(c,net)==signature(after,net);assert exact;unchangedBanks.append({'net':net,'source':ref+'.'+pin,'exact_all_actual_native_discrete_and_filled_array_equality':True,'all_real_holes_and_original_via_used_layers_exact':True,'actual_graph_source_keys_direct_contacts_fill_only_references_mathematically_identical':True,'inherited_failed_gates_not_waived':True})
 put(O/'all-eight-other-prior-source-and-bank-reference-exact-no-hole-preservation.json',unchangedBanks);rec,trees=F.build(after,layers={'In3.Cu'});filled=[]
 for z in after['zones']:
  if 'In3.Cu'in z['fills']:filled.extend({'uuid':z['uuid'],'net':z['net'],'kind':'fill','local':float(z['clearance_mm']),'shape':sh}for sh in L.poly(z['fills']['In3.Cu']))
 for z in q:
  if z['layer']=='In3.Cu':filled.append({'uuid':z['uuid'],'net':z['net'],'kind':'owned_physical_zone','local':float(z['clearance_mm']),'shape':z['shape']})
 ft=STRtree([rr['shape']for rr in filled]);holes=[(v['uuid'],v['net'],Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=128))for v in h['vias']]+[(p['uuid'],p['net'],sh)for p in h['pads']for sh in L.poly(p.get('hole')or[])];ht=STRtree([sh for uid,net,sh in holes]);dom=h['domains_normalized'];gap=lambda a,bb:.15 if dom.get(L.norm(a))==dom.get(L.norm(bb))else .6;reserve,exempt=A.reservations();checks=[];nativeBad=[];planner=[]
 for t in nt:
  axis=LineString([t['a'],t['b']]);rad=t['w']/2;body=zero(Z.bounded_buffer(axis,rad));targets=[rec['In3.Cu'][int(i)]for i in trees['In3.Cu'].query(body.buffer(1),predicate='intersects')]+[filled[int(i)]for i in ft.query(body.buffer(1),predicate='intersects')]
  for rr in targets:
   if L.norm(rr['net'])==NET:continue
   if rr['kind']=='track'and not rr['source'].get('m'):x=rr['source'];dist=axis.distance(LineString([x['a'],x['b']]))-rad-x['w']/2
   elif rr['kind']=='via':v=rr['source'];dist=axis.distance(Point(v['x'],v['y']))-rad-v['d']/2
   else:dist=axis.distance(rr['shape'])-rad
   req=max(gap(NET,rr['net']),rr.get('local',0));row={'new_UUID':t['uuid'],'other_UUID':rr['uuid'],'kind':rr['kind'],'layer':'In3.Cu','actual_gap_mm':dist,'actual_native_required_mm':req,'conservative_new_planner_required_mm':req+.025};checks.append(row)
   if dist<req:nativeBad.append(row)
   if dist<req+.025:planner.append(row)
  for j in ht.query(body.buffer(.285),predicate='intersects'):
   uid,net,sh=holes[int(j)]
   if L.norm(net)==NET:continue
   dd=axis.distance(sh)-rad-.005;row={'new_UUID':t['uuid'],'other_UUID':uid,'kind':'every_foreign_real_hole_guard','actual_gap_with5um_guard_mm':dd,'required_mm':.275};checks.append(row)
   if dd<.275:nativeBad.append(row)
  for rr in h['rule_areas']:
   if 'In3.Cu'in rr['layers']and rr.get('no_tracks')and any(body.distance(sh)<.025 for sh in L.poly(rr['outline'])):nativeBad.append({'new_UUID':t['uuid'],'kind':'original_native_rule_area','rule':rr.get('name',rr.get('uuid'))})
  for rr in reserve['keepouts']:
   if 'In3.Cu'in rr['layers']and NET not in exempt.get(rr['name'],set())and any(body.distance(sh)<.025 for sh in L.poly(rr['outline'])):nativeBad.append({'new_UUID':t['uuid'],'kind':'exact_frozen_reserved_area','rule':rr['name']})
 put(O/'all-seven-new-analytic-Cu-hole-rule-geometry-ledger.json',checks);put(O/'new-actual-native-rule-errors.json',nativeBad);put(O/'new-extra-planner-deficits.json',planner);audit=H/'sbc-power/CM79-R353-fresh-all-current-source-native-reference-audit-r354';cache=audit/'actual-drilled-after-groups.pkl';assert sha(cache)=='339dbe2c2173388fa7384c697e6364dcf5b9c507e552e64836b08c55203ed4eb';lg=K.root(pickle.loads(cache.read_bytes())['/LOGIC_GND'],'J11001','2');ref=zero(unary_union([rr['shape']for rr in lg if rr['kind']=='fill'and rr['layer']=='In4.Cu']));bodyRefs=[]
 for t in nt:
  actual=zero(unary_union([rr['shape']for xs in fresh for rr in xs if rr['kind']=='track'and rr['uuid']==t['uuid']and rr['layer']=='In3.Cu']));lost=actual.difference(ref);file=O/(t['uuid']+'-raw-new-IO3-whole-body-source-fill-reference-gap.wkb');file.write_bytes(lost.wkb);bodyRefs.append({'UUID':t['uuid'],'actual_drill_subtracted_body_mm2':actual.area,'raw_MAP_In3_to_source_LG_In4_gap_EMPTY':lost.is_empty,'raw_gap_type':lost.geom_type,'raw_gap_mm2':lost.area,'raw_gap_WKB_sha256':sha(file),'no_generic_power_or_D4_signal_aperture_credit':True,'complete_signed_IO3_supply_return_loop_and_thermal':'OPEN'})
 put(O/'raw-all-seven-new-IO3-body-reference-and-open-loop-ledger.json',bodyRefs);length=sum(LineString([t['a'],t['b']]).length for t in nt);conditional=[];scenario=H/'sbc-power/signed-return-scenarios-r1.json';assert sha(scenario)=='e1b14aeafe8802907ae92cd5ceb8c0c9ad42bf7beaf343d6c3886cdc1da165af'
 for copper in(35,70):
  for temp in(20,60,100,125):
   rho=1.7241e-8*(1+.00393*(temp-20));rr=rho*length*.001/(.0005*copper*.000001);conditional.append({'hypothetical_all2A_IO3_bypass_stress_A':2,'conditional_copper_um':copper,'conditional_Cu_C':temp,'actual_trace_length_mm':length,'ordinary_width_mm':.5,'conditional_trace_resistance_ohm':rr,'conditional_trace_only_drop_mV':2*rr*1000,'conditional_trace_only_loss_W':4*rr,'actual_branch_allocation_both_existing_0p5_0p2_barrel_plating_spreading_whole_loop_thermal_and_capacity':'OPEN','no_equalshare_capacity_or_total_loop_drop_claim':True})
 put(O/'conditional-conserved-total-IO3-two-A-bypass-trace-only-drop.json',conditional);put(O/'exact-sparse-preservation-contract.json',{'original_pads_pose_native_zones_current_fill_arrays_owned_WKB_source_settings_via_flags_and_real_holes_exact':all(c[k]==after[k]for k in c if k!='tracks')and all(h[k]==newh[k]for k in h if k!='tracks')and all(z[rr].wkb==roleBefore[z['uuid'],rr]for z in q for rr in('shape','zone_outline_shape')),'original_IO3_3689_keys_restored':not missing and not parentLoss,'current_IO3_contacts_zero_loss':not currentLoss,'all_other_eight_source_graphs_direct_contacts_and_ground_oldrefs_exact':True,'no_new_holes_no_native_filled_or_owned_role_operations':True});(O/'only-seven-IO3-tracks-no-hole-no-delete.pkl').write_bytes(pickle.dumps(d,protocol=5));(O/'model.pkl').write_bytes(pickle.dumps((g,newh,b,q,after),protocol=5));result={'verdict':'CM79_PLUS_IO3_NO_HOLE_SOURCE_REPAIR_DIAGNOSTIC_FRESH_GATES','exact_parent_R353_model_sha256':sha(mp),'R359_nomination_receipt_sha256':sha(D/'receipt.json'),'model_sha256':sha(O/'model.pkl'),'sparse_discrete_sha256':sha(O/'only-seven-IO3-tracks-no-hole-no-delete.pkl'),'new_ordinary_In3_track_count':len(nt),'new_width_mm':.5,'new_actual_length_mm':length,'new_holes_deletes_owned_roles_native_fill_changes':0,'original_all3689_IO3_source_layer_key_loss_count':len(missing),'original_IO3_group_loss_count':len(parentLoss),'current_R353_IO3_group_loss_count':len(currentLoss),'other_eight_prior_source_graphs_and_all_three_banks_oldrefs_exact':True,'new_actual_native_geometry_error_count':len(nativeBad),'new_extra_planner_deficit_count':len(planner),'new_IO3_raw_body_reference_FAIL_count':sum(not row['raw_MAP_In3_to_source_LG_In4_gap_EMPTY']for row in bodyRefs),'all_inherited_CORE93_six_R7_reserve_CM1_original_TMR_and_power_raw_body_current_thermal_native_fault_flags':'FAIL_OR_OPEN_RETAINED','all_full_signed_IO3_CORE5_GND_mesh_current_drop_thermal_capacity_and_native':'OPEN','native_jobs':0,'adopted':False,'elapsed_seconds':time.monotonic()-started,'script_sha256':sha(__file__)};put(O/'receipt.json',result);print('R360_COMPLETE',sha(O/'receipt.json'),json.dumps(result),flush=True)
if __name__=='__main__':
 try:main()
 except Exception:
  if O.exists():put(O/'failure.json',{'traceback':traceback.format_exc(),'script_sha256':sha(__file__)})
  raise
