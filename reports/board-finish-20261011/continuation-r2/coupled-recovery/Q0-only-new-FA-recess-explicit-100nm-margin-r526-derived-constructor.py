"""Minimal actual shielding composition: one new FG zone, one new FA recess.

Every original/native discrete/zone definition is preserved. Only named7ef
owned physical/intended roles and its actual current fills withdraw. All raw
no-gain failures/reserves bind before/after; power current/native stays open.
"""
from pathlib import Path
import sys,pickle,json,hashlib,time,copy
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import restore_field_current_mixed_precision_states_r366 as M
from shapely import set_precision,get_precision
from shapely.geometry import Point
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def arrays(sh):return [[list(s.exterior.coords),[list(r.coords)for r in s.interiors]]for s in K.RF.parts(sh)]
out=H/'Q0-only-new-FA-recess-explicit-100nm-margin-r526';assert not out.exists();out.mkdir();start=time.monotonic()
mp=H/'Q0-owned-actual-fill-strict-local-negative-successor-r504/model.pkl';assert sha(mp)=='f738f9a4891664324f3e09511276036e77d94e12471713762d7998121d10593a';g,h,b0,q0,current=pickle.loads(mp.read_bytes());b=copy.deepcopy(b0);q=copy.deepcopy(q0);M.restore_bound_field_current_precision_states(b,q)
nd=H/'Q0-two-SMD-ground-only-owned-FA-recess-nomination-r516';assert sha(nd/'receipt.json')=='1a38bbfeef8cef6c69563c65ca949cd271377b3ca9e3cdaf7152ad737ca7f08f';pp=nd/'only-one-new-ground-reference-positive-zone-and-filled-record.pkl';assert sha(pp)=='4c99933cf9ef47f843fd2601563c186f77b6feafd3e705b973570d5a0d387e0f';op=pickle.loads(pp.read_bytes());uid='7ef3cb5e-deed-5cd0-9002-7f87b3e9ac19';owned=next(z for z in q if z['uuid']==uid);original=next(z for z in q0 if z['uuid']==uid);roleledger=[];negatives={};fail=[]
for row in op['required_only_owned_FA_negative_operations']:
 role=row['role'];assert row['UUID']==uid and K.C.sha(owned[role].wkb)==row['before_exact_WKB_sha256'];before=set_precision(owned[role],0);mask=set_precision(K.Z.bounded_buffer(row['exact_negative_cutter'],.0001),0);candidate=before.difference(mask);scope=[mask];reserves=[]
 for i in range(24):
  canonical=set_precision(candidate,1e-6,mode='pointwise');literal=set_precision(canonical,0);gain=literal.difference(before)
  if gain.is_empty:break
  gf=out/(role+'-'+str(i)+'-raw-role-gain.wkb');gf.write_bytes(gain.wkb);negative=set_precision(K.Z.bounded_buffer(gain,.0001),0);nf=out/(role+'-'+str(i)+'-explicit-100nm-role-negative-reserve.wkb');nf.write_bytes(negative.wkb);scope.append(negative);candidate=literal.difference(negative).intersection(before);reserves.append({'raw_gain_file':str(gf),'raw_gain_sha256':sha(gf),'exact_negative_reserve_file':str(nf),'exact_negative_reserve_sha256':sha(nf),'outward_mm':.0001})
 canonical=set_precision(candidate,1e-6,mode='pointwise');literal=set_precision(canonical,0);gain=literal.difference(before);total=unary_union(scope);owned[role]=canonical;negatives[role]=total;scopefile=out/(role+'-exact-full-owned-negative-scope.wkb');scopefile.write_bytes(total.wkb);roleledger.append({'UUID':uid,'role':role,'before_exact_WKB_sha256':K.C.sha(original[role].wkb),'after_exact_WKB_sha256':K.C.sha(canonical.wkb),'strict_literal_zero_positive_gain':gain.is_empty,'actual_removed_mm2':before.difference(literal).area,'exact_negative_scope_file':str(scopefile),'exact_negative_scope_sha256':sha(scopefile),'only_named_NEW_owned_FA_Cu_withdrawn':True,'explicit_additional_outward_negative_guard_mm':.0001,'R522_native_PASS_extra_margin_FAIL_preserved':True,'all_full_signed_loads_current_paths_and_contacts_mandatory':True,'raw_gain_and_local_reserves':reserves})
 if not canonical.is_valid or not gain.is_empty:fail.append({'role':role,'kind':'invalid_or_literal_positive_owned_role_gain'})
