"""Conservative local-clearance/minimum-web projection, distinct from native refill."""
import copy
from shapely.ops import unary_union
from shapely import set_precision

def projected(g,h,zones):
    import complete_geometry_r2 as G
    original,ledger=G.projected(g,h,zones)
    prior={q['uuid']:q for q in h['zones']};out=[];extra=[]
    for z in original['zones']:
        row=copy.deepcopy(z)
        if z['uuid'] in prior:
            old=prior[z['uuid']];local=float(old.get('clearance_mm') or .15)
            for layer,rs in z['fills'].items():
                before=unary_union(G.p.base.polygons(rs))
                cutters=[q['shape'].buffer(max(G.gap(h,z['net'],q['net']),local,.15)+.025) for q in zones if q['layer']==layer and G.p.norm(q['net'])!=G.p.norm(z['net'])]
                after=before.difference(unary_union(cutters))
                row['fills'][layer]=G.records(after)
                delta=before.difference(after)
                if delta.area>1e-8:extra.append({'zone_uuid':z['uuid'],'net_raw':z['net'],'layer':layer,'native_old_local_clearance_mm':local,'extra_clearance_removed_area_mm2':delta.area})
        out.append(row)
    return {**original,'zones':out},ledger+extra

def minimum_web_screen(zones,minimum=.15):
    """Erase subminimum detached components without assigning them continuity credit."""
    rows=[]
    for q in zones:
        parts=[q['shape']] if q['shape'].geom_type=='Polygon' else list(q['shape'].geoms)
        parts=sorted(parts,key=lambda p:(-p.area,p.bounds))
        for i,p in enumerate(parts):
            interior=p.buffer(-minimum/2)
            rows.append({'uuid':q['uuid'],'net_raw':q['net'],'layer':q['layer'],'part_index':i,'area_mm2':p.area,'survives_minimum_interior':not interior.is_empty,'core_area_mm2':interior.area,'native_fill_qualification':False})
    return rows
