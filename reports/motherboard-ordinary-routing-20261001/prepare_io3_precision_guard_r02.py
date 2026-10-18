"""Stage a separate explicit two-native-unit containment precision check."""
from pathlib import Path
p=Path(__file__).parent
s=(p/'check_io3_backbone_preservation_r01.py').read_text()
old=" if intersection(removed,narrow).OutlineCount():raise ValueError('New routing cuts a pre-existing sub-1mm power feature or protected corner')"
new=""" # Native polygon Boolean operations round newly intersected coordinates to
 # integer nanometres. Use a bounded geometric containment tolerance, never
 # an area filter: arbitrarily long or small real notches beyond2nm fail.
 # This is2/1000 of the already reserved1um erosion approximation margin.
 assert pcbnew.FromMM(.000001)==1
 precision_after=duplicate(after)
 precision_after.Inflate(2,pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
 escaped=subtract(narrow,precision_after)
 if escaped.OutlineCount():raise ValueError('New routing cuts a pre-existing sub-1mm power feature beyond2nm native coordinate rounding')"""
assert old in s;s=s.replace(old,new)
s=s.replace('preexisting_sub1mm_features_preserved=True,removed_copper_mm2=', 'preexisting_sub1mm_features_preserved_within_native_precision=True,maximum_native_boundary_rounding_nm=2,no_area_based_exemptions=True,removed_copper_mm2=')
(p/'check_io3_backbone_preservation_r02.py').write_text(s)
compile(s,str(p/'check_io3_backbone_preservation_r02.py'),'exec')
t=(p/'test_io3_backbone_native_r01.py').read_text().replace('check_io3_backbone_preservation_r01','check_io3_backbone_preservation_r02').replace('io3-relative-power-screen-native-r01','io3-relative-power-screen-native-r02')
anchor="for name,a,b in cases:"
assert anchor in t
t=t.replace(anchor,"""# Precision is bounded by distance, never total removed area. A2um-long,
# 32nm-deep real notch in a0.8mm neck has only6.4e-8mm2 area but must fail.
cases.append(('real tiny-area32nm notch in old thin neck',narrow,h.subtract(narrow,h.box(.8,.399968,.802,.401))))
cases.append(('real2um partial-width neck erosion',narrow,h.subtract(narrow,h.box(.8,.398,1.2,.401))))
"""+anchor)
(p/'test_io3_backbone_native_r02.py').write_text(t)
compile(t,str(p/'test_io3_backbone_native_r02.py'),'exec')
v=(p/'verify_OUT_PERMIT_common_In1_r01.py').read_text().replace('check_io3_backbone_preservation_r01','check_io3_backbone_preservation_r02').replace('io3-relative-power-screen-native-r01','io3-relative-power-screen-native-r02')
(p/'verify_OUT_PERMIT_common_In1_r02.py').write_text(v)
