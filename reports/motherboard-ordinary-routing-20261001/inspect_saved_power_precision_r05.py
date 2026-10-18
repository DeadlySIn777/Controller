from pathlib import Path
import sys,json
p=Path(__file__).parent;sys.path[:0]=[str(p/'isolated-geometry-deps-r01')]
from shapely import wkt
from shapely.geometry import Polygon
report=json.loads((p/'actual-source26-root81-OUT-PERMIT-r06/independent-exact-native-geometry-r04.json').read_text())
shape=wkt.loads(report['exact_cut_wkt'])
rows=[]
for poly in shape.geoms:
 if not isinstance(poly,Polygon):continue
 # The minimum rotated rectangle gives the full extent normal to even a
 # long, nearly-collinear boundary; area alone cannot bound that extent.
 rect=list(poly.minimum_rotated_rectangle.exterior.coords)
 import math
 sides=[math.dist(a,b)for a,b in zip(rect,rect[1:])]
 rows.append(dict(area_nm2=poly.area,bounds_nm=poly.bounds,minimum_rectangle_width_nm=min(sides),length_nm=max(sides)))
print(json.dumps(rows,indent=2))
(p/'actual-source26-root81-OUT-PERMIT-r06/independent-cut-widths-r05.json').write_text(json.dumps(rows,indent=2))
