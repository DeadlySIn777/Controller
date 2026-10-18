"""Check exact component membership without reclipping a derived subset."""
from pathlib import Path
p=Path(__file__).parent
s=(p/'check_io3_backbone_preservation_r05.py').read_text()
assert s.count('owners=[i for i,q in enumerate(full_new)if covered(surviving,q)]')==1
s=s.replace('owners=[i for i,q in enumerate(full_new)if covered(surviving,q)]','owners=[i for i,q in enumerate(full_new)if intersection(piece,q).OutlineCount()]')
assert s.count('owners=[i for i,p in enumerate(new_pieces)if covered(surviving,p)]')==1
s=s.replace('owners=[i for i,p in enumerate(new_pieces)if covered(surviving,p)]','owners=[i for i,p in enumerate(new_pieces)if intersection(piece,p).OutlineCount()]')
(p/'check_io3_backbone_preservation_r06.py').write_text(s)
for old,new in [('test_io3_backbone_native_r05.py','test_io3_backbone_native_r06.py'),('test_io3_precision_boundary_r05.py','test_io3_precision_boundary_r06.py')]:
 t=(p/old).read_text().replace('preservation_r05','preservation_r06').replace('screen-native-r05','screen-native-r06').replace('boundary-r05','boundary-r06')
 (p/new).write_text(t)
for old,new in [('verify_OUT_PERMIT_common_In1_r05.py','verify_OUT_PERMIT_common_In1_r06.py'),('verify_OUT_PERMIT_combined_r04.py','verify_OUT_PERMIT_combined_r05.py')]:
 t=(p/old).read_text().replace('preservation_r05','preservation_r06').replace('screen-native-r05','screen-native-r06').replace('boundary-r05','boundary-r06')
 (p/new).write_text(t);compile(t,str(p/new),'exec')
