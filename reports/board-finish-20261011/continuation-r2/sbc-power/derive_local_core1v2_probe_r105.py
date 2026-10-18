"""Preserve R104 failed no-F-layer goal evidence; probe actual flashed F ports."""
from pathlib import Path
H=Path(__file__).resolve().parent;s=(H/'probe_core1v2_local_outer_joins_r104.py').read_text()
assert s.count("O=L.OUT/'core1v2-local-outer-join-nominees-r104'")==1;s=s.replace("O=L.OUT/'core1v2-local-outer-join-nominees-r104'","O=L.OUT/'core1v2-local-outer-join-nominees-r105'")
old="""        for ref,pin in preferred:
            goal=next(q for q in h['pads'] if (q['ref'],q['num'])==(ref,pin));assert goal['net']==raw;gshape=unary_union(p.base.polygons(goal['layers']['F.Cu']));a,bp=nearest_points(body.buffer(-.03),gshape.buffer(-.03));coords=[list(map(lambda x:round(x,6),s)) for s in (a.coords[0],bp.coords[0])];line=LineString(coords);errors=[];region=line.buffer(2)"""
new="""        goals=[]
        for ref,pin in preferred:
            goal=next(q for q in h['pads'] if (q['ref'],q['num'])==(ref,pin));assert goal['net']==raw
            if 'F.Cu' in goal['layers']:goals.append((ref,pin,unary_union(p.base.polygons(goal['layers']['F.Cu']))))
        for via in h['vias']:
            if via['net']==raw and 'F.Cu' in via['flashed'] and Point(via['x'],via['y']).distance(body)<15:
                gshape=Point(via['x'],via['y']).buffer(via['d']/2).difference(Point(via['x'],via['y']).buffer(via['drill']/2));goals.append(('@VIA',via['uuid'],gshape))
        goals.sort(key=lambda q:q[2].distance(body))
        for ref,pin,gshape in goals:
            a,bp=nearest_points(body.buffer(-.03),gshape.buffer(-.03));coords=[list(map(lambda x:round(x,6),s)) for s in (a.coords[0],bp.coords[0])];line=LineString(coords);errors=[];region=line.buffer(2)"""
assert s.count(old)==1;s=s.replace(old,new)
s=s.replace("'CORE1V2-local-r104-'","'CORE1V2-local-r105-'")
s=s.replace("[(r['goal'],len(r['errors'])) for r in attempts if r['target']==[target_ref,target_pin]]","[(r['goal'],len(r['errors']),r['errors'][:2]) for r in attempts if r['target']==[target_ref,target_pin]]")
out=H/'probe_core1v2_local_outer_joins_r105.py';assert not out.exists();out.write_text(s);compile(s,str(out),'exec');print('ACTUAL_FLASHED_OUTER_GOAL_DERIVATIVE_READY')
