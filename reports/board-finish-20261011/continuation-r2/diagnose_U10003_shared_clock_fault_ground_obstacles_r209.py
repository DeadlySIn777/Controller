"""Attribute both nominal shared-return lobes to exact existing obstacles."""
from pathlib import Path
H=Path(__file__).resolve().parent;src=H/'nominate_U10003_single_shared_ground_for_clock_fault_r207.py'
prefix=src.read_text().split("exec(compile(code,str(src),'exec'))")[0];exec(compile(prefix,str(src),'exec'))
code=code.replace('shared-ground-return-faces-r207','shared-ground-return-obstacles-r209').replace("\nprint('R198","\n print('R198")
needle="candidates=[]\n  for poly in polys(near):"
assert code.count(needle)==1
code=code.replace(needle,"""candidates=[]
  nominal=pt.buffer(1.0,quad_segs=256).difference(pt.buffer(.9,quad_segs=256)).intersection(sp.buffer(1.0,quad_segs=256)).difference(sp.buffer(.9,quad_segs=256))
  attribution=[]
  for ii,poly in enumerate(polys(nominal)):
   pnt=poly.representative_point();hits=[{**r,'overlap_with_nominal_lobe_mm2':c.intersection(poly).area,'representative_point_covered':c.covers(pnt)}for r,c in zip(ledger,cuts)if c.intersects(poly)]
   attribution.append({'nominal_lobe':ii,'nominal_bounds_mm':list(poly.bounds),'representative_site_mm':[pnt.x,pnt.y],'clock_distance_mm':pnt.distance(pt),'fault_distance_mm':pnt.distance(sp),'exact_obstacles_intersecting_lobe':hits})
  put(OUT/'shared-return-two-lobes-exact-obstacle-attribution.json',attribution)
  for poly in polys(near):""")
exec(compile(code,str(src),'exec'))
