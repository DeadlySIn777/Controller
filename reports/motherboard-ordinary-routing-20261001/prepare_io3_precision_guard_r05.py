"""Retain exact unbuffered topology before relative boundary comparison."""
from pathlib import Path
p=Path(__file__).parent
s=(p/'check_io3_backbone_preservation_r04.py').read_text()
needle=" # 502um reserves1um native offset approximation plus1um boundary comparison;500um remains."
assert needle in s
s=s.replace(needle,""" # The precision neighborhood can never bridge a real slit. Preserve
 # unbuffered actual component membership before erosion or comparison.
 full_new=list(split_polygons(after));full_rows=[]
 for index,piece in enumerate(split_polygons(before)):
  surviving=intersection(piece,after)
  if not surviving.OutlineCount():raise ValueError('An entire actual old power-fill component was lost')
  owners=[i for i,q in enumerate(full_new)if covered(surviving,q)]
  if len(owners)!=1:raise ValueError('Actual unbuffered power-fill topology was split')
  full_rows.append(dict(before_component=index,after_component=owners[0],unbuffered_membership_preserved=True))
"""+needle)
s=s.replace("return dict(passed=True,minimum_screened_core_width_mm=1.", "return dict(passed=True,actual_unbuffered_component_mapping=full_rows,minimum_screened_core_width_mm=1.")
(p/'check_io3_backbone_preservation_r05.py').write_text(s)
for old,new in [('test_io3_backbone_native_r04.py','test_io3_backbone_native_r05.py'),('test_io3_precision_boundary_r04.py','test_io3_precision_boundary_r05.py')]:
 t=(p/old).read_text().replace('preservation_r04','preservation_r05').replace('screen-native-r04','screen-native-r05').replace('boundary-r04','boundary-r05')
 if old.startswith('test_io3_backbone'):
  t=t.replace('for name,a,b in cases:',"cases.append(('actual2nm complete slit across existing sub1mm neck',narrow,h.subtract(narrow,h.box(.8,-.5,.800002,.5))))\nfor name,a,b in cases:")
 (p/new).write_text(t)
for old,new in [('verify_OUT_PERMIT_common_In1_r04.py','verify_OUT_PERMIT_common_In1_r05.py'),('verify_OUT_PERMIT_combined_r03.py','verify_OUT_PERMIT_combined_r04.py')]:
 t=(p/old).read_text().replace('preservation_r04','preservation_r05').replace('screen-native-r04','screen-native-r05').replace('boundary-r04','boundary-r05')
 (p/new).write_text(t);compile(t,str(p/new),'exec')
