"""Per-record remove-only fill operation, with explicit local gain reserves."""
import copy,json
from shapely import set_precision
from shapely.ops import unary_union
import contact_layout as L
import physical_reference_losses_r3_zero_r208 as RF
import guarded_power_projection_r44 as Z
import audit_aux_exact_raw as A
C=A.C
def records(sh):
 return [[list(p.exterior.coords),[list(r.coords)for r in p.interiors]]for p in RF.parts(sh)]
def subtract(rs,cuts,folder,key):
 original=L.poly(rs);assert len(original)==len(rs);cut=unary_union(cuts);out=[];ledger=[]
 for i,(rec,p)in enumerate(zip(rs,original)):
  p0=set_precision(p,0);assert p0.wkb==p.wkb
  if not cut.intersects(p0):out.append(copy.deepcopy(rec));ledger.append({'record':i,'untouched_record_arrays_exact':True,'before_WKB_sha256':C.sha(p.wkb)});continue
  remain=p0.difference(cut);reserves=[]
  for it in range(16):
   serialized=records(remain);actual=unary_union(L.poly(serialized));gain=actual.difference(p0)
   if gain.is_empty:break
   gf=folder/(key+'-'+str(i)+'-'+str(it)+'-raw-positive-gain.wkb');gf.write_bytes(gain.wkb)
   reserve=Z.bounded_buffer(gain,.0001);rz=set_precision(reserve,0);assert rz.wkb==reserve.wkb
   rf=folder/(key+'-'+str(i)+'-'+str(it)+'-local-100nm-negative-reserve.wkb');rf.write_bytes(reserve.wkb)
   previous=actual;remain=actual.difference(rz).intersection(p0);removed=previous.difference(remain)
   nf=folder/(key+'-'+str(i)+'-'+str(it)+'-actual-negative-delta.wkb');nf.write_bytes(removed.wkb)
   reserves.append({'iteration':it,'raw_gain_file':str(gf),'raw_gain_sha256':C.sha(gain.wkb),'raw_gain_area_mm2':gain.area,'reserve_file':str(rf),'reserve_sha256':C.sha(reserve.wkb),'actual_negative_file':str(nf),'actual_negative_sha256':C.sha(removed.wkb),'actual_removed_area_mm2':removed.area,'nominal_local_negative_reserve_mm':.0001})
  serialized=records(remain);actual=unary_union(L.poly(serialized));gain=actual.difference(p0);assert gain.is_empty,('strict_record_gain',key,i,gain.area)
  af=folder/(key+'-'+str(i)+'-actual-final-record.wkb');af.write_bytes(actual.wkb);extra=p0.difference(actual).difference(cut);xf=folder/(key+'-'+str(i)+'-explicit-extra-negative-delta.wkb');xf.write_bytes(extra.wkb)
  ledger.append({'record':i,'before_WKB_sha256':C.sha(p.wkb),'after_WKB_sha256':C.sha(actual.wkb),'actual_final_record_file':str(af),'strict_no_reclaimed_Cu':True,'reserves':reserves,'explicit_additional_negative_file':str(xf),'explicit_additional_negative_sha256':C.sha(extra.wkb),'explicit_additional_negative_area_mm2':extra.area,'no_original_coordinate_snap':True})
  if actual.difference(p0).is_empty and p0.difference(actual).is_empty:out.append(copy.deepcopy(rec))
  else:out.extend(serialized)
 old=unary_union(original);new=unary_union(L.poly(out));gain=new.difference(old);assert gain.is_empty,('strict_complete_fill_gain',key,gain.area)
 return out,{'per_original_record_operations':ledger,'before_WKB_sha256':C.sha(old.wkb),'after_WKB_sha256':C.sha(new.wkb),'strict_complete_fill_subset':True,'exact_removed_mm2':old.difference(new).area,'actual_polygonal_piece_count':len(out)}
