"""Native 1nm polygon splices with literal positive/negative coverage gates.

Preserve every original native vertex that survives the Boolean operation.
New intersections snap outward for positive field edits or inward for negative
ground edits. Every resulting wedge must be inventoried by its caller.
"""
import math
import shapely
from shapely.geometry import Point,LineString,Polygon,MultiPolygon
from shapely.prepared import prep
from shapely.strtree import STRtree

def parts(s):
    if s.is_empty:return []
    if s.geom_type=='Polygon':return [s]
    return [p for a in getattr(s,'geoms',[])for p in parts(a)]

def splice(old,boolean,positive):
    old=shapely.set_precision(old,0);boolean=shapely.set_precision(boolean,0)
    oldpoints={tuple(p)for p in shapely.get_coordinates(old)}
    assert all(float(f'{x:.6f}')==x for p in oldpoints for x in p),'Original source intent is not literal native1nm'
    edges=[]
    for p in parts(old):
        for ring in[p.exterior,*p.interiors]:
            c=list(ring.coords);edges.extend(LineString([a,b])for a,b in zip(c,c[1:])if a!=b)
    tree=STRtree(edges);prepared=prep(old);attempts=[]
    def edge_distance(point):return point.distance(edges[int(tree.nearest(point))])
    for margin_nm in(0,1,2,4,8,16,32):
        moved=[];preserved=0;newpolys=[]
        def snap(ring):
            nonlocal preserved
            out=[]
            for pp in list(ring.coords)[:-1]:
                p=tuple(pp)
                if p in oldpoints:q=p;preserved+=1
                else:
                    x,y=p;ix=math.floor(x*1e6);iy=math.floor(y*1e6);reach=max(2,margin_nm+2);candidates=[]
                    for a in range(ix-reach,ix+reach+2):
                        for b in range(iy-reach,iy+reach+2):
                            q0=(a/1e6,b/1e6);pt=Point(q0)
                            side=(not prepared.covers(pt))if positive else prepared.contains(pt)
                            if not side:continue
                            if margin_nm and edge_distance(pt)<margin_nm*1e-6:continue
                            candidates.append(((q0[0]-x)**2+(q0[1]-y)**2,q0))
                    if not candidates:raise ValueError('No native lattice candidate on required side')
                    _,q=min(candidates);moved.append({'old_boolean_point_mm':list(p),'native_point_mm':list(q),'move_mm':math.dist(p,q)})
                if not out or out[-1]!=q:out.append(q)
            if out and out[-1]==out[0]:out.pop()
            if len(out)<3:raise ValueError('Collapsed source contour')
            return out
        try:
            for p in parts(boolean):newpolys.append(Polygon(snap(p.exterior),[snap(r)for r in p.interiors]))
            new=MultiPolygon(newpolys)if len(newpolys)>1 else newpolys[0]
            if not new.is_valid:raise ValueError('Native splice is invalid')
            forbidden=old.difference(new)if positive else new.difference(old)
            attempt={'margin_nm':margin_nm,'valid':True,'forbidden_empty':forbidden.is_empty,'forbidden_area_mm2':forbidden.area,'preserved_source_vertex_occurrences':preserved,'new_or_shifted_vertex_count':len(moved)};attempts.append(attempt)
            if forbidden.is_empty:
                assert all(float(f'{x:.6f}')==x for row in shapely.get_coordinates(new)for x in row)
                return new,{'positive':positive,'literal_old_subset_of_new':positive,'literal_new_subset_of_old':not positive,'attempts':attempts,'selected_margin_nm':margin_nm,'native_moves':moved,'all_old_surviving_native_vertices_preserved':True,'no_area_or_distance_waiver':True}
        except(ValueError,TypeError)as error:attempts.append({'margin_nm':margin_nm,'valid':False,'reason':str(error)})
    raise ValueError({'status':'NO_LITERAL_NATIVE_LATTICE_SPLICE','attempts':attempts})
