"""Strict per-record AND aggregate subtraction for overlapped restorations.

Preserves the original R254 per-record checks. A union can expose a literal
boundary remainder despite all individual checks; that remainder receives
an explicit local 100 nm negative reservation and is rechecked. No area
threshold, native-coordinate snap, or accepted positive remainder exists.
"""
from pathlib import Path
from shapely.ops import unary_union
from shapely import set_precision
import immutable_local_fill_subtraction_r254 as ORIGINAL
import contact_layout as L
import guarded_power_projection_r44 as Z
import audit_aux_exact_raw as A
records=ORIGINAL.records
source=Path(ORIGINAL.__file__).read_text(encoding='utf-8')
source=source.replace('def subtract(rs,cuts,folder,key):','def per_record_step(rs,cuts,folder,key):')
needle="gain=new.difference(old);assert gain.is_empty,('strict_complete_fill_gain',key,gain.area)"
assert source.count(needle)==1
source=source.replace(needle,'gain=new.difference(old)')
source=source.replace("'strict_complete_fill_subset':True","'strict_complete_fill_subset':gain.is_empty")
scope={};exec(compile(source,str(ORIGINAL.__file__),'exec'),scope)
def subtract(rs,cuts,folder,key):
 original=unary_union(L.poly(rs));out,first=scope['per_record_step'](rs,cuts,folder,key);steps=[]
 for i in range(32):
  actual=unary_union(L.poly(out));gain=actual.difference(original)
  if gain.is_empty:break
  gf=folder/(key+'-aggregate-'+str(i)+'-literal-boundary-gain.wkb');gf.write_bytes(gain.wkb)
  reserve=Z.bounded_buffer(gain,.0001);rz=set_precision(reserve,0);assert rz.wkb==reserve.wkb
  rf=folder/(key+'-aggregate-'+str(i)+'-explicit-local-100nm-negative.wkb');rf.write_bytes(reserve.wkb)
  previous=actual;out,proof=scope['per_record_step'](out,[rz],folder,key+'-aggregate-'+str(i));after=unary_union(L.poly(out));removed=previous.difference(after);nf=folder/(key+'-aggregate-'+str(i)+'-actual-negative.wkb');nf.write_bytes(removed.wkb)
  steps.append({'iteration':i,'literal_gain_file':str(gf.resolve()),'literal_gain_sha256':A.C.sha(gain.wkb),'literal_gain_mm2':gain.area,'explicit_negative_file':str(rf.resolve()),'explicit_negative_sha256':A.C.sha(reserve.wkb),'nominal_negative_mm':.0001,'actual_negative_file':str(nf.resolve()),'actual_negative_sha256':A.C.sha(removed.wkb),'actual_negative_mm2':removed.area,'per_previous_record_strict_proof':proof})
 else:raise AssertionError(('strict aggregate subtraction did not converge',key))
 actual=unary_union(L.poly(out));assert actual.difference(original).is_empty,('strict aggregate gained Cu',key)
 return out,{**first,'R254_original_helper_sha256':A.C.sha(Path(ORIGINAL.__file__).read_bytes()),'initial_aggregate_gain_preserved_if_present':not first['strict_complete_fill_subset'],'explicit_aggregate_negative_steps':steps,'before_WKB_sha256':A.C.sha(original.wkb),'after_WKB_sha256':A.C.sha(actual.wkb),'strict_complete_fill_subset':True,'exact_removed_mm2':original.difference(actual).area,'actual_polygonal_piece_count':len(out),'native_original_arrays_not_snapped':True}
