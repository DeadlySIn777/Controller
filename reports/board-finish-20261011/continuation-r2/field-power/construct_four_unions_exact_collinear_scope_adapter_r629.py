"""Represent a provably collinear scope triangle as its exact edge."""
from pathlib import Path
import ast
H=Path(__file__).resolve().parent
p=H/'construct_four_minimal_unions_inherited_intent_FAIL_bound_r627.py'
t=ast.parse(p.read_text(encoding='utf-8'));t.body.pop();ns={'__file__':str(p)};exec(compile(t,str(p),'exec'),ns);s=ns['s']
s=s.replace('R543-four-minimal-unions-inherited-B3-intent-FAIL-bound-r627','R543-four-unions-exact-collinear-owned-scope-adapter-r629')
s=s.replace('from shapely.geometry import Polygon,LineString','from shapely.geometry import Polygon,LineString,Point\nfrom fractions import Fraction')
old='     for side,t in enumerate(triangles):\n      assert t.is_valid and not t.is_empty;mask='
new='''     for side,t in enumerate(triangles):
      if not t.is_valid:
       pts=list(t.exterior.coords)[:3];ff=[tuple(Fraction.from_float(float(c))for c in p)for p in pts];det=(ff[1][0]-ff[0][0])*(ff[2][1]-ff[0][1])-(ff[1][1]-ff[0][1])*(ff[2][0]-ff[0][0]);assert det==0,('invalid NONcollinear triangle',i,role,j,side,str(det));t=LineString(pts)if len(set(tuple(p)for p in pts))>1 else Point(pts[0])
      assert t.is_valid and not t.is_empty;mask='''
assert old in s;s=s.replace(old,new)
s=s.replace("print('R627'","print('R629'")
exec(compile(s,str(Path(__file__)),'exec'))
