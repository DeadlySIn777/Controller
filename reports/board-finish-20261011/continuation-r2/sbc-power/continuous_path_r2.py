"""Host continuous polygon path through constrained triangle portals."""
import math,heapq
from shapely import constrained_delaunay_triangles,STRtree
from shapely.geometry import Point,LineString
def path(poly,start,end,node_cap=500000):
    direct=LineString([start,end])
    if poly.covers(direct):return {'verdict':'HOST_PATH','points':[list(start),list(end)],'length_mm':direct.length,'continuous_polygon_triangles':0}
    triangles=list(constrained_delaunay_triangles(poly).geoms)
    if len(triangles)>node_cap:return {'verdict':'TRIANGLE_CAP','triangle_count':len(triangles)}
    tree=STRtree(triangles);ss=tree.query(Point(start),predicate='intersects');ee=set(map(int,tree.query(Point(end),predicate='intersects')))
    if not len(ss) or not ee:return {'verdict':'TRIANGLE_ENDPOINT_MISSING'}
    adj=[[] for _ in triangles];edges={};centres=[t.centroid.coords[0] for t in triangles]
    for i,t in enumerate(triangles):
        vertices=list(t.exterior.coords)[:3]
        for a,b in zip(vertices,vertices[1:]+vertices[:1]):
            key=tuple(sorted((tuple(round(x,10) for x in a),tuple(round(x,10) for x in b))))
            if key in edges:
                j=edges.pop(key);portal=((a[0]+b[0])/2,(a[1]+b[1])/2);adj[i].append((j,portal));adj[j].append((i,portal))
            else:edges[key]=i
    distance={int(i):0. for i in ss};prev={};heap=[(math.dist(centres[int(i)],end),0.,int(i)) for i in ss];heapq.heapify(heap);goal=None
    while heap:
        _,cost,i=heapq.heappop(heap)
        if cost!=distance.get(i):continue
        if i in ee:goal=i;break
        for j,portal in adj[i]:
            q=cost+math.dist(centres[i],centres[j])
            if q<distance.get(j,math.inf):distance[j]=q;prev[j]=(i,portal);heapq.heappush(heap,(q+math.dist(centres[j],end),q,j))
    if goal is None:return {'verdict':'NO_TRIANGLE_PATH','triangle_count':len(triangles)}
    portals=[];i=goal
    while i in prev:i,portal=prev[i];portals.append(portal)
    points=[tuple(start)]+list(reversed(portals))+[tuple(end)]
    # Remove redundant portal vertices without crossing any real copper obstacle.
    out=[points[0]];idx=0
    while idx<len(points)-1:
        upper=min(len(points)-1,idx+100)
        while upper>idx+1 and not poly.covers(LineString([points[idx],points[upper]])):upper-=1
        if not poly.covers(LineString([points[idx],points[upper]])):return {'verdict':'PORTAL_SEGMENT_NOT_COVERED','triangle_count':len(triangles)}
        out.append(points[upper]);idx=upper
    return {'verdict':'HOST_PATH','points':[list(x) for x in out],'length_mm':LineString(out).length,'continuous_polygon_triangles':len(triangles),'every_segment_exact_polygon_covered':True}
