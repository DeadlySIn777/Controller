from pathlib import Path
import json
p=Path('reports/motherboard-return-zoning-20261001/inspect-motor-r04-literal-sliver-provenance-r01.py')
q=p.with_name(p.name.replace('r01.py','r02.py'))
if q.exists():raise ValueError('Immutable revision already exists')
s=p.read_text().replace('motor-bank-A-r04-literal-sliver-provenance-r01.json','motor-bank-A-r04-literal-sliver-provenance-r02.json')
s=s.replace('return [[list(poly.CVertex(j,i))for j in range(poly.CPointCount(i))]for i in range(poly.OutlineCount())]','return [[[poly.COutline(i).CPoint(j).x,poly.COutline(i).CPoint(j).y]for j in range(poly.COutline(i).PointCount())]for i in range(poly.OutlineCount())]')
q.write_text(s)
p.with_suffix('.failure.json').write_text(json.dumps(dict(passed=False,reason='Native SHAPE_POLY_SET exposes COutline(i).PointCount(), not CPointCount(i); no output or copper mutation occurred.'),indent=2))
