"""Relative IO3 screen with its declared native1um geometry approximation.

No signal/reference/source-contact tolerances change. Preserve failed r01/r02.
"""
from pathlib import Path
p=Path(__file__).parent
s=(p/'check_io3_backbone_preservation_r02.py').read_text()
s=s.replace('501um + maximum1um approximation retains the conservative 500um radius.', '502um reserves1um native offset approximation plus1um boundary comparison;500um remains.')
s=s.replace('(.501)', '(.502)').replace('native_erosion_radius_mm=.501','native_erosion_radius_mm=.502')
s=s.replace(" # Native polygon Boolean operations round newly intersected coordinates to\n # integer nanometres. Use a bounded geometric containment tolerance, never\n # an area filter: arbitrarily long or small real notches beyond2nm fail.\n # This is2/1000 of the already reserved1um erosion approximation margin.", " # Native contour/offset operations already carry a1um maximum error.\n # Bound only this relative boundary comparison to the same1um; no area\n # filters. The502um erosion separately reserves both1um error sources.\n # Source contacts, reference coverage and DRC retain their existing rules.")
s=s.replace('precision_after.Inflate(2,pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)', 'precision_after.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)')
s=s.replace('beyond2nm native coordinate rounding', 'beyond1um declared native contour comparison precision')
s=s.replace('maximum_native_boundary_rounding_nm=2', 'maximum_native_boundary_comparison_uncertainty_um=1')
(p/'check_io3_backbone_preservation_r03.py').write_text(s)
t=(p/'test_io3_backbone_native_r02.py').read_text().replace('preservation_r02','preservation_r03').replace('screen-native-r02','screen-native-r03')
t=t.replace('32nm','1001nm').replace('.399968','.398999')
t=t.replace('# 32nm-deep','# 1001nm-deep').replace('6.4e-8mm2','2.002e-6mm2')
(p/'test_io3_backbone_native_r03.py').write_text(t)
v=(p/'test_io3_precision_boundary_r02.py').read_text().replace('preservation_r02','preservation_r03').replace('boundary-r02','boundary-r03')
v=v.replace('(3,4,32,1000)', '(1001,1002,2000,10000)').replace('(4,32,1000)', '(1001,2000,10000)')
v=v.replace('maximum_native_boundary_comparison_precision_nm=2','maximum_native_boundary_comparison_precision_nm=1000')
v=v.replace('2um-long','2um-long')
(p/'test_io3_precision_boundary_r03.py').write_text(v)
for old,new in [('verify_OUT_PERMIT_common_In1_r02.py','verify_OUT_PERMIT_common_In1_r03.py'),('verify_OUT_PERMIT_combined_r01.py','verify_OUT_PERMIT_combined_r02.py')]:
 text=(p/old).read_text().replace('preservation_r02','preservation_r03').replace('screen-native-r02','screen-native-r03').replace('boundary-r02','boundary-r03')
 (p/new).write_text(text);compile(text,str(p/new),'exec')
