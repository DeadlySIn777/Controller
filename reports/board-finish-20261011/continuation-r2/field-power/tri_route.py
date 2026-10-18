"""Construct an exact polygon-contained route through constrained triangles."""
import heapq,math
import numpy as np
import shapely
from shapely.geometry import Point,LineString
from shapely.strtree import STRtree

def route(free,start,end):
 a=Point(start);b=Point(end)
 assert free.covers(a) and free.covers(b)
 if free.covers(LineString([start,end])):return [start,end],{'method':'exact_direct_polygon_coverage','triangles':0}
 ts=list(shapely.constrained_delaunay_triangles(free).geoms)
 shapely.prepare(free)
 assert np.all(shapely.covers(free,np.array(ts,dtype=object)))
 tree=STRtree(ts);centers=[tuple(t.centroid.coords[0]) for t in ts];adj=[[] for t in ts];edges={};portals={}
 for i,t in enumerate(ts):
  ps=list(t.exterior.coords)[:-1];assert len(ps)==3
  for x,y in zip(ps,ps[1:]+ps[:1]):
   key=tuple(sorted((tuple(x),tuple(y))))
   if key in edges:
    j=edges.pop(key);adj[i].append(j);adj[j].append(i);portals[(min(i,j),max(i,j))]=((x[0]+y[0])/2,(x[1]+y[1])/2)
   else:edges[key]=i
 ss=[int(i) for i in tree.query(a) if ts[int(i)].covers(a)];gg={int(i) for i in tree.query(b) if ts[int(i)].covers(b)};assert ss and gg
 cost={};prev={};queue=[]
 for i in ss:cost[i]=math.dist(start,centers[i]);heapq.heappush(queue,(cost[i]+math.dist(centers[i],end),cost[i],i))
 expanded=0;finish=None
 while queue:
  _,distance,i=heapq.heappop(queue)
  if distance>cost[i]+1e-12:continue
  expanded+=1
  if i in gg:finish=i;break
  for j in adj[i]:
   mid=portals[(min(i,j),max(i,j))];new=distance+math.dist(centers[i],mid)+math.dist(mid,centers[j])
   if new+1e-12<cost.get(j,math.inf):cost[j]=new;prev[j]=i;heapq.heappush(queue,(new+math.dist(centers[j],end),new,j))
 if finish is None:raise ValueError('Constrained triangle graph disconnected despite continuous polygon proof')
 chain=[finish]
 while chain[-1] in prev:chain.append(prev[chain[-1]])
 chain.reverse();raw=[tuple(start),centers[chain[0]]]
 for i,j in zip(chain,chain[1:]):raw.extend([portals[(min(i,j),max(i,j))],centers[j]])
 raw.append(tuple(end));assert free.covers(LineString(raw))
 # Every selected chord is verified against the exact free polygon. The
 # exponential/binary search only accelerates simplification; it never grants
 # passage across an untested obstacle or assumes raster connectivity.
 result=[raw[0]];i=0;tests=0
 while i<len(raw)-1:
  last=i+1;jump=2;upper=len(raw)-1
  while i+jump<len(raw):
   j=i+jump;tests+=1
   if free.covers(LineString([raw[i],raw[j]])):last=j;jump*=2
   else:upper=j;break
  else:
   tests+=1
   if free.covers(LineString([raw[i],raw[-1]])):last=len(raw)-1
  lo,hi=last+1,upper
  while lo<=hi:
   j=(lo+hi)//2;tests+=1
   if free.covers(LineString([raw[i],raw[j]])):last=j;lo=j+1
   else:hi=j-1
  result.append(raw[last]);i=last
 assert free.covers(LineString(result))
 return result,{'method':'constrained_triangle_graph_then_exact_covered_chords','triangles':len(ts),'triangle_nodes_expanded':expanded,'triangle_chain':len(chain),'raw_points':len(raw),'covered_chord_tests':tests,'final_points':len(result)}
