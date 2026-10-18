"""Native-local-clearance-aware prospective fill subtraction.

Original zone definitions/configuration remain unchanged. This host projection
does not model KiCad's minimum thickness, island deletion or exact refill.
"""
import copy
from shapely.geometry import Point
from shapely.ops import unary_union
import complete_geometry_r2 as G
p=G.p
def projected(g,h,zones):
    old_ids={q['uuid'] for k in ('tracks','vias','pads') for q in g[k]}
    changed={q['uuid'] for k in ('tracks','vias','pads') for q in h[k] if q['uuid'] not in old_ids}
    for kind in ('tracks','vias','pads'):
        old={q['uuid']:q for q in g[kind]}
        changed|={q['uuid'] for q in h[kind] if q['uuid'] in old and q!=old[q['uuid']]}
    cache={};ledger=[];result=[]
    def cutters(net,layer,local):
        key=(net,layer,local)
        if key in cache:return cache[key]
        rows=[]
        def copper(uid,other,shape,kind):
            clear=max(G.gap(h,net,other),local)
            rows.append((uid,shape.buffer(clear+.025),kind,clear))
        for t in h['tracks']:
            if t['uuid'] in changed and t['layer']==layer and p.norm(t['net'])!=p.norm(net):copper(t['uuid'],t['net'],p.base.body(t),'changed_track')
        for v in h['vias']:
            if v['uuid'] not in changed or p.norm(v['net'])==p.norm(net):continue
            clear=max(G.gap(h,net,v['net']),local)
            radius=v['drill']/2+.25+.025
            if layer in v['flashed']:radius=max(radius,v['d']/2+clear+.025)
            rows.append((v['uuid'],Point(v['x'],v['y']).buffer(radius),'changed_via_Cu_and_hole',clear))
        for q in h['pads']:
            if q['uuid'] in changed and p.norm(q['net'])!=p.norm(net):
                for sh in p.base.polygons(q['layers'].get(layer,[])):copper(q['uuid'],q['net'],sh,'changed_pad')
        for q in zones:
            if q['layer']==layer and p.norm(q['net'])!=p.norm(net):
                clear=max(G.gap(h,net,q['net']),local,float(q.get('clearance_mm',.15)))
                rows.append((q['uuid'],q['shape'].buffer(clear+.025),'new_zone',clear))
        cache[key]=(rows,unary_union([s for _,s,_,_ in rows]));return cache[key]
    for z in h['zones']:
        row=copy.deepcopy(z);row['fills']={};local=float(z['clearance_mm'])
        for layer,records in z['fills'].items():
            original=unary_union(p.base.polygons(records));rows,cut=cutters(z['net'],layer,local);remaining=original.difference(cut)
            row['fills'][layer]=G.records(remaining)
            removed=original.difference(remaining)
            if not removed.is_empty:ledger.append({'zone_uuid':z['uuid'],'net_raw':z['net'],'layer':layer,'native_original_local_clearance_mm':local,'native_original_priority':z['priority'],'native_original_min_thickness_mm':z['min_thickness_mm'],'removed_Cu_area_mm2':removed.area,'cutters':[{'uuid':u,'kind':kind,'clearance_mm_before_guard':c} for u,s,kind,c in rows if s.intersects(original)]})
        result.append(row)
    for q in zones:result.append({'uuid':q['uuid'],'net':q['net'],'priority':124,'clearance_mm':float(q.get('clearance_mm',.15)),'min_thickness_mm':.15,'fills':{q['layer']:G.records(q['shape'])},'prospective_not_native':True})
    return {**h,'zones':result},ledger
