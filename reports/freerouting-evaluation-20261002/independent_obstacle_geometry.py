"""Independent source-ring reconstruction for a read-only DSN coverage audit.

This module deliberately does not import the obstacle converter. Invalid
fractured contours are reconstructed by noding linework, polygonizing cells,
and selecting cells by the original ring's even/odd crossings. No area
tolerance, automatic buffer(0), or deletion of small islands is permitted.
"""
from pathlib import Path
import sys
ROOT=Path.cwd()
sys.path.insert(0,str(ROOT/'reports/motherboard-ordinary-routing-20261001/isolated-native-geometry-deps-r01'))
from shapely.geometry import Polygon,LineString,GeometryCollection
from shapely.ops import unary_union,polygonize


def odd_crossings(point, ring):
    x,y=point
    inside=False
    for (ax,ay),(bx,by) in zip(ring,ring[1:]+ring[:1]):
        if (ay>y)!=(by>y) and x < ax+(y-ay)*(bx-ax)/(by-ay):
            inside=not inside
    return inside


def reconstruct(outer,holes):
    direct=Polygon(outer,holes)
    rings=[outer,*holes]
    lines=unary_union([LineString(r+[r[0]])for r in rings if len(r)>1])
    if direct.is_valid and direct.area>0:
        return direct,lines,False
    kept=[]
    for cell in polygonize(lines):
        point=cell.representative_point()
        xy=(point.x,point.y)
        if odd_crossings(xy,outer) and not any(odd_crossings(xy,h)for h in holes):
            kept.append(cell)
    result=unary_union(kept) if kept else GeometryCollection()
    assert result.is_valid
    return result,lines,True


if __name__=='__main__':
    # A doubled bridge joins outer/hole loops without filling the hole. The
    # disconnected island and zero-width spur are retained in their own roles.
    ring=[(0,0),(10,0),(10,10),(0,10),(0,0),(2,2),(2,8),(8,8),(8,2),(2,2),(0,0)]
    shape,lines,rebuilt=reconstruct(ring,[])
    expected=Polygon([(0,0),(10,0),(10,10),(0,10)], [[(2,2),(8,2),(8,8),(2,8)]])
    assert rebuilt and shape.symmetric_difference(expected).is_empty
    assert not shape.contains(__import__('shapely').geometry.Point(5,5))
    shape,_,rebuilt=reconstruct([(0,0),(2,0),(2,2),(0,2)],[])
    assert not rebuilt and shape.area==4
    print('Independent bridged-hole reconstruction controls PASS')