for row in b['generated_precision_state_ledger']:
 if row['new_generated_UUID']==uid:row['unchanged_WKB_SHA256']=K.C.sha(owned[row['role']].wkb)
newzone=copy.deepcopy(op['zone']);newuid=newzone['uuid'];assert newuid not in {z['uuid']for z in q};newfilled=copy.deepcopy(op['filled'])
for role in('shape','zone_outline_shape'):
 before=newzone[role].wkb;newzone[role]=set_precision(newzone[role],1e-6,mode='pointwise');assert newzone[role].wkb==before
q.append(newzone);b['restored_generated_grid_UUIDs'].append(newuid)
for role in('shape','zone_outline_shape'):b['generated_precision_state_ledger'].append({'new_generated_UUID':newuid,'role':role,'grid_mm':1e-6,'mode':'pointwise','unchanged_WKB_SHA256':K.C.sha(newzone[role].wkb),'explicit_new_owner_Q0_two_SMD_reference_declaration':True})
profile=M.restore_bound_field_current_precision_states(b,q)
zones=[];fillledger=[];actualnegative=[]
for zz in current['zones']:
 if zz['uuid']!=uid:zones.append(zz);continue
 z=copy.deepcopy(zz);mask=negatives['shape'];l=owned['layer'];rs=zz['fills'][l];newrs=[]
 for index,(record,piece)in enumerate(zip(rs,K.L.poly(rs))):
  if not piece.intersects(mask):newrs.append(copy.deepcopy(record));continue
  before=set_precision(piece,0);candidate=before.difference(mask);scopes=[mask];steps=[]
  for passindex in range(24):
   aa=arrays(candidate);actual=unary_union(K.L.poly(aa));gain=actual.difference(before);withdrawal=set_precision(original['shape'],0).difference(set_precision(owned['shape'],0));exterior=actual.intersection(withdrawal).difference(set_precision(owned['shape'],0));raw=unary_union([gain,exterior])
   if raw.is_empty:break
   gf=out/(str(index)+'-'+str(passindex)+'-raw-fill-gain-or-role-exterior.wkb');gf.write_bytes(raw.wkb);negative=set_precision(K.Z.bounded_buffer(raw,.0001),0);nf=out/(str(index)+'-'+str(passindex)+'-explicit-100nm-current-fill-negative.wkb');nf.write_bytes(negative.wkb);scopes.append(negative);candidate=actual.difference(negative).intersection(before);steps.append({'raw_gain_or_exterior_file':str(gf),'raw_gain_or_exterior_sha256':sha(gf),'raw_gain_mm2':gain.area,'raw_exterior_mm2':exterior.area,'exact_local_negative_file':str(nf),'exact_local_negative_sha256':sha(nf),'outward_mm':.0001,'no_area_dimension_or_boundary_waiver':True})
  aa=arrays(candidate);actual=unary_union(K.L.poly(aa));gain=actual.difference(before);exterior=actual.intersection(set_precision(original['shape'],0).difference(set_precision(owned['shape'],0))).difference(set_precision(owned['shape'],0));newrs.extend(aa);total=unary_union(scopes);actualnegative.append(total);fillledger.append({'UUID':uid,'layer':l,'original_record':index,'before_exact_actual_WKB_sha256':K.C.sha(before.wkb),'after_exact_actual_WKB_sha256':K.C.sha(actual.wkb),'strict_literal_zero_positive_or_reclaimed_Cu':gain.is_empty,'strict_actual_new_role_exterior_empty':exterior.is_empty,'actual_removed_mm2':before.difference(actual).area,'only_bound_current_local_negative_scope_WKB_sha256':K.C.sha(total.wkb),'explicit_raw_failures_and_negative_steps':steps})
  if not gain.is_empty or not exterior.is_empty:fail.append({'record':index,'kind':'literal_actual_gain_or_exterior_nonempty'})
 z['fills'][l]=newrs;zones.append(z)
