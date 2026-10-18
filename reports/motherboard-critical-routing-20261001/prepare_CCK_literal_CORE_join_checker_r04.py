"""Stage a separate two-pair native hole-join ledger, no frozen guard edits.
The full CORE ownership/narrow/source/annulus/regulator guards stay intact.
This accounts for actual minimum-feature closure between a new barrel and an
explicit unchanged nonflashed old LOGIC barrel; no arbitrary area mask.
"""
from pathlib import Path
p=Path(__file__).parent;source=p/'check_literal_CCK_CORE_preservation_r01.py';text=source.read_text()
old=" residual=f.subtract(removed,literal_antipads)\n if residual.OutlineCount():raise ValueError('CORE removal extends outside literal added-via antipads')\n"
new=""" # Actual native CORE min-feature filling joins two specific new barrel
 # clearances to old, nonflashed LOGIC drill clearances. Their names, native
 # positions/shapes and old geometry are literal; no Source/current pad can
 # be admitted by this list. All 1mm receiving-tab guards above remain exact.
 join_pairs={'aa6951f3-0d1f-40f5-aa79-47aae426bc59':'3376a140-028c-4a29-84f0-21540ab5865a','890ade5e-74e0-48ed-85f2-1d2c497237f3':'b1e1485b-fbb0-48dd-a58a-2262fbd55ce3'}
 actual_min=max(z.GetMinThickness()for z in after.Zones()if z.GetNetname()==CORE and z.IsOnLayer(pcbnew.In3_Cu)and not z.GetIsRuleArea())
 if actual_min!=pcbnew.FromMM(.175):raise ValueError('Native CORE minimum-feature process changed')
 joins=[]
 for newuid,olduid in join_pairs.items():
  old=bc[olduid];current=ac[olduid];newvia=ac[newuid]
  if old.Type()!=pcbnew.PCB_VIA_T or old.GetNetname()!='/LOGIC_GND' or identity(old)!=identity(current)or current.FlashLayer(pcbnew.In3_Cu):raise ValueError('Literal old nonfunctional CORE-layer neighbour changed')
  if abs(math.dist(mm(old.GetPosition()),mm(newvia.GetPosition()))-.8)>1e-8:raise ValueError('Literal new/old antipad adjacency changed')
  # A nonflashed old via exposes its actual drill-only inner Cu shape. The
  # .20 clearance bound is retained from the original checker; native .175
  # minimum feature closure contributes precisely half that width.
  radius=old.GetDrillValue()//2+pcbnew.FromMM(.20)+actual_min//2
  collar=circle(tuple(old.GetPosition()),radius);literal_antipads.BooleanAdd(collar)
  joins.append(dict(new_via_UUID=newuid,unchanged_old_LOGIC_via_UUID=olduid,old_native_In3_shape=current.GetEffectiveShape(pcbnew.In3_Cu).Format(),old_In3_annulus_absent=True,actual_centres_distance_mm=.8,retained_clearance_bound_mm=.20,actual_native_minimum_feature_width_mm=.175,derived_drill_clearance_join_radius_mm=pcbnew.ToMM(radius),actual_removed_join_polygon=f.intersection(removed,collar).Format(False)))
 precision=f.duplicate(af);precision.Inflate(pcbnew.FromMM(.001),pcbnew.CORNER_STRATEGY_ROUND_ALL_CORNERS,1)
 certain_removed=f.subtract(bf,precision);residual=f.subtract(certain_removed,literal_antipads)
 if residual.OutlineCount():raise ValueError('Actual CORE removal exceeds literal barrel/join ledgers beyond unchanged1um contour precision')
 # Persist the positive physical contour delta as well as its bounded native
 # comparison. Nominal submicron facet change is not called zero geometry.
 nominal_outside=f.subtract(removed,literal_antipads)
"""
assert text.count(old)==1;text=text.replace(old,new)
text=text.replace("actual_literal_antipad_ledger=audits,remaining_outside_antipad_removal_mm2=0.,","actual_literal_antipad_ledger=audits,actual_literal_native_join_ledger=joins,actual_nominal_outside_contour_delta_polygon=nominal_outside.Format(False),actual_nominal_outside_contour_delta_mm2=nominal_outside.Area()/1e12,unchanged_native_contour_comparison_um=1.,remaining_definite_outside_ledger_removal_mm2=0.,")
(p/'check_literal_CCK_CORE_preservation_r04.py').write_text(text)
wrapper=(p/'review_CCK_CORE_cleaned_pair_r03.py').read_text().replace('check_literal_CCK_CORE_preservation_r01','check_literal_CCK_CORE_preservation_r04').replace('CORE-cleaned-CCK-relative-review-r03','CORE-cleaned-CCK-relative-review-r04')
(p/'review_CCK_CORE_cleaned_pair_r04.py').write_text(wrapper)
