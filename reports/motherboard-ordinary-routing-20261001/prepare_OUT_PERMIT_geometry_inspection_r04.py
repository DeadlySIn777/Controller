from pathlib import Path
p=Path(__file__).parent;s=(p/'inspect_OUT_PERMIT_exact_native_polygons_r03.py').read_text()
start=s.index('literal=[]');end=s.index('report=dict(',start)
s=s[:start]+s[end:]
s=s.replace("union_before_difference_area_nm2=gb.symmetric_difference(literal[0]).area,union_after_difference_area_nm2=ga.symmetric_difference(literal[1]).area,", "raw_uncombined_zone_contours_require_separate_touching_hole_review=True,")
s=s.replace(",\n literal_raw_fill_narrow_cut_mm2=literal[0].difference(go).intersection(literal[0].difference(literal[1])).area/1e12,\n literal_raw_fill_narrow2nm_escape_mm2=literal[0].difference(go).difference(literal[1].buffer(2,quad_segs=32)).area/1e12", "")
s=s.replace('independent-exact-native-geometry-r03.json','independent-exact-native-geometry-r04.json')
(p/'inspect_OUT_PERMIT_exact_native_polygons_r04.py').write_text(s)
