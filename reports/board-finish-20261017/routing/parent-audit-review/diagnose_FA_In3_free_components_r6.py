import sys
sys.dont_write_bytecode=True
from pathlib import Path
import json,hashlib
from shapely import from_wkb
from shapely.geometry import Point,box
from shapely.ops import nearest_points
H=Path(__file__).resolve().parent;P=H/'FA-existing-In3-no-new-hole-current-source-floor-route-r5';OUT=H/'FA-existing-In3-free-component-diagnostic-r6'
def parts(p):return[p]if p.geom_type=='Polygon'else list(p.geoms)
def main():
 assert not OUT.exists();OUT.mkdir();floor=from_wkb((P/'R299-actual-source-FG-In4-floor.wkb').read_bytes());free=from_wkb((P/'search-only-free-centerline-area.wkb').read_bytes());ar=json.loads((P/'retained-In3-anchor-options.json').read_bytes());fp=parts(floor.buffer(-.1001));ff=parts(free);rows=[]
 for sh,name in((fp,'full-source-floor-eroded_100_1um'),(ff,'bounded-complete-free')):
  assigned=[]
  for group in ar:
   assigned.append(sorted({i for q in group['points_mm']for i,p in enumerate(sh)if p.covers(Point(q))}))
  pairs=[]
  for i in assigned[0]:
   for j in assigned[1]:
    a,b=nearest_points(sh[i],sh[j]);pairs.append({'left':i,'right':j,'distance_mm':a.distance(b),'nearest_points_mm':[[a.x,a.y],[b.x,b.y]],'left_area_mm2':sh[i].area,'right_area_mm2':sh[j].area,'left_bounds':list(sh[i].bounds),'right_bounds':list(sh[j].bounds)})
  rows.append({'scope':name,'all_component_count':len(sh),'left_component_indices':assigned[0],'right_component_indices':assigned[1],'common_components':sorted(set(assigned[0])&set(assigned[1])),'pairs':sorted(pairs,key=lambda r:r['distance_mm'])[:8]})
 (OUT/'receipt.json').write_text(json.dumps(rows,indent=1)+'\n',encoding='utf-8');print(json.dumps(rows))
if __name__=='__main__':main()
