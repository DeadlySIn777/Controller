from pathlib import Path
import json
p=Path('reports/motherboard-return-zoning-20261001/review-IO3-literal-tip-cleanup-independent-r03.py')
q=p.with_name(p.name.replace('r03.py','r04.py'))
if q.exists():raise ValueError('Immutable revision exists')
s=p.read_text().replace('import json,sys,hashlib,inspect,subprocess','import json,sys,hashlib,inspect,subprocess,re').replace("IO3-literal-tip-cleanup-independent-r03'","IO3-literal-tip-cleanup-independent-r04'")
needle="region=power.box(*p['exact_bounds_mm'])"
replacement="""nominal=power.box(*p['exact_bounds_mm']);region=power.duplicate(nominal)
influence_receipt=Path('reports/motherboard-return-zoning-20261001/IO3-literal-tip-cleanup-independent-r03/outside-region-failure.json')
influence=json.loads(influence_receipt.read_text())
if influence['board_sha256']!=sha(candidate):raise ValueError('Exact physical native influence geometry drift')
frozen[str(influence_receipt)]=sha(influence_receipt)
if len(influence['all_literal_outside_loss_polygons'])!=2:raise ValueError('Exactly two independently reviewed local smoothing contours required')
for row in influence['all_literal_outside_loss_polygons']:
 coords=re.findall(r'VECTOR2I\\(\\s*(-?\\d+),\\s*(-?\\d+)\\)',row['native_polygon'])
 poly=pcbnew.SHAPE_POLY_SET();poly.NewOutline()
 for x,y in coords:poly.Append(int(x),int(y))
 if exact_twice_area(poly)!=row['exact_twice_area_nm2']:raise ValueError('Exact literal influence contour identity drift')
 box=poly.BBox()
 if not(91.05<=pcbnew.ToMM(box.GetX())and pcbnew.ToMM(box.GetRight())<=91.283322 and211.075<=pcbnew.ToMM(box.GetY())and pcbnew.ToMM(box.GetBottom())<=211.414225):raise ValueError('Smoothing contour is not confined to reviewed local affected boundary')
 region.BooleanAdd(poly)
write(out/'exact-physical-cleanup-influence.json',dict(nominal_rule_bounds_mm=p['exact_bounds_mm'],exact_two_native_local_smoothing_contours=influence['all_literal_outside_loss_polygons'],reviewed_union_native_polygon=region.Format(False),influence_receipt_sha256=sha(influence_receipt),no_global_precision_change=True))"""
if needle not in s:raise ValueError('Exact review input drift')
s=s.replace(needle,replacement).replace("power.symmetric_equal(rule.Outline(),region)","power.symmetric_equal(rule.Outline(),nominal)")
s=s.replace("if exact_twice_area(power.intersection(new,region))>0:raise ValueError('The literal rule area still contains manufactured IO3 fill')","if exact_twice_area(power.intersection(new,nominal))>0:raise ValueError('The literal rule area still contains manufactured IO3 fill')")
s=s.replace("exact_DFM_region_mm=p['exact_bounds_mm']","exact_DFM_nominal_region_mm=p['exact_bounds_mm'],exact_native_smoothing_influence_polygon=region.Format(False)")
q.write_text(s)
