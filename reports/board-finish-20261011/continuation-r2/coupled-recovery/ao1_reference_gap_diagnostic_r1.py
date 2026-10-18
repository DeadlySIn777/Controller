"""Classify exact missing reference without assigning speculative fill credit."""
from pathlib import Path
from shapely.geometry import Point
from shapely.ops import unary_union
import audit_ao1_positive_operation_r4 as Q
A,P,G,S,C=Q.A,Q.P,Q.G,Q.S,Q.C

def diagnose(base,final,parsed,removed,source_masks,refs,inventory,outdir):
    gaps=Q.zone_gaps(inventory);signals={z['net']:z for z in parsed.values() if z['kind']=='via' and z['net'] in (Q.VREF,Q.SDI)}
    old=[v for v in base.g['vias'] if v['uuid'] in removed]
    rows=[]
    for uid,z in parsed.items():
        if z['kind']!='segment':continue
        plane='In1.Cu' if z['layer']=='F.Cu' else 'In4.Cu';v=signals[z['net']]
        ownbase=Point(v['at']).buffer(v['d']/2,resolution=128)
        source_zones=[r for r in base.records[plane] if r['kind']=='fill' and r['net']==Q.COM and r['shape'].distance(ownbase)<=max(.15,gaps[r['uuid']])+.025]
        local=max([.15]+[gaps[r['uuid']] for r in source_zones]);own=Point(v['at']).buffer(v['d']/2+local+.025,resolution=128)
        uncovered=A.shape(z).difference(own).difference(refs[z['layer']])
        if uncovered.area<=1e-9:continue
        # Neighbor new transition voids remain real physical obligations even
        # when they overlap the discarded barrel's cached clearance region.
        othercuts=[]
        for q in parsed.values():
            if q['kind']!='via' or q['uuid']==v['uuid']:continue
            radius=q['drill']/2 if q['net']==Q.COM else q['d']/2+local+.025
            othercuts.append(Point(q['at']).buffer(radius,resolution=128))
        neighbors=unary_union(othercuts)
        stale=[];stalemeta=[]
        for q in old:
            if plane not in source_masks.get(q['uuid'],set()):continue
            radius=q['d']/2+local+.025;circle=Point(q['x'],q['y']).buffer(radius,resolution=128);stale.append(circle)
            stalemeta.append({'withdrawn_uuid':q['uuid'],'exact_source_position_mm':[q['x'],q['y']],'exact_source_diameter_mm':q['d'],'exact_actual_flash_layer':plane,'clearance_region_nomination_radius_mm':radius})
        stale=unary_union(stale)
        retained=[]
        for r in final.records[plane]:
            if r['kind']=='hole':retained.append(r['shape'])
            elif r['kind'] in ('pad','track','via') and r.get('net')!=Q.COM and r['uuid'] not in parsed:
                required=max(local,.15 if r.get('domain')==base.domains[Q.COM] else .6)
                retained.append(r['shape'].buffer(required+.025,resolution=128))
        retained=unary_union(retained)
        path=Path(outdir)/(uid+'-reference-gap.wkb');path.write_bytes(uncovered.wkb)
        rows.append({'uuid':uid,'net':z['net'],'layer':z['layer'],'reference_plane':plane,'uncovered_full_body_mm2':uncovered.area,'uncovered_bounds_mm':list(uncovered.bounds),'exact_gap_WKB_path':str(path.resolve()),'exact_gap_WKB_sha256':C.sha(uncovered.wkb),'within_withdrawn_barrel_clearance_region_mm2':uncovered.intersection(stale).area,'outside_withdrawn_barrel_region_mm2':uncovered.difference(stale).area,'actual_new_neighbor_transition_or_return_drill_overlap_mm2':uncovered.intersection(neighbors).area,'retained_existing_foreign_copper_or_physical_hole_clearance_overlap_mm2':uncovered.intersection(retained).area,'withdrawn_native_barrel_geometry':stalemeta,'stale_fill_healing_credit':False,'fresh_native_refill_export_required':True})
    return rows
