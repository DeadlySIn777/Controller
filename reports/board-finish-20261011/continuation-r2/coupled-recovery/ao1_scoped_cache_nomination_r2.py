"""Exploratory geometry only; never expands an accepted native reference."""
from shapely.geometry import Point,Polygon
from shapely.ops import unary_union
import audit_ao1_positive_operation_r2 as Q
A,P,G,S,C=Q.A,Q.P,Q.G,Q.S,Q.C

def provisional(initial,refs,native,inventory):
    uid='2b635368-5867-4b98-b422-f0fc9cd7464c';old=G.parse(uid,inventory[4][uid],{})
    assert old['kind']=='via' and old['net']==Q.SDI and old['d']==.6 and old['drill']==.3
    gaps=Q.zone_gaps(inventory);out={};rows=[]
    for signal,plane in (('F.Cu','In1.Cu'),('B.Cu','In4.Cu'),('In3.Cu','In4.Cu')):
        zones=[z for z in native['zones'] if S.norm(z['net'])==Q.COM and plane in z['layers']]
        outlines=unary_union([Polygon(rings[0],rings[1:]) for z in zones for rings in z['outline']]);local=max([.15]+[gaps[z['uuid']] for z in zones])
        circle=Point(old['at']).buffer(old['d']/2+local+.025,resolution=128)
        scope=circle.intersection(outlines.buffer(-.01));cutters=[];blockers=[]
        for r in initial.records[plane]:
            if not r['shape'].intersects(circle.buffer(.7)):continue
            if r['kind']=='hole':region=r['shape']
            elif r.get('net')==Q.COM:continue
            else:
                # Other actual plane fill and flashed copper remain physical
                # boundaries. No neighboring existing or planned void credit.
                clearance=max(local,.15 if r.get('domain')==initial.domains[Q.COM] else .6)
                region=r['shape'].buffer(clearance+.025,resolution=128)
            if region.intersects(scope):cutters.append(region);blockers.append({'uuid':r['uuid'],'kind':r['kind'],'net':r.get('net')})
        for hard in initial.hard[plane]:
            if Q.COM not in hard['exempt']:cutters.append(hard['shape'].buffer(.025))
        scope=scope.difference(unary_union(cutters))
        out[signal]=refs[signal].union(scope)
        rows.append({'signal_layer':signal,'reference_plane':plane,'withdrawn_exact_uuid':uid,'withdrawn_exact_at_mm':old['at'],'withdrawn_exact_diameter_mm':old['d'],'native_zone_local_clearance_mm':local,'provisional_scope_mm2':scope.area,'scope_bounds_mm':list(scope.bounds) if not scope.is_empty else [],'scope_WKB_sha256':C.sha(scope.wkb),'actual_foreign_plane_boundaries_retained':blockers,'zone_outline_uuids':sorted(z['uuid'] for z in zones),'nomination_only':True,'accepted_reference_credit':False,'fresh_native_refill_export_gate':'OPEN'})
    return out,rows
