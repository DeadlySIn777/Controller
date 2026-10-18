"""Replay exact masks plus explicit local no-gain reserves on four roles.

Every unmodified role and every remote current filled array stays exact.
No global projection, original native snap, positive gain, or flag flip.
"""
from pathlib import Path
import sys,pickle,json,hashlib,copy,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
import restore_field_current_mixed_precision_states_r366 as M
from shapely import set_precision,get_precision
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def arr(sh):return[[list(p.exterior.coords),[list(r.coords)for r in p.interiors]]for p in K.RF.parts(sh)]
out=H/'Q0-owned-roles-literal-negative-canonical-r488';assert not out.exists();out.mkdir();start=time.monotonic();mp=H/'Q0-exact-R476-ground-contact-pose-r478/model.pkl';assert sha(mp)=='aec47d8600135e340be9e38ca18891e2903e7c283ee0b7095673d383ce079ebd';g,h,b0,q0,current=pickle.loads(mp.read_bytes());b=copy.deepcopy(b0);q=copy.deepcopy(q0);restored=M.restore_bound_field_current_precision_states(b,q);opsfile=H/'Q0-current-owned-role-antipad-masks-r486/only-current-owned-roles-exact-negative-masks.pkl';assert sha(opsfile)=='b2a9a31248eefe42a961591ef23e864b1eb0a9ea332604b94763fc0584c36d30';ops=pickle.loads(opsfile.read_bytes());by={z['uuid']:z for z in q};rows=[];scope={};fail=[]
for op in ops:
 uid,role=op['UUID'],op['role'];z=by[uid];before=set_precision(z[role],0);assert K.C.sha(before.wkb)==op['before_WKB_sha256'];mask=set_precision(op['exact_negative_mask'],0);negative=[mask];candidate=before.difference(mask);reserves=[]
 for i in range(24):
  canonical=set_precision(candidate,1e-6,mode='pointwise')
  if not canonical.is_valid:fail.append({'UUID':uid,'role':role,'kind':'invalid_nm_geometry'});break
  literal=set_precision(canonical,0);gain=literal.difference(before)
  if gain.is_empty:break
  stem=uid+'-'+role+'-'+str(i);gf=out/(stem+'-raw-literal-gain.wkb');gf.write_bytes(gain.wkb);reserve=set_precision(K.Z.bounded_buffer(gain,.0001),0);rf=out/(stem+'-explicit-100nm-negative-reserve.wkb');rf.write_bytes(reserve.wkb);negative.append(reserve);candidate=literal.difference(reserve).intersection(before);reserves.append({'gain_file':str(gf),'gain_sha256':sha(gf),'negative_reserve_file':str(rf),'negative_reserve_sha256':sha(rf),'outward_bound_mm':.0001,'gain_bounds_mm':gain.bounds,'no_area_threshold':True})
 canonical=set_precision(candidate,1e-6,mode='pointwise');literal=set_precision(canonical,0);gain=literal.difference(before);removed=before.difference(literal);total=unary_union(negative)
 if not gain.is_empty:fail.append({'UUID':uid,'role':role,'kind':'literal_positive_gain','gain_mm2':gain.area});(out/(uid+'-'+role+'-unresolved-gain.wkb')).write_bytes(gain.wkb)
 assert get_precision(canonical)==1e-6;z[role]=canonical;scope[(uid,role)]=total;rows.append({'UUID':uid,'role':role,'before_WKB_sha256':K.C.sha(before.wkb),'after_WKB_sha256':K.C.sha(canonical.wkb),'literal_zero_grid_no_gain':gain.is_empty,'removed_mm2':removed.area,'exact_mask_plus_new_local_negative_scope_WKB_sha256':K.C.sha(total.wkb),'new_integer_nm_boundary':True,'local_negative_reserves':reserves});(out/(uid+'-'+role+'-actual-full-negative-scope.wkb')).write_bytes(total.wkb)
# Bind exactly four changed role hashes in the exhaustive current 96-row map.
for row in b['generated_precision_state_ledger']:
 key=(row['new_generated_UUID'],row['role'])
 if key in scope:row['unchanged_WKB_SHA256']=K.C.sha(by[key[0]][key[1]].wkb)