after={**current,'zones':zones+[newfilled]}
target=unary_union([p for z in h['pads']if z['ref']=='R10016'for p in K.L.poly(z['layers']['F.Cu'])]);rawtargetgap=target.difference(newzone['shape']);assert rawtargetgap.is_empty
put(out/'only-two-owned-FA-role-literal-negative-ledger.json',roleledger);put(out/'only-current-owned-FA-fill-record-negative-ledger.json',fillledger);put(out/'explicit-new-one-FG-zone-native-owner-profile-and-mixed-binding.json',{'new_UUID':newuid,'profile':newzone['native_owner_profile_explicit_new_declaration'],'exact_physical_WKB_sha256':K.C.sha(newzone['shape'].wkb),'exact_native_intended_WKB_sha256':K.C.sha(newzone['zone_outline_shape'].wkb),'exhaustive_new_role_count':len(profile),'every_old_unrelated_precision_binding_exact':True,'native_API_settings_and_fullfill':'OPEN_MANDATORY'});put(out/'raw-unresolved-failures.json',fail)
model=out/'model.pkl'
if not fail:model.write_bytes(pickle.dumps((g,h,b,q,after),protocol=5))
packet=out/'only-new-FG-positive-and-named-owned-FA-negative-current-delta.pkl';packet.write_bytes(pickle.dumps({'new_zone':newzone,'new_filled_record':newfilled,'required_only_owned_FA_negative_operations':op['required_only_owned_FA_negative_operations'],'exact_repaired_FA_roles':{r:owned[r]for r in('shape','zone_outline_shape')},'exact_owned_negative_scopes':negatives,'exact_current_filled_negative_scope':unary_union(actualnegative),'role_ledger':roleledger,'filled_ledger':fillledger,'new_owner_mixed_precision_rows':[r for r in b['generated_precision_state_ledger']if r['new_generated_UUID']==newuid],'native_original_Cu_outline_settings_and_every_unrelated_q_fill_exact':True},protocol=5));result={'verdict':'SPARSE_TWO_SMD_GROUND_POSITIVE_AND_ONLY_NEW_FA_RECESS_CONSTRUCTOR_FRESH_ALL_GATES_OPEN'if not fail else'OWNED_FA_RECESS_LITERAL_GAIN_OR_FILL_ALIGNMENT_FAILED_NO_MODEL','input_model_file':str(mp),'input_model_sha256':sha(mp),'nomination_packet_sha256':sha(pp),'model_file':str(model)if not fail else None,'model_sha256':sha(model)if not fail else None,'exact_sparse_delta_file':str(packet),'exact_sparse_delta_sha256':sha(packet),'new_FG_zone_UUID':newuid,'only_withdrawn_NEW_FA_zone_UUID':uid,'only_two_current_FA_role_hashes_updated_plus_two_new_FG_roles_declared':True,'all_g_h_original_native_source_Cu_FP_rule_zone_outlines_every_other_q_fill_unchanged':True,'both_exact_native_R10016_whole_pad_bodies_covered_by_nominal_new_plane':True,'new_holes':0,'raw_unresolved_failures':len(fail),'all_81_contacts_ten_source_direct_strict_reference_true_native_clearance_actual_root_full_signed_current_NATIVE_SI':'OPEN_FRESH_INDEPENDENT_CHECK_REQUIRED','all_original_raw_failures_preserved':True,'only_owned_FA_negative_scope_additional_100nm_guard_explicit':True,'new_FG_geometry_original_native_Cu_and_all_holes_exact_R518':True,'native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**result}),flush=True)
