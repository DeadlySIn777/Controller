from pathlib import Path
p=Path('reports/motherboard-return-zoning-20261001/review-IO3-literal-tip-cleanup-independent-r05.py');q=p.with_name(p.name.replace('r05.py','r06.py'))
if q.exists():raise ValueError('Immutable revision exists')
s=p.read_text().replace("IO3-literal-tip-cleanup-independent-r05'","IO3-literal-tip-cleanup-independent-r06'")
needle="if beyond.OutlineCount():raise ValueError('Unexpected real IO3 cut outside the literal DFM region')"
replacement="""if beyond.OutlineCount():
  lost=[]
  for piece in split_polygons(beyond):
   box=piece.BBox();lost.append(dict(bounds_mm=[pcbnew.ToMM(v)for v in(box.GetX(),box.GetY(),box.GetRight(),box.GetBottom())],exact_twice_area_nm2=exact_twice_area(piece),native_polygon=piece.Format(False)))
  write(out/'full-native-influence-outside-thin-mask.json',dict(passed=False,input_sha256=frozen,board_sha256=sha(candidate),exact_authorized_nominal_region_mm=p['exact_bounds_mm'],unbuffered_native_topology=full,actual_502um_core_mapping=cores,all_literal_outside_loss_polygons=lost,no_precision_or_area_waiver=True))
  raise ValueError('Unexpected real IO3 cut outside the literal DFM region')"""
if needle not in s:raise ValueError('Strict exact full influence check drift')
q.write_text(s.replace(needle,replacement))
