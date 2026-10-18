"""Finite annular nomination on exact continuous centre polygons."""
import math
from shapely.geometry import Point
from shapely.ops import unary_union,nearest_points
import audit_ao1_positive_operation_r2 as Q

def candidates(region,refs,signal,positions):
    p=Point(signal);ring=p.buffer(1.,resolution=256).difference(p.buffer(.81-1e-9,resolution=256))
    legal=region.intersection(ring)
    for at in positions:
        if tuple(at)!=tuple(signal):legal=legal.difference(Point(at).buffer(.81-1e-9,resolution=256))
    physical=legal
    areas={'physical_ordinary_ring_mm2':legal.area}
    for layer in ('F.Cu','B.Cu'):
        legal=legal.intersection(refs[layer].buffer(-.075).buffer(.25,resolution=128))
        areas['after_'+layer+'_finite_annular_nomination_mm2']=legal.area
    points=[]
    for component in sorted(Q.P.K.D.components(legal),key=lambda p:(-p.area,p.bounds)):
        sites=[component.representative_point()]
        if component.covers(component.centroid):sites.append(component.centroid)
        inner=component.buffer(-.005)
        if not inner.is_empty:sites.extend(p.representative_point() for p in Q.P.K.D.components(inner))
        toward=nearest_points(component,Point(signal[0]-.75,signal[1]-.65))[0]
        middle=component.representative_point()
        for fraction in (.05,.2,.5):
            site=Point(toward.x*(1-fraction)+middle.x*fraction,toward.y*(1-fraction)+middle.y*fraction)
            if component.covers(site):sites.append(site)
        for site in sites:
            at=(round(site.x,9),round(site.y,9));point=Point(at)
            if legal.covers(point) and at not in points:points.append(at)
    return points,legal,physical,areas

def site_blockers(model,net,at,smd,centres,positions):
    p=Point(at);body=p.buffer(.25,resolution=128);hole=p.buffer(.1,resolution=128);domain=model.domains[net];out=[]
    i=int(smd.nearest(p));gap=p.distance(smd.geometries[i])-.1-.005
    if gap<.275:out.append({'kind':'all_SMD_drill_aperture','gap_after_export_error_mm':gap})
    for i in centres.query(p.buffer(.81-1e-9),predicate='intersects'):out.append({'kind':'ordinary_old_via_pitch','source_via_at_mm':list(centres.geometries[int(i)].coords)[0]})
    for old in positions:
        if math.dist(old,at)<.81-1e-9:out.append({'kind':'ordinary_new_via_pitch','at_mm':old,'distance_mm':math.dist(old,at)})
    for layer in model.g['copper_layers']:
        for i in model.trees[layer].query(body.buffer(.675),predicate='intersects'):
            r=model.records[layer][int(i)]
            if r['kind']=='hole':distance=hole.distance(r['shape']);required=.275
            elif r.get('net')==net:continue
            elif r['kind']=='fill' and r.get('domain')==domain:continue
            else:distance=body.distance(r['shape']);required=.175 if r.get('domain')==domain else .625
            if distance<required-1e-9:out.append({'kind':r['kind'],'layer':layer,'uuid':r['uuid'],'pad_id':r.get('pad_id'),'net':r.get('net'),'gap_mm':distance,'required_mm':required})
        for h in model.hard[layer]:
            if net not in h['exempt'] and body.buffer(.025).intersects(h['shape']):out.append({'kind':'hard','layer':layer,'identity':{k:v for k,v in h.items() if k not in ('shape','exempt')}})
    return out
