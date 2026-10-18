from pathlib import Path
import json
p=Path('reports/motherboard-return-zoning-20261001/review-IO3-literal-tip-cleanup-independent-r02.py')
q=p.with_name(p.name.replace('r02.py','r03.py'))
if q.exists():raise ValueError('Immutable revision exists')
s=p.read_text().replace("IO3-literal-tip-cleanup-independent-r02'","IO3-literal-tip-cleanup-independent-r03'")
needle="if outside.OutlineCount():raise ValueError('A definite old thin feature outside the exact DFM region changed beyond frozen1um precision')"
replacement="""if outside.OutlineCount():
  lost=[]
  for piece in split_polygons(outside):
   box=piece.BBox();lost.append(dict(bounds_mm=[pcbnew.ToMM(v)for v in(box.GetX(),box.GetY(),box.GetRight(),box.GetBottom())],exact_twice_area_nm2=exact_twice_area(piece),native_polygon=piece.Format(False)))
  write(out/'outside-region-failure.json',dict(passed=False,input_sha256=frozen,board_sha256=sha(candidate),exact_authorized_region_mm=p['exact_bounds_mm'],unbuffered_native_topology=full,actual_502um_core_mapping=cores,all_literal_outside_loss_polygons=lost,no_precision_or_area_waiver=True))
  raise ValueError('A definite old thin feature outside the exact DFM region changed beyond frozen1um precision')"""
if needle not in s:raise ValueError('Exact strict preservation guard drift')
s=s.replace(needle,replacement);q.write_text(s)
Path('reports/motherboard-return-zoning-20261001/IO3-literal-tip-cleanup-independent-r02/failure.json').write_text(json.dumps(dict(passed=False,reason='Strict unchanged r07 outside-region definite-thin-feature preservation rejected. No guard or board mutation. Exact polygon localization follows in a new immutable r03.'),indent=2))
