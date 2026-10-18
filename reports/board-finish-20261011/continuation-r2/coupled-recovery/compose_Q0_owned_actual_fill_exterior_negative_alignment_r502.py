"""Local actual-filled-only withdrawal around literal new-role exterior.

R488 g/h/b/q/native definitions/settings stay exact. No original boundary
snap, threshold, gained/reclaimed fill or broad role reconstruction.
"""
from pathlib import Path
import sys,pickle,json,hashlib,copy,time
H=Path(__file__).resolve().parent;P=H.parent
for d in(P/'field-power',P/'sbc-power',H):sys.path.insert(0,str(d))
import audit_DIC_C1022_actual_R214_full77_and_signals_r220 as K
from shapely import set_precision
from shapely.ops import unary_union
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def put(p,v):p.write_text(json.dumps(v,indent=1,allow_nan=False)+'\n')
def arrays(sh):return [[list(s.exterior.coords),[list(r.coords)for r in s.interiors]]for s in K.RF.parts(sh)]
out=H/'Q0-owned-actual-fill-exterior-negative-alignment-r502';assert not out.exists();out.mkdir();start=time.monotonic()
mp=H/'Q0-owned-roles-literal-negative-canonical-r488/model.pkl';assert sha(mp)=='1b2c6f54ab37e90c415a2e053862d8d8e35f3767b4e2130555bb307458cf075e';g,h,b,q,current=pickle.loads(mp.read_bytes())
bm=P/'R5051-own-drill-intended-only-current-R364-rebase-r155/model.pkl';assert sha(bm)=='ff9893e41f73f868d377357e114dab60a943379fc0c411a8629f609df96bc5b4';_,_,_,q0,_=pickle.loads(bm.read_bytes());oldq={z['uuid']:z for z in q0};newq={z['uuid']:z for z in q}
dd=H/'Q0-R488-actual-filled-exterior-membership-r500';assert sha(dd/'receipt.json')=='1d3801b3438e821eeb462cf3c7c1aceae9a31bef1552e4c668d9d16ff3f7ad74';diag=json.loads((dd/'receipt.json').read_bytes());assert diag['actual_fill_inside_new_role_withdrawal_raw_rows']==2
scopes={};scopeRows=[]
for row in json.loads((dd/'exact-new-physical-role-withdrawal-and-actual-filled-alignment.json').read_bytes()):
 uid=row['UUID'];a=set_precision(oldq[uid]['shape'],0);z=set_precision(newq[uid]['shape'],0);lost=a.difference(z);fill=unary_union([p for zz in current['zones']if zz['uuid']==uid for p in K.L.poly(zz['fills'][row['layer']])]);residue=fill.intersection(lost).difference(z);assert not residue.is_empty
 rf=dd/(uid+'-raw-current-filled-inside-new-physical-withdrawal.wkb');assert rf.read_bytes()==residue.wkb
 mask=set_precision(K.Z.bounded_buffer(residue,.0001),0);mf=out/(uid+'-exact-raw-exterior-outward-100nm-negative-scope.wkb');mf.write_bytes(mask.wkb);scopes[uid,row['layer']]=mask;scopeRows.append({'UUID':uid,'layer':row['layer'],'raw_exterior_file':str(rf),'raw_exterior_sha256':sha(rf),'raw_exterior_mm2':residue.area,'explicit_negative_scope_file':str(mf),'explicit_negative_scope_sha256':sha(mf),'outward_reserve_mm':.0001,'exact_new_owned_physical_role_WKB_sha256':K.C.sha(newq[uid]['shape'].wkb),'physical_and_intended_role_unchanged':True})
