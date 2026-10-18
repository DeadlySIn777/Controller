"""Explicit outward-bound projection for final proposed power geometry.

Original native definitions remain unchanged. The returned old fill shapes
are a host projection, not native refill evidence. New-zone correction is
separate and returns an explicit mutation ledger before contact auditing.
"""
import copy, math, hashlib
from shapely import set_precision, STRtree
from shapely.geometry import Point, LineString
from shapely.ops import unary_union
import complete_geometry_r2 as G
p=G.p
GRID=1e-6
ARC_QUADS=64
OUTWARD_MM=.000002

def bounded_buffer(shape,distance):
    assert distance>0
    return set_precision(shape.buffer((distance+OUTWARD_MM)/math.cos(math.pi/(4*ARC_QUADS)),quad_segs=ARC_QUADS),GRID)

def bounded_disk(v,radius):
    return bounded_buffer(Point(v['x'],v['y']),radius)

def digest(shape):return hashlib.sha256(shape.wkb).hexdigest()

def changed_ids(g,h):
    result=set()
    for kind in ('tracks','vias','pads'):
        old={q['uuid']:q for q in g[kind]}
        result.update(q['uuid'] for q in h[kind] if q['uuid'] not in old or q!=old[q['uuid']])
    return result

def normalize_owned_via_guards(h,zones):
    """Cut every foreign actual/prospective via disk from owned proposals.

    Both physical and intended outlines lose foreign antipads; own drill
    cutouts stay physical-only. Never edit original zone definitions here.
    """
    vias=h['vias'];tree=STRtree([Point(v['x'],v['y']) for v in vias]);out=[];ledger=[]
    for q in zones:
        before=q['shape'];outline_before=q.get('zone_outline_shape',before)
        rows=[]
        for j in tree.query(outline_before.buffer(1.5),predicate='intersects'):
            v=vias[int(j)]
            if p.norm(v['net'])==p.norm(q['net']):continue
            clear=max(G.gap(h,q['net'],v['net']),float(q.get('clearance_mm',.15)))+.025
            radius=v['drill']/2+.275
            if q['layer'] in v['flashed']:radius=max(radius,v['d']/2+clear)
            cut=bounded_disk(v,radius)
            if cut.intersects(outline_before):rows.append((v,cut,radius,clear))
        if not rows:out.append(copy.deepcopy(q));continue
        cutters=unary_union([r[1] for r in rows]);after=set_precision(set_precision(before,GRID).difference(cutters),GRID)
        outline_after=set_precision(set_precision(outline_before,GRID).difference(cutters),GRID)
        result=copy.deepcopy(q);result['shape']=after;result['zone_outline_shape']=outline_after;out.append(result)
        if before.equals(after) and outline_before.equals(outline_after):continue
        ledger.append({'zone_uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],
            'physical_before_WKB_SHA256':digest(before),'physical_after_WKB_SHA256':digest(after),
            'outline_before_WKB_SHA256':digest(outline_before),'outline_after_WKB_SHA256':digest(outline_after),
            'physical_removed_area_mm2':before.difference(after).area,'physical_quantization_added_area_mm2':after.difference(before).area,
            'outline_removed_area_mm2':outline_before.difference(outline_after).area,'outline_quantization_added_area_mm2':outline_after.difference(outline_before).area,
            'cutters':[{'via_uuid':v['uuid'],'raw_net':v['net'],'analytic_radius_mm':radius,'required_Cu_gap_with_guard_mm':clear,'outward256edge_WKB_SHA256':digest(cut)} for v,cut,radius,clear in rows],
            'cutters_union_WKB_SHA256':digest(cutters),'fresh_contact_current_native_audit_required':True})
    return out,ledger

def projected(g,h,zones):
    """Preserve local clearances; enclose circle/corner planning guards."""
    changed=changed_ids(g,h);cache={};ledger=[];result=[]
    def cutters(net,layer,local):
        key=(net,layer,local)
        if key in cache:return cache[key]
        rows=[]
        for t in h['tracks']:
            if t['uuid'] not in changed or t['layer']!=layer or p.norm(t['net'])==p.norm(net):continue
            clear=max(G.gap(h,net,t['net']),local)
            rows.append((t['uuid'],bounded_buffer(LineString([t['a'],t['b']]),t['w']/2+clear+.025),'changed_track_outward_Cu',clear))
        for v in h['vias']:
            if v['uuid'] not in changed or p.norm(v['net'])==p.norm(net):continue
            clear=max(G.gap(h,net,v['net']),local);radius=v['drill']/2+.275
            if layer in v['flashed']:radius=max(radius,v['d']/2+clear+.025)
            rows.append((v['uuid'],bounded_disk(v,radius),'changed_via_outward_Cu_and_hole',clear))
        for q in h['pads']:
            if q['uuid'] not in changed or p.norm(q['net'])==p.norm(net):continue
            clear=max(G.gap(h,net,q['net']),local)
            for sh in p.base.polygons(q['layers'].get(layer,[])):rows.append((q['uuid'],bounded_buffer(sh,clear+.025),'changed_pad_outward_polygon',clear))
        for q in zones:
            if q['layer']!=layer or p.norm(q['net'])==p.norm(net):continue
            clear=max(G.gap(h,net,q['net']),local,float(q.get('clearance_mm',.15)))
            rows.append((q['uuid'],bounded_buffer(q['shape'],clear+.025),'new_zone_outward_polygon',clear))
        cache[key]=(rows,unary_union([r[1] for r in rows]));return cache[key]
    for z in h['zones']:
        row=copy.deepcopy(z);row['fills']={};local=float(z['clearance_mm'])
        for layer,records in z['fills'].items():
            original=unary_union(p.base.polygons(records));rows,cut=cutters(z['net'],layer,local)
            remaining=original.difference(cut);row['fills'][layer]=G.records(remaining);removed=original.difference(remaining)
            if not removed.is_empty:ledger.append({'zone_uuid':z['uuid'],'net_raw':z['net'],'layer':layer,
                'native_original_local_clearance_mm':local,'native_original_priority':z['priority'],'native_original_min_thickness_mm':z['min_thickness_mm'],
                'old_WKB_SHA256':digest(original),'new_WKB_SHA256':digest(remaining),'removed_Cu_area_mm2':removed.area,
                'cutters':[{'uuid':uid,'kind':kind,'clearance_mm_before_guard':clear,'outward_cutter_WKB_SHA256':digest(shape)} for uid,shape,kind,clear in rows if shape.intersects(original)]})
        result.append(row)
    for q in zones:result.append({'uuid':q['uuid'],'net':q['net'],'priority':int(q.get('priority',124)),'clearance_mm':float(q.get('clearance_mm',.15)),'min_thickness_mm':float(q.get('min_thickness_mm',.15)),'pad_connect_mode':q.get('pad_connect_mode','FULL_SOLID'),'island_removal_mode':int(q.get('island_removal_mode',1)),'thermal_gap_mm':float(q.get('thermal_gap_mm',.15)),'thermal_bridge_width_mm':float(q.get('thermal_bridge_width_mm',.3)),
        'fills':{q['layer']:G.records(q['shape'])},'prospective_not_native':True})
    return {**h,'zones':result},ledger
