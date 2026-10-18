"""Preserve R405 failure; explicitly remove its physical boundary residue."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'repair_FIELD5_R393_actual_IO3_margin_r405.py').read_text(encoding='utf-8')
s=s.replace('FIELD5-R393-only-new-plane-actual-IO3-margin-correction-r405','FIELD5-R393-only-new-plane-margin-and-native-boundary-correction-r407')
needle=" assert literal(q['shape']).difference(literal(q['zone_outline_shape'])).is_empty"
extra=""" prior=q['shape'];allowed=literal(prior).intersection(literal(q['zone_outline_shape']));after=set_precision(allowed,1e-6,mode='pointwise');reserves=[]
 for i in range(32):
  gain=literal(after).difference(allowed)
  if gain.is_empty:break
  gf=O/('physical-native-boundary-'+str(i)+'-literal-outside.wkb');gf.write_bytes(gain.wkb);reserve=literal(N.bounded_buffer(gain,.0001));rf=O/('physical-native-boundary-'+str(i)+'-explicit-100nm-negative.wkb');rf.write_bytes(reserve.wkb)
  after=set_precision(literal(after).difference(reserve),1e-6,mode='pointwise');reserves.append({'literal_outside_file':str(gf.resolve()),'literal_outside_sha256':sha(gf),'explicit_negative_file':str(rf.resolve()),'explicit_negative_sha256':sha(rf)})
 else:raise AssertionError('physical/native boundary did not converge')
 q['shape']=after;assert literal(after).difference(literal(prior)).is_empty
 rows.append({'UUID':UID,'role':'shape','operation':'only_new_FIELD5_physical_inside_final_intended_literal_boundary','before_sha256':dg(prior),'after_sha256':dg(after),'removed_mm2':literal(prior).difference(literal(after)).area,'literal_gain_empty':True,'explicit_canonical_negative_reserves':reserves})
"""
assert s.count(needle)==1;s=s.replace(needle,extra+needle)
exec(compile(s,str(H/'repair_FIELD5_R393_actual_IO3_margin_r405.py'),'exec'))
