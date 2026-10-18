"""Exact scoped owned-fill subtraction with strict per-record provenance."""
import sys,json,pickle,copy,time
from pathlib import Path
H=Path(__file__).resolve().parent;sys.dont_write_bytecode=True
for p in(H.parent/'field-power',H.parent/'sbc-power',H):sys.path.insert(0,str(p))
import audit_aux_exact_raw as A
import contact_layout as L
import physical_reference_losses_r3_zero_r208 as RF
import restore_SAFE_generated_precision_states_r168 as PS
import guarded_power_projection_r44 as Z
from shapely import set_precision
from shapely.geometry import box,Point
from shapely.ops import unary_union
C=A.C;O=H/'CORE-R112-per-polygon-immutable-owned-construction-r250'
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def records(sh):return [[list(p.exterior.coords),[list(r.coords)for r in p.interiors]]for p in RF.parts(sh)]
def main():
 started=time.monotonic();assert not O.exists();O.mkdir()
 base=H.parent/'field-power/R54-native-wider-IO3-monitor-joint-audit-r214/model.pkl';raw0=A.read(base);assert C.sha(raw0)=='87e997c79f7815f801f5c567b9f848aeb98640380f5856a2724dc1bb177dfa0e';g0,h0,b0,q0,c0=pickle.loads(raw0);op=PS.restore_bound_generated_precision_states(b0,q0)
 candidate=H.parent/'CORE-wide-reserved-IO3-immutable-R214-materialized-r112';receipt=A.read(candidate/'receipt.json');assert C.sha(receipt)=='94a8a335edcda606c0c64f94ae77597815b6206f80dfef13fe5e2422ca460680';raw=A.read(candidate/'model.pkl');assert C.sha(raw)=='6312b10a88b2d3614e21760d1709866d2417b419d418e20e09055eb13b8e3b7e';g,h,b,q,c=pickle.loads(raw);np=PS.restore_bound_generated_precision_states(b,q);assert g==g0;by0={z['uuid']:z for z in q0};oldactual={z['uuid']:z for z in c0['zones']};newactual={z['uuid']:z for z in c['zones']};by={z['uuid']:z for z in q};assert set(by)==set(by0)|{'b0453302-df03-561f-9bc4-0560bc66658a'};ledger=[];failures=[];outzones=copy.deepcopy(c['zones']);outmap={z['uuid']:z for z in outzones};witness=box(267.142249857124,185.81632585369508,267.2323231270132,186.00910215737292)
 for uid,z in by.items():
  if uid not in by0:
   ledger.append({'UUID':uid,'new_CORE_only_filled_records_exact_R112':True,'filled_WKB_sha256':C.sha(unary_union(L.poly(newactual[uid]['fills'][z['layer']])).wkb)});continue
  old=by0[uid];assert old['layer']==z['layer'];a,n=old['shape'],z['shape'];assert n.difference(a).is_empty;withdrawal=a.difference(n);wr0=withdrawal.wkb;cut=set_precision(withdrawal,0);assert cut.wkb==wr0;(O/(uid+'.exact-role-withdrawal.wkb')).write_bytes(wr0);before=oldactual[uid];layer=z['layer'];before_records=before['fills'][layer];primitive=[];oldvia={v['uuid']for v in h0['vias']};newvia=[v for v in h['vias']if v['uuid']not in oldvia];assert len(newvia)==2;newcore=by['b0453302-df03-561f-9bc4-0560bc66658a'];dom=h['domains_normalized'];domain_gap=lambda a,b:.15 if dom.get(L.norm(a))==dom.get(L.norm(b))else .6
  for via in newvia:
   same=L.norm(z['net'])==L.norm(via['net']);radius=via['drill']/2 if same else max(via['drill']/2+.275+.0001,via['d']/2+max(float(z['clearance_mm']),domain_gap(z['net'],via['net']))+.025+.0001);mask=Z.bounded_disk(via,radius);mask_zero=set_precision(mask,0);assert mask_zero.wkb==mask.wkb;mf=O/(uid+'-'+via['uuid']+'-exact-new-ordinary-filled-cut.wkb');mf.write_bytes(mask.wkb);primitive.append({'new_UUID':via['uuid'],'kind':'same_raw_net_new_drill'if same else'new_ordinary_foreign_annulus_drill_antipad','radius_mm':radius,'cut_WKB_file':str(mf),'cut_WKB_sha256':C.sha(mask.wkb),'shape':mask_zero})
  if layer==newcore['layer']and L.norm(z['net'])!=L.norm(newcore['net']):
   clear=max(float(z['clearance_mm']),domain_gap(z['net'],newcore['net']))+.025+.0001;mask=Z.bounded_buffer(newcore['shape'],clear);mask_zero=set_precision(mask,0);assert mask_zero.wkb==mask.wkb;mf=O/(uid+'-new-CORE-body-filled-cut.wkb');mf.write_bytes(mask.wkb);primitive.append({'new_UUID':newcore['uuid'],'kind':'new_CORE_body_foreign_actual_filled_cut','clearance_with_guard_mm':clear,'cut_WKB_file':str(mf),'cut_WKB_sha256':C.sha(mask.wkb),'shape':mask_zero})
  cut=unary_union([cut,*[r['shape']for r in primitive]]);pieces=L.poly(before_records);assert len(pieces)==len(before_records);new_records=[];steps=[]
  for i,(rec,p)in enumerate(zip(before_records,pieces)):
   pzero=set_precision(p,0);assert pzero.wkb==p.wkb
   if cut.is_empty or not cut.intersects(pzero):
    new_records.append(copy.deepcopy(rec));steps.append({'record':i,'before_WKB_sha256':C.sha(p.wkb),'untouched_record_arrays_exact':True});continue
   remaining=pzero.difference(cut);clip=[]
   for iteration in range(16):
    gain=remaining.difference(pzero)
    if gain.is_empty:break
    seed=O/(uid+'-'+str(i)+'-'+str(iteration)+'-raw-positive-filled-gain.wkb');seed.write_bytes(gain.wkb)
    reserve=Z.bounded_buffer(gain,.0001);reserve_zero=set_precision(reserve,0);assert reserve_zero.wkb==reserve.wkb
    rf=O/(uid+'-'+str(i)+'-'+str(iteration)+'-explicit-100nm-local-filled-reserve.wkb');rf.write_bytes(reserve.wkb)
    previous=remaining;remaining=remaining.difference(reserve_zero).intersection(pzero)
    removed=previous.difference(remaining);negative=O/(uid+'-'+str(i)+'-'+str(iteration)+'-actual-local-filled-withdrawal.wkb');negative.write_bytes(removed.wkb)
    clip.append({'iteration':iteration,'actual_raw_gain_WKB_file':str(seed),'actual_raw_gain_WKB_sha256':C.sha(gain.wkb),'actual_raw_gain_mm2':gain.area,'local_reserve_cutter_file':str(rf),'local_reserve_WKB_sha256':C.sha(reserve.wkb),'reserve_nominal_mm':.0001,'only_local_new_generated_outward_bound_not_original_coordinate_snap':True,'actual_negative_filled_delta_file':str(negative),'actual_negative_delta_WKB_sha256':C.sha(removed.wkb),'actual_removed_mm2':removed.area,'bounded_to_exact_original_record_after_negative_cut':True})
   gain=remaining.difference(pzero);outside_withdrawal=pzero.difference(remaining).difference(cut);serialized=records(remaining);reconstructed=unary_union(L.poly(serialized));polygonal=unary_union(RF.parts(remaining));serialized_equal=reconstructed.equals(polygonal);geometry_state={'remaining_type':remaining.geom_type,'remaining_valid':remaining.is_valid,'polygonal_type':polygonal.geom_type,'polygonal_valid':polygonal.is_valid,'reconstructed_type':reconstructed.geom_type,'reconstructed_valid':reconstructed.is_valid,'raw_remaining_WKB_sha256':C.sha(remaining.wkb),'polygonal_WKB_sha256':C.sha(polygonal.wkb),'reconstructed_WKB_sha256':C.sha(reconstructed.wkb),'serialized_polygonal_exact':serialized_equal,'nonpolygonal_residue_never_counted_as_Cu_contact_or_reference':True};(O/(uid+'-'+str(i)+'-raw-before-record-reconstruction.wkb')).write_bytes(remaining.wkb);(O/(uid+'-'+str(i)+'-serialized-record-reconstruction.wkb')).write_bytes(reconstructed.wkb)
   gain=reconstructed.difference(pzero);outside_withdrawal=pzero.difference(reconstructed).difference(cut);ok=gain.is_empty and serialized_equal
   row={'record':i,'before_WKB_sha256':C.sha(p.wkb),'exact_record_withdrawal_WKB_sha256':C.sha(p.intersection(cut).wkb),'after_WKB_sha256':C.sha(reconstructed.wkb),'strict_no_new_Cu':gain.is_empty,'raw_original_role_only_scope_pass':outside_withdrawal.is_empty,'explicit_additional_negative_filled_withdrawal_WKB_sha256':C.sha(outside_withdrawal.wkb),'new_local_negative_withdrawals_authorized_separately_by_root_2026_10_12':True,'typed_geometry_and_serialization':geometry_state,'clip_only_to_exact_original_record_iterations':clip,'preserved_all_no_cut_records':True};steps.append(row);(O/(uid+'-'+str(i)+'-explicit-final-additional-negative-filled-withdrawal.wkb')).write_bytes(outside_withdrawal.wkb)
   if not ok:failures.append({'UUID':uid,'layer':layer,**row});(O/(uid+'-'+str(i)+'-strict-gain.wkb')).write_bytes(gain.wkb);(O/(uid+'-'+str(i)+'-strict-extra-loss.wkb')).write_bytes(outside_withdrawal.wkb)
   if reconstructed.wkb==p.wkb or(reconstructed.difference(p).is_empty and p.difference(reconstructed).is_empty):new_records.append(copy.deepcopy(rec))
   else:new_records.extend(serialized)
  finalfills=copy.deepcopy(before['fills']);finalfills[layer]=new_records;oldfull=unary_union(pieces);newfull=unary_union(L.poly(new_records));gain=newfull.difference(oldfull);extra=oldfull.difference(newfull).difference(cut);local=oldfull.difference(newfull).intersection(witness)if uid=='bde7a0cf-1ad7-5a04-b956-9f8848bb3f2a'else None
  row={'UUID':uid,'layer':layer,'old_role_WKB_sha256':C.sha(a.wkb),'new_role_WKB_sha256':C.sha(n.wkb),'exact_role_withdrawal_WKB_sha256':C.sha(wr0),'exact_NEW_primitive_owned_fill_cuts':[{k:v for k,v in row.items()if k!='shape'}for row in primitive],'exact_before_filled_WKB_sha256':C.sha(oldfull.wkb),'exact_after_filled_WKB_sha256':C.sha(newfull.wkb),'entire_filled_no_reclaimed_Cu':gain.is_empty,'raw_original_role_only_scope_pass':extra.is_empty,'entire_explicit_additional_negative_delta_WKB_sha256':C.sha(extra.wkb),'root_authorized_local_negative_filled_scope_native_current_and_all_source_reference_still_OPEN':True,'gain_mm2':gain.area,'extra_removal_mm2':extra.area,'all_record_operations':steps,'b1ba_exact_local_fill_loss_empty':local.is_empty if local is not None else None}
  ledger.append(row);outmap[uid]['fills']=finalfills;(O/(uid+'-entire-explicit-additional-negative-filled-withdrawal.wkb')).write_bytes(extra.wkb)
  if not gain.is_empty or(local is not None and not local.is_empty):failures.append({'kind':'complete_owned_strict_subset_authorized_local_boundary','UUID':uid,'gain_mm2':gain.area,'extra_removal_mm2':extra.area,'b1ba_local_loss_empty':local.is_empty if local is not None else None})
  put(O/'immutable-owned-record-ledger-progress.json',ledger);put(O/'strict-operation-failures-progress.json',failures);print('R250_OWNED_RECORD',uid,len(steps),'strict_failures',len(failures),flush=True)
 for z in c['zones']:
  if z['uuid']not in by0:assert outmap[z['uuid']]==z,'All actual native fills and new CORE records stay exact R112'
 current={**c,'zones':outzones};put(O/'immutable-owned-record-delta-ledger.json',ledger);put(O/'strict-operation-failures.json',failures);put(O/'bound-generated-role-operation-replay.json',{'R214':op,'R112':np});ok=not failures
 if ok:(O/'model.pkl').write_bytes(pickle.dumps((g,h,b,q,current),protocol=5))
 result={'verdict':'EXACT_R112_IMMUTABLE_OWNED_LOCAL_NEGATIVE_FILLED_RESERVE_CONSTRUCTOR_PASS_FULL_GATES_OPEN'if ok else'EXACT_PER_POLYGON_SCOPE_OR_SUBSET_FAIL_NO_MODEL_EMISSION','original_R214_model_sha256':C.sha(raw0),'R112_model_sha256':C.sha(raw),'R112_receipt_sha256':C.sha(receipt),'g_h_b_all_discrete_native_definition_and_q_physical_intended_profile_exact_R112':True,'every_current_native_and_new_CORE_filled_record_exact_R112':True,'all_untouched_owned_record_arrays_preserved_exact':True,'all_exact_empty_gain_required_no_tolerance':True,'actual_role_withdrawals_plus_explicit_root_authorized_local_negative_filled_delta':True,'strict_failures':failures,'no_native_or_global_projection_no_global_snap_no_tolerance':True,'local_negative_reserve_scope_authority':'Root 2026-10-12: explicit LOCAL remove-only reserves around literal gains on actual FILLED Cu only; all q physical/intended/settings stay exact; source/contact/reference/current/native requalification mandatory.','full_all77_source_directlayer_old_reference_new_body_current_native':'OPEN','native_jobs':0,'board_written':False,'adopted':False,'model_sha256':C.sha((O/'model.pkl').read_bytes())if ok else None,'read_files_sha256':A.READS,'output_files_sha256':{str(p):C.sha(p.read_bytes())for p in O.iterdir()if p.is_file()and p.name!='receipt.json'},'elapsed_seconds':time.monotonic()-started};put(O/'receipt.json',result);print(json.dumps({'receipt_sha256':C.sha((O/'receipt.json').read_bytes()),'constructor_pass':ok,'strict_failures':len(failures)}),flush=True)
if __name__=='__main__':main()
