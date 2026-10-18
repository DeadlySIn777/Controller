"""Reduced search meshes with exact original-polygon path verification.

Simplification is a search aid only. Every accepted line segment remains covered
by the untouched 1 nm polygon. An eroded simplified component must be wholly
covered by that polygon before it can be used as a routing mesh.
"""
import math
from shapely.geometry import Point,LineString
from shapely.ops import nearest_points
import continuous_path_r2 as exact

def path(poly,start,end,node_cap=500000):
    direct=LineString([start,end])
    if poly.covers(direct):
        return {'verdict':'HOST_PATH','points':[list(start),list(end)],'length_mm':direct.length,'continuous_polygon_triangles':0,'every_segment_exact_polygon_covered':True}
    attempts=[]
    for tolerance in (.02,.005,.001):
        reduced=poly.buffer(-tolerance*2).simplify(tolerance,preserve_topology=True)
        components=list(reduced.geoms) if hasattr(reduced,'geoms') else [reduced]
        choices=[]
        for component in components:
            if component.is_empty or component.geom_type!='Polygon':continue
            a=nearest_points(Point(start),component)[1].coords[0]
            b=nearest_points(Point(end),component)[1].coords[0]
            if not poly.covers(LineString([start,a])) or not poly.covers(LineString([b,end])):continue
            choices.append((math.dist(start,a)+math.dist(b,end),component,a,b))
        for _,component,a,b in sorted(choices,key=lambda q:q[0])[:3]:
            if not poly.covers(component):
                attempts.append({'simplification_tolerance_mm':tolerance,'verdict':'REDUCED_POLYGON_NOT_CONTAINED'});continue
            route=exact.path(component,a,b,node_cap=node_cap)
            attempts.append({'simplification_tolerance_mm':tolerance,'verdict':route['verdict'],'triangles':route.get('continuous_polygon_triangles',route.get('triangle_count'))})
            if route['verdict']!='HOST_PATH':continue
            points=[list(start)]+route['points']+[list(end)]
            points=[q for i,q in enumerate(points) if i==0 or q!=points[i-1]]
            if not all(poly.covers(LineString([a,b])) for a,b in zip(points,points[1:])):continue
            return {**route,'points':points,'length_mm':LineString(points).length,'every_segment_exact_polygon_covered':True,'reduced_mesh_wholly_exact_polygon_covered':True,'search_simplification_tolerance_mm':tolerance,'search_attempts':attempts}
    route=exact.path(poly,start,end,node_cap=node_cap)
    return {**route,'search_attempts':attempts,'full_mesh_fallback':True}
