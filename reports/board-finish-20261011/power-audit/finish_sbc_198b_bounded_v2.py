"""Distinct gate: independently prove exact connectors, including direct shortcuts.

The frozen v1 gate withheld direct helper results for omitted connector metadata.
This gate verifies the geometry itself; no old receipt, board or tool is edited.
"""
import json,math
from shapely.geometry import Point,LineString,box
import finish_sbc_198b_bounded as F

def route_accepted(route,start,end,free):
    if not isinstance(route,dict) or route.get('verdict')!='HOST_PATH':return False
    if route.get('exact_native_endpoint_connectors_checked') is False:return False
    points=route.get('points')
    if not isinstance(points,list) or not points:return False
    if any(not isinstance(pt,(tuple,list)) or len(pt)!=2 or any(not isinstance(v,(float,int)) or isinstance(v,bool) or not math.isfinite(v) for v in pt) for pt in points):return False
    if math.dist(points[0],start)>1e-8 or math.dist(points[-1],end)>1e-8:return False
    if not all(free.covers(Point(pt)) for pt in points):return False
    if not all(free.covers(LineString([a,b])) for a,b in zip(points,points[1:]) if math.dist(a,b)>1e-9):return False
    length=sum(math.dist(a,b) for a,b in zip(points,points[1:]))
    reported=route.get('length_mm')
    return isinstance(reported,(float,int)) and not isinstance(reported,bool) and math.isfinite(reported) and abs(reported-length)<1e-6

def controls():
    free=box(-1,-1,2,2);start,end=(0.,0.),(1.,1.)
    good={'verdict':'HOST_PATH','points':[[0.,0.],[1.,1.]],'length_mm':math.sqrt(2),'searched_nodes':0}
    rows=[]
    def test(name,route,a,b,geometry,expected):
        actual=route_accepted(route,a,b,geometry)
        if actual!=expected:raise ValueError('route gate control failed: '+name)
        rows.append({'name':name,'expected_accept':expected,'actual_accept':actual})
    test('exact direct helper shortcut without redundant metadata',good,start,end,free,True)
    test('truthy NO_PATH dictionary',{'verdict':'NO_PATH_AT_GRID_OR_NODE_CAP'},start,end,free,False)
    test('HOST_PATH missing points',{**good,'points':None},start,end,free,False)
    test('explicit failed connector evidence',{**good,'exact_native_endpoint_connectors_checked':False},start,end,free,False)
    test('wrong exact native terminal',{**good,'points':[[.001,0.],[1.,1.]]},start,end,free,False)
    test('nonfinite point',{**good,'points':[[0.,0.],[float('nan'),1.]]},start,end,free,False)
    test('false reported length',{**good,'length_mm':1.},start,end,free,False)
    test('diagonal through exact wall',good,start,end,free.difference(box(.4,-1,.6,2)),False)
    test('zero length exact shared hub',{'verdict':'HOST_PATH','points':[[0.,0.],[0.,0.]],'length_mm':0.,'searched_nodes':0},start,start,free,True)
    test('zero length wrong shared hub',{'verdict':'HOST_PATH','points':[[0.,0.],[0.,0.]],'length_mm':0.,'searched_nodes':0},start,end,free,False)
    return rows

def main():
    F.route_accepted=route_accepted;F.controls=controls
    F.DEST=F.OUT/'final-bounded-blocker-v2.json'
    F.main()

if __name__=='__main__':main()
