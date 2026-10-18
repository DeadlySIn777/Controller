"""Keep R502 raw FAIL; explicitly withdraw each remaining literal exterior.

Only current owned FILLED records change. Each bounded local reserve and
every failed literal intermediate is retained; no role/native snap or waiver.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
base=H/'compose_Q0_owned_actual_fill_exterior_negative_alignment_r502.py'
code=base.read_text().replace('Q0-owned-actual-fill-exterior-negative-alignment-r502','Q0-owned-actual-fill-strict-local-negative-successor-r504')
needle="after={**current,'zones':zones}\nalignment=[]"
assert code.count(needle)==1
block="""after={**current,'zones':zones}
for passindex in range(12):
 additional={}
 for uid,l in scopes:
  old=set_precision(oldq[uid]['shape'],0);new=set_precision(newq[uid]['shape'],0);filled=unary_union([p for z in after['zones']if z['uuid']==uid for p in K.L.poly(z['fills'][l])]);residue=filled.intersection(old.difference(new)).difference(new)
  if residue.is_empty:continue
  rf=out/(uid+'-'+str(passindex)+'-retained-raw-exterior.wkb');rf.write_bytes(residue.wkb);mask=set_precision(K.Z.bounded_buffer(residue,.0001),0);mf=out/(uid+'-'+str(passindex)+'-explicit-local-exterior-100nm-negative-scope.wkb');mf.write_bytes(mask.wkb);additional[uid,l]=mask;scopeRows.append({'UUID':uid,'layer':l,'pass':passindex,'raw_exterior_file':str(rf),'raw_exterior_sha256':sha(rf),'raw_exterior_kind':residue.geom_type,'raw_exterior_mm2':residue.area,'explicit_negative_scope_file':str(mf),'explicit_negative_scope_sha256':sha(mf),'outward_reserve_mm':.0001,'no_dimension_or_area_exception':True});scopes[uid,l]=unary_union([scopes[uid,l],mask])
 if not additional:break
 nextzones=[]
 for zz in after['zones']:
  if not any(key[0]==zz['uuid']for key in additional):nextzones.append(zz);continue
  z=copy.deepcopy(zz)
  for l,rs in zz['fills'].items():
   mask=additional.get((zz['uuid'],l))
   if mask is None:continue
   newrs=[]
   for index,(record,piece)in enumerate(zip(rs,K.L.poly(rs))):
    if not piece.intersects(mask):newrs.append(copy.deepcopy(record));continue
    before=set_precision(piece,0);remain=before.difference(mask);gainRows=[]
    for i in range(24):
     aa=arrays(remain);actual=unary_union(K.L.poly(aa));gain=actual.difference(before)
     if gain.is_empty:break
     gf=out/(zz['uuid']+'-'+l+'-'+str(passindex)+'-'+str(index)+'-'+str(i)+'-raw-local-reconstruction-gain.wkb');gf.write_bytes(gain.wkb);negative=set_precision(K.Z.bounded_buffer(gain,.0001),0);nf=out/(gf.stem+'-explicit-100nm-negative-reserve.wkb');nf.write_bytes(negative.wkb);remain=actual.difference(negative).intersection(before);gainRows.append({'raw_gain_file':str(gf),'raw_gain_sha256':sha(gf),'negative_scope_file':str(nf),'negative_scope_sha256':sha(nf),'outward_mm':.0001})
    aa=arrays(remain);actual=unary_union(K.L.poly(aa));gain=actual.difference(before)
    if not gain.is_empty:fail.append({'UUID':zz['uuid'],'layer':l,'pass':passindex,'record':index,'kind':'literal_local_reconstruction_gain'})
    newrs.extend(aa);ledger.append({'UUID':zz['uuid'],'layer':l,'pass':passindex,'record':index,'immutable_before_actual_WKB_sha256':K.C.sha(before.wkb),'after_actual_WKB_sha256':K.C.sha(actual.wkb),'strict_zero_new_or_reclaimed_Cu':gain.is_empty,'actual_removed_mm2':before.difference(actual).area,'actual_negative_scope_WKB_sha256':K.C.sha(mask.wkb),'local_reconstruction_gain_reserves':gainRows})
   z['fills'][l]=newrs
  nextzones.append(z)
 after={**after,'zones':nextzones}
alignment=[]"""
code=code.replace(needle,block)
derived=H/'Q0-owned-actual-fill-strict-local-negative-successor-r504-derived-constructor.py';assert not derived.exists();derived.write_text(code)
exec(compile(code,str(derived),'exec'))
