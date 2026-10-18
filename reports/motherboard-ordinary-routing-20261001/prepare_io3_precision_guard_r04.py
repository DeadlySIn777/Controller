"""Correct the adversarial notch width, retaining the unchanged1um metric."""
from pathlib import Path
p=Path(__file__).parent
s=(p/'check_io3_backbone_preservation_r03.py').read_text()
(p/'check_io3_backbone_preservation_r04.py').write_text(s)
for old,new in [('test_io3_backbone_native_r03.py','test_io3_backbone_native_r04.py'),('test_io3_precision_boundary_r03.py','test_io3_precision_boundary_r04.py')]:
 t=(p/old).read_text().replace('preservation_r03','preservation_r04').replace('screen-native-r03','screen-native-r04').replace('boundary-r03','boundary-r04')
 t=t.replace('.802','.804').replace('width_um=2','width_um=4').replace('2um-long','4um-long').replace('2.002e-6mm2','4.004e-6mm2')
 (p/new).write_text(t)
for old,new in [('verify_OUT_PERMIT_common_In1_r03.py','verify_OUT_PERMIT_common_In1_r04.py'),('verify_OUT_PERMIT_combined_r02.py','verify_OUT_PERMIT_combined_r03.py')]:
 t=(p/old).read_text().replace('preservation_r03','preservation_r04').replace('screen-native-r03','screen-native-r04').replace('boundary-r03','boundary-r04')
 (p/new).write_text(t);compile(t,str(p/new),'exec')
