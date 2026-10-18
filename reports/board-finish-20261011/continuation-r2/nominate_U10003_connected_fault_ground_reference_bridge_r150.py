"""Add a real contained FG plane arm between the ordinary barrel and fault."""
from pathlib import Path
H=Path(__file__).resolve().parent;source=H/'nominate_U10003_fault_ground_reference_bridge_r149.py';code=source.read_text()
code=code.replace('bridge-nominee-r149','bridge-nominee-r150')
code=code.replace('from shapely.ops import unary_union','from shapely.ops import unary_union,nearest_points')
needle='desired=body.buffer(.15,quad_segs=128).union(pt.buffer(.30,quad_segs=128))';assert code.count(needle)==1
code=code.replace(needle,"connector=LineString([pt,nearest_points(pt,fault)[1]]);desired=body.buffer(.15,quad_segs=128).union(pt.buffer(.30,quad_segs=128)).union(connector.buffer(.25,quad_segs=128))")
compile(code,str(source),'exec');exec(compile(code,str(source),'exec'))
