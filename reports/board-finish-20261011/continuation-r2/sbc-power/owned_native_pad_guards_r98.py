"""Ledgered outward pad-polygon cuts with explicit additional 20 nm reserve for owned NEW power-zone proposals.

Call after complete discrete/pose composition and before final integer union.
Pad polygons come from the exact native-bound geometry and explicit moved-pad
contracts. True native curve/refill/clearance remains a separate native gate.
No original zone definition, pad, copper object, or source entity is edited.
"""
import copy,hashlib
from shapely import STRtree,set_precision
from shapely.ops import unary_union
import guarded_declared_settings_projection_r58 as GP
G=GP.G
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def normalize_owned_pad_guards(h,zones):
    records={l:[] for l in h['copper_layers']}
    for pad in h['pads']:
        for layer,rs in pad['layers'].items():
            for piece in G.p.base.polygons(rs):records[layer].append({'pad':pad,'shape':piece})
    trees={l:STRtree([r['shape'] for r in rows]) for l,rows in records.items()}
    output=[];ledger=[];geometry={}
    for q in zones:
        before=q['shape'];outline=q.get('zone_outline_shape',before);cutters=[];rows=[]
        for ii in trees[q['layer']].query(outline.buffer(1.5),predicate='intersects'):
            r=records[q['layer']][int(ii)];pad=r['pad']
            if pad['net']==q['net']:continue
            clear=max(G.gap(h,q['net'],pad['net']),float(q.get('clearance_mm',.15)))+.025
            cutter=GP.bounded_buffer(r['shape'],clear+.000020)
            if cutter.intersects(outline):
                cutters.append(cutter);rows.append({'pad_UUID':pad['uuid'],'ref':pad['ref'],'pin':pad['num'],'actual_raw_net':pad['net'],'actual_native_bound_pad_polygon_WKB_sha256':digest(r['shape']),'required_Cu_guard_mm':clear,'explicit_extra_outward_pad_construction_reserve_mm':.000020,'independent_required_gap_unchanged':True,'outward256edge_guard_WKB_sha256':digest(cutter)})
        if not cutters:output.append(copy.deepcopy(q));continue
        cutter=unary_union(cutters);after=set_precision(set_precision(before,1e-6).difference(cutter),1e-6);oa=set_precision(set_precision(outline,1e-6).difference(cutter),1e-6)
        if before.equals(after) and outline.equals(oa):output.append(copy.deepcopy(q));continue
        output.append({**copy.deepcopy(q),'shape':after,'zone_outline_shape':oa})
        geometry[q['uuid']]={'physical-before':before,'physical-after':after,'outline-before':outline,'outline-after':oa,'pad-cutter-union':cutter}
        ledger.append({'zone_uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'physical_before_WKB_SHA256':digest(before),'physical_after_WKB_SHA256':digest(after),'outline_before_WKB_SHA256':digest(outline),'outline_after_WKB_SHA256':digest(oa),'physical_removed_area_mm2':before.difference(after).area,'physical_quantization_added_area_mm2':after.difference(before).area,'outline_removed_area_mm2':outline.difference(oa).area,'outline_quantization_added_area_mm2':oa.difference(outline).area,'cutters_union_WKB_SHA256':digest(cutter),'cutters':rows,'all_original_outline_discrete_and_prior_contact_obligations_retained':True,'fresh_source_contact_native_current_gate_required':True})
    return output,ledger,geometry
