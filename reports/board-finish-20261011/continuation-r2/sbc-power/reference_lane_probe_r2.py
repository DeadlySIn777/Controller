import json,math
from shapely.geometry import box,Point
from shapely.ops import unary_union
import core_lane_r2 as R
def main():
    g,h,scope,native,prior,omit=R.model();p=R.p;p.WINDOW=box(103,100,250,175)
    points=[(188,115),(190,115),(192,115),(190,125),(192,125),(196,110),(199,110),(202,110),(194,140),(195,141)]
    rows=[]
    for x,y in points:
        pt=Point(x,y);fills={}
        for layer in ('In1.Cu','In4.Cu'):
            nearby=[]
            for z in g['zones']:
                if layer not in z['fills']:continue
                polys=R.p.base.polygons(z['fills'][layer]);nearest=min((poly.distance(pt) for poly in polys),default=1e9)
                if nearest<3:nearby.append({'uuid':z['uuid'],'net':z['net'],'distance':nearest})
            fills[layer]={'source_ground_distance':g['_rooted_refs'][layer].distance(pt),'source_ground_interior_margin':pt.distance(g['_rooted_refs'][layer].boundary),'nearby_fills':nearby}
        rows.append({'at':[x,y],'planes':fills})
    (R.L.OUT/'reference-lane-probe-r2.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
if __name__=='__main__':main()