validated=M.restore_bound_field_current_precision_states(b,q);zones=[];fillrows=[]
for oldz in current['zones']:
 key=(oldz['uuid'],'shape');mask=scope.get(key)
 if mask is None:zones.append(oldz);continue
 z=copy.deepcopy(oldz)
 for layer,records in oldz['fills'].items():
  if layer!=by[oldz['uuid']]['layer']:continue
  newrecords=[]
  for index,(record,piece)in enumerate(zip(records,K.L.poly(records))):
   if not piece.intersects(mask):newrecords.append(copy.deepcopy(record));continue
   before=set_precision(piece,0);remaining=before.difference(mask);reserves=[]
   for i in range(24):
    arrays=arr(remaining);actual=unary_union(K.L.poly(arrays));gain=actual.difference(before)
    if gain.is_empty:break
    stem=oldz['uuid']+'-'+layer+'-'+str(index)+'-'+str(i);gf=out/(stem+'-filled-raw-literal-gain.wkb');gf.write_bytes(gain.wkb);reserve=set_precision(K.Z.bounded_buffer(gain,.0001),0);rf=out/(stem+'-filled-explicit-100nm-negative-reserve.wkb');rf.write_bytes(reserve.wkb);remaining=actual.difference(reserve).intersection(before);reserves.append({'raw_gain_file':str(gf),'raw_gain_sha256':sha(gf),'negative_reserve_file':str(rf),'negative_reserve_sha256':sha(rf),'reserve_mm':.0001})
   arrays=arr(remaining);actual=unary_union(K.L.poly(arrays));gain=actual.difference(before)
   if not gain.is_empty:fail.append({'UUID':oldz['uuid'],'layer':layer,'record':index,'kind':'literal_actual_filled_gain'});(out/(stem+'-unresolved-filled-gain.wkb')).write_bytes(gain.wkb)
   newrecords.extend(arrays);fillrows.append({'UUID':oldz['uuid'],'layer':layer,'original_record':index,'before_WKB_sha256':K.C.sha(before.wkb),'after_WKB_sha256':K.C.sha(actual.wkb),'strict_no_new_or_reclaimed_filled_Cu':gain.is_empty,'actual_removed_mm2':before.difference(actual).area,'exact_scoped_new_primitive_and_new_role_negative_only':True,'local_negative_reserves':reserves})
  z['fills'][layer]=newrecords
 zones.append(z)
after={**current,'zones':zones};changed={(o['UUID'],o['role'])for o in ops}
for old,z in zip(q0,q):
 for key in old:
  if (old['uuid'],key)in changed:continue
  assert old[key].wkb==z[key].wkb if hasattr(old[key],'wkb')else old[key]==z[key]
put(out/'all-four-roles-strict-literal-canonical-negative-ledger.json',rows);put(out/'immutable-actual-filled-only-new-negative-alignment-ledger.json',fillrows);put(out/'raw-unresolved-no-gain-failures.json',fail);put(out/'exact-mixed-current-precision-binding-and-restoration-ledger.json',{'initial':restored,'validated_after_exact_four_role_hash_updates':validated});modelout=out/'model.pkl'
if not fail:modelout.write_bytes(pickle.dumps((g,h,b,q,after),protocol=5))
delta=out/'only-four-current-role-negative-masks-and-canonical-replacements.pkl';delta.write_bytes(pickle.dumps({'operations':ops,'repaired_role_rows':rows,'repaired_roles':{key:by[key[0]][key[1]]for key in changed},'explicit_exact_negative_scopes':scope,'actual_current_filled_alignment_rows':fillrows},protocol=5));result={'verdict':'FOUR_CURRENT_OWNED_ROLE_CANONICAL_LITERAL_NEGATIVE_REPLAY_COMPLETE_FRESH_ALL_GATES_OPEN'if not fail else'STRICT_LITERAL_ROLE_OR_ACTUAL_FILL_GAIN_FAIL_NO_MODEL','parent_actual_current_model_sha256':sha(mp),'only_exact_negative_mask_packet_sha256':sha(opsfile),'new_model_file':str(modelout)if not fail else None,'new_model_sha256':sha(modelout)if not fail else None,'sparse_delta_file':str(delta),'sparse_delta_sha256':sha(delta),'changed_current_roles':len(rows),'changed_actual_filled_record_rows':len(fillrows),'raw_unresolved_gain_failures':len(fail),'all_g_h_original_native_source_geometry_every_other_q_profile_and_every_far_filled_record_exact':True,'only_four_mixed_precision_hashes_updated_no_other_b_flags_changed':True,'all_raw_R155_R368_R486_CORE_ROOT42_inherited_B_SMD_native_current_failures_preserved':True,'source_contact_ZERO_old_reference_same_plane_new_body_current_native_DRC_SI':'OPEN_FRESH_REAUDIT_REQUIRED','native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start};put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**result}),flush=True)