zones=[];ledger=[];fail=[]
for zz in current['zones']:
 if not any(key[0]==zz['uuid']for key in scopes):zones.append(zz);continue
 z=copy.deepcopy(zz)
 for l,rs in zz['fills'].items():
  mask=scopes.get((zz['uuid'],l))
  if mask is None:continue
  newrs=[]
  for index,(record,piece)in enumerate(zip(rs,K.L.poly(rs))):
   if not piece.intersects(mask):newrs.append(copy.deepcopy(record));continue
   before=set_precision(piece,0);remain=before.difference(mask);gainRows=[]
   for i in range(24):
    aa=arrays(remain);actual=unary_union(K.L.poly(aa));gain=actual.difference(before)
    if gain.is_empty:break
    gf=out/(zz['uuid']+'-'+l+'-'+str(index)+'-'+str(i)+'-raw-reconstruction-gain.wkb');gf.write_bytes(gain.wkb);negative=set_precision(K.Z.bounded_buffer(gain,.0001),0);nf=out/(gf.stem+'-explicit-100nm-negative-reserve.wkb');nf.write_bytes(negative.wkb);remain=actual.difference(negative).intersection(before);gainRows.append({'raw_gain_file':str(gf),'raw_gain_sha256':sha(gf),'negative_scope_file':str(nf),'negative_scope_sha256':sha(nf),'outward_mm':.0001})
   aa=arrays(remain);actual=unary_union(K.L.poly(aa));gain=actual.difference(before)
   if not gain.is_empty:fail.append({'UUID':zz['uuid'],'layer':l,'record':index,'kind':'literal_reconstruction_gain'})
   newrs.extend(aa);ledger.append({'UUID':zz['uuid'],'layer':l,'record':index,'immutable_before_actual_WKB_sha256':K.C.sha(before.wkb),'after_actual_WKB_sha256':K.C.sha(actual.wkb),'strict_zero_new_or_reclaimed_Cu':gain.is_empty,'actual_removed_mm2':before.difference(actual).area,'actual_negative_scope_WKB_sha256':K.C.sha(mask.wkb),'local_reconstruction_gain_reserves':gainRows})
  z['fills'][l]=newrs
 zones.append(z)
after={**current,'zones':zones}
alignment=[]
for uid,l in scopes:
 old=set_precision(oldq[uid]['shape'],0);new=set_precision(newq[uid]['shape'],0);filled=unary_union([p for z in after['zones']if z['uuid']==uid for p in K.L.poly(z['fills'][l])]);residue=filled.intersection(old.difference(new)).difference(new);row={'UUID':uid,'layer':l,'final_literal_exterior_to_exact_new_physical_role_empty':residue.is_empty,'raw_residue_mm2':residue.area};alignment.append(row)
 if not residue.is_empty:fail.append({'kind':'final_actual_exterior_nonempty',**row});(out/(uid+'-unresolved-current-exterior.wkb')).write_bytes(residue.wkb)
put(out/'two-exact-local-current-filled-negative-reserve-scopes.json',scopeRows);put(out/'only-local-actual-filled-record-negative-ledger.json',ledger);put(out/'final-exact-new-role-exterior-alignment.json',alignment);put(out/'raw-unresolved-failures.json',fail)
model=out/'model.pkl'
if not fail:model.write_bytes(pickle.dumps((g,h,b,q,after),protocol=5))
packet=out/'only-two-current-owned-fill-local-negative-scopes.pkl';packet.write_bytes(pickle.dumps({'exact_negative_scopes':scopes,'scope_rows':scopeRows,'record_ledger':ledger,'all_g_h_b_q_native_settings_exact_parent':True},protocol=5))
result={'verdict':'LOCAL_ACTUAL_FILLED_ONLY_LITERAL_EXTERIOR_ALIGNMENT_COMPLETE_FRESH_ALL_GATES_OPEN'if not fail else'LITERAL_FILLED_EXTERIOR_REPAIR_FAILED_NO_MODEL','parent_current_model_file':str(mp),'parent_current_model_sha256':sha(mp),'raw_R500_failure_receipt_sha256':sha(dd/'receipt.json'),'model_file':str(model)if not fail else None,'model_sha256':sha(model)if not fail else None,'only_actual_filled_negative_packet_file':str(packet),'only_actual_filled_negative_packet_sha256':sha(packet),'exact_local_negative_scope_count':len(scopes),'only_current_filled_record_steps':len(ledger),'raw_unresolved_failures':len(fail),'g_h_b_every_physical_intended_profile_NATIVE_outline_exact_R488':True,'no_original_native_fill_snap_or_positive_reclaim_or_threshold':True,'all_source_contact_direct_ZEROoldref_newbody_sameplane_native_current_SI_gates':'OPEN_FRESH_REAUDIT_REQUIRED','all_inherited_raw_failures_preserved':True,'native_jobs':0,'board_written':False,'adopted':False,'elapsed_seconds':time.monotonic()-start}
put(out/'receipt.json',result);print(json.dumps({'receipt_sha256':sha(out/'receipt.json'),**result}),flush=True)
