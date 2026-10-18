"""Read-only parser evidence and bounded convex-partition feasibility probe."""
from pathlib import Path
import sys, json, hashlib, urllib.request, ast, collections, time
ROOT=Path.cwd()
sys.path[:0]=[str(ROOT/'tools'),str(ROOT/'reports/motherboard-ordinary-routing-20261001/isolated-native-geometry-deps-r01')]
import shapely
from shapely.geometry import Polygon
import hardware_route_selected_additive_r02 as e
OUT=ROOT/'reports/freerouting-evaluation-20261002/parser-convex-fallback-inspection-r01'
OUT.mkdir(exist_ok=False)
primary={}
for name,rel in {'Shape.java':'io/specctra/parser/Shape.java','Polygon.java':'io/specctra/parser/Polygon.java','PolylineArea.java':'geometry/planar/PolylineArea.java','PolygonShape.java':'geometry/planar/PolygonShape.java'}.items():
 url='https://raw.githubusercontent.com/freerouting/freerouting/v2.4.1/src/main/java/app/freerouting/'+rel
 data=urllib.request.urlopen(url,timeout=30).read();(OUT/name).write_bytes(data)
 primary[name]={'url':url,'path':str(OUT/name),'sha256':hashlib.sha256(data).hexdigest()}
def area2(p):return sum(x*y1-x1*y for(x,y),(x1,y1)in zip(p,p[1:]+p[:1]))
def edges(p):return list(zip(p,p[1:]+p[:1]))
def clean(p):
 changed=True
 while changed and len(p)>3:
  changed=False;r=[]
  for a,b,c in zip(p[-1:]+p[:-1],p,p[1:]+p[:1]):
   if (b[0]-a[0])*(c[1]-b[1])==(b[1]-a[1])*(c[0]-b[0]):changed=True
   else:r.append(b)
  p=r
 return p
def partition(g):
 tris=list(shapely.get_parts(shapely.constrained_delaunay_triangles(g)))
 pieces={};owners=collections.defaultdict(set);queue=[];merges=0
 for i,t in enumerate(tris):
  p=[tuple(v)for v in list(t.exterior.coords)[:-1]]
  assert all(x.is_integer()and y.is_integer()for x,y in p)
  p=[(int(x),int(y))for x,y in p]
  if area2(p)<0:p.reverse()
  pieces[i]=p
  for a,b in edges(p):owners[tuple(sorted((a,b)))].add(i)
 for edge,ids in owners.items():
  if len(ids)==2:queue.append((edge,*ids))
 # Prefer long internal edges first; all merges require exact integer union
 # boundary, area equality and convexity. No vertex-count threshold.
 queue.sort(key=lambda v:(v[0][0][0]-v[0][1][0])**2+(v[0][0][1]-v[0][1][1])**2)
 while queue:
  edge,i,j=queue.pop()
  if i not in pieces or j not in pieces or owners.get(edge)!=set((i,j)):continue
  a,b=pieces[i],pieces[j];boundary=set(edges(a))
  for x,y in edges(b):
   if(y,x)in boundary:boundary.remove((y,x))
   else:boundary.add((x,y))
  successor={x:y for x,y in boundary}
  if len(successor)!=len(boundary):continue
  start=next(iter(successor));p=[start];at=successor[start]
  while at!=start and at in successor and len(p)<=len(boundary):p.append(at);at=successor[at]
  if at!=start or len(p)!=len(boundary):continue
  if any((y[0]-x[0])*(z[1]-y[1])-(y[1]-x[1])*(z[0]-y[0])<0 for x,y,z in zip(p,p[1:]+p[:1],p[2:]+p[:2])):continue
  assert area2(p)==area2(a)+area2(b)
  # Retain collinear subdivision vertices in the adjacency inventory so an
  # unmerged neighbor still shares the exact edge. Strip only when emitted.
  for old in(a,b):
   for x,y in edges(old):owners[tuple(sorted((x,y)))].discard(i);owners[tuple(sorted((x,y)))].discard(j)
  pieces[i]=p;del pieces[j];merges+=1
  for x,y in edges(p):
   key=tuple(sorted((x,y)));owners[key].add(i)
   if len(owners[key])==2:queue.append((key,*owners[key]))
 result=[clean(p)for p in pieces.values()]
 assert sum(area2(p)for p in result)==round(g.area*2)
 return result,len(tris),merges
if __name__=='__main__':
 d=e.read(ROOT/'reports/freerouting-evaluation-20261002/ROOT103-GPIO-config-convex-DSN-r03/convex-conservative-coverage-review.json')
 tree=e.parse((ROOT/'reports/freerouting-evaluation-20261002/ROOT103-GPIO-config-window-DSN-r04/selected.dsn').read_text())
 ks=e.children(e.child(tree,'structure'),'keepout');rows=[]
 top=sorted(d['records'],key=lambda r:r['replacement_count'],reverse=True)[:10]
 for row in top:
  name='LiteralWindow_'+str(row['original_keepout_index'])+'_0'
  k=next(k for k in ks if e.value(k[1])==name);raw=e.child(k,'polygon')
  coords=lambda r:[(round(float(r[i])*1000),round(float(r[i+1])*1000))for i in range(3,len(r),2)]
  g=Polygon(coords(raw),[coords(e.child(w,'polygon'))for w in e.children(k,'window')]);start=time.monotonic()
  out,nt,nm=partition(g)
  rows.append(dict(index=row['original_keepout_index'],old_pieces=row['replacement_count'],triangles=nt,merged_pieces=len(out),merges=nm,max_vertices=max(map(len,out)),seconds=time.monotonic()-start))
  print(json.dumps(rows[-1]),flush=True)
 e.write(OUT/'inspection.json',dict(primary=primary,copy_only=True,rows=rows,passed=True,feasibility_only=True,no_DSN_or_native_board_modified=True,source_warning='Window grammar is legal but parser geometry still performs recursive convex decomposition and hole cutouts.'))
