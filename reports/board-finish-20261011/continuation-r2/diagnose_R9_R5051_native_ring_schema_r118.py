"""Use the actual native list-of-rings schema; preserve failed R117."""
from pathlib import Path
H=Path(__file__).resolve().parent
source=H/'diagnose_R9_R5051_actual_native_zone_flash_r117.py';code=source.read_text()
needle="OUT=H/'R9-R5051-exact-actual-zone-flash-diagnosis-r117'";assert code.count(needle)==1
code=code.replace(needle,"OUT=H/'R9-R5051-exact-native-ring-flash-diagnosis-r118'")
needle="from shapely.geometry import Point";assert code.count(needle)==1;code=code.replace(needle,"from shapely.geometry import Point,Polygon")
needle="intended=unary_union(C.poly(q['outline']));actual=unary_union(C.poly(q['fills'].get('In3.Cu',[])))"
assert code.count(needle)==1
code=code.replace(needle,"intended=unary_union([Polygon(rs[0],rs[1:]) for rs in q['outline']]);actual=unary_union([Polygon(rs[0],rs[1:]) for rs in q['fills'].get('In3.Cu',[])])")
exec(compile(code,str(source),'exec'))
