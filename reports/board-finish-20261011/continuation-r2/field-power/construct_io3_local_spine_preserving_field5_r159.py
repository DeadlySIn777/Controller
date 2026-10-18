"""Bound the exact old-IO3 crossing before triangulation; no reduced geometry."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_io3_spine_preserving_field5_r157.py').read_text(encoding='utf-8')
s=s.replace('r157','r159').replace('R157','R159')
start=s.index('for width in (.3,.25,.2):');end=s.index('assert answer is not None',start)
s=s[:start]+'''from shapely.geometry import box
for margin in (3.,8.,20.,40.):
 win=box(min(aa.x,bb.x)-margin,min(aa.y,bb.y)-margin,max(aa.x,bb.x)+margin,max(aa.y,bb.y)+margin)
 for width in (.3,.25,.2):
  free=A.intersection(win).buffer(-width/2-.00002)
  parts=[free] if free.geom_type=='Polygon' else [q for q in getattr(free,'geoms',[]) if q.geom_type=='Polygon']
  for part in sorted(parts,key=lambda q:-q.area):
   a=part.intersection(start);b=part.intersection(end)
   if a.is_empty or b.is_empty:continue
   pa,pb=nearest_points(a,b);line=LineString([pa,pb]);body=P.bounded_buffer(line,width/2)
   if not A.covers(body):
    print('R159 old IO3 bounded crossing',margin,width,list(win.bounds),flush=True)
    try:points,search=T.route(part,tuple(pa.coords[0]),tuple(pb.coords[0]))
    except (AssertionError,ValueError):continue
    line=LineString([[round(x,6),round(y,6)] for x,y in points]);body=P.bounded_buffer(line,width/2)
   if A.covers(body) and body.intersection(start).area>1e-8 and body.intersection(end).area>1e-8:answer=(line,body,width);break
  if answer:break
 if answer:break
'''+s[end:]
exec(compile(s,str(H/'construct_io3_spine_preserving_field5_r157.py'),'exec'))
