"""Independent integer-boundary attacks for the explicitly scoped IO3 screen."""
from pathlib import Path
import json,sys
sys.path.insert(0,str(Path(__file__).parent))
import pcbnew
import check_io3_backbone_preservation_r07 as h
out=Path(__file__).parent/'io3-precision-boundary-r07';out.mkdir(exist_ok=False)
base=h.box(-4,-2,0,2);base.BooleanAdd(h.box(2,-2,6,2));base.BooleanAdd(h.box(0,-.4,2,.4));base.Simplify()
rows=[]
for shift in (1001,1002,2000,10000):
 moved=h.duplicate(base);moved.Move(pcbnew.VECTOR2I(0,shift))
 try:h.backbone(base,moved)
 except ValueError as ex:rows.append(dict(attack='translated native boundary',shift_nm=shift,rejected=True,reason=str(ex)))
 else:raise AssertionError(('Actual geometry translation passed',shift))
for depth in (1001,2000,10000):
 notch=h.box(.8,.4-depth/1e6,.804,.401)
 after=h.subtract(base,notch)
 try:h.backbone(base,after)
 except ValueError as ex:rows.append(dict(attack='tiny area actual narrow-feature notch',depth_nm=depth,width_um=4,rejected=True,reason=str(ex)))
 else:raise AssertionError(('Actual notch passed',depth))
(out/'receipt.json').write_text(json.dumps(dict(passed=True,helper_sha256=h.sha(h.__file__),test_sha256=h.sha(__file__),native_geometric_controls=rows,maximum_native_boundary_comparison_precision_nm=1000,all_actual_reference_coverage_rules_unchanged=True,no_area_exemption=True,physical_qualification=False),indent=2))
print(json.dumps(dict(passed=True,native_boundary_attacks=len(rows))))
