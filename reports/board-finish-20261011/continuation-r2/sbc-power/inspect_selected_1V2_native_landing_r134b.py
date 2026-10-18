"""Preserve R134 reader-type failure; explicitly decode serialized contours."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'inspect_selected_1V2_native_landing_r134.py').read_text().replace('import ordinary_routes as O','import ordinary_routes as O\nimport contact_layout as C').replace("unary_union(O.polys(nq['fills'].get('In4.Cu',[])))","unary_union(C.poly(O.polys(nq['fills'].get('In4.Cu',[]))))")
exec(compile(s,str(H/'inspect_selected_1V2_native_landing_r134.py'),'exec'))
