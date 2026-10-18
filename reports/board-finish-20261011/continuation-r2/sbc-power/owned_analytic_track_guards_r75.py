"""Ledgered exact-centerline round-cap correction for owned new planes.

Call before integer-grid union and final contact auditing. This helper never
edits original native zone definitions or discrete copper. Its output remains
prospective until actual source, retained contact and native gates pass.
"""
import copy,hashlib
from shapely import STRtree,set_precision
from shapely.geometry import LineString
from shapely.ops import unary_union
import guarded_declared_settings_projection_r58 as GP
G=GP.G
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def normalize_owned_track_guards(h,zones):
    records={l:[] for l in h['copper_layers']}
    for t in h['tracks']:
        records[t['layer']].append({'track':t,'centerline':LineString([t['a'],t['b']])})
    trees={l:STRtree([r['centerline'] for r in rs]) for l,rs in records.items()}
    out=[];ledger=[];geometry={}
    for q in zones:
        before=q['shape'];outline=q.get('zone_outline_shape',before);cuts=[];rows=[]
        for ii in trees[q['layer']].query(outline.buffer(3),predicate='intersects'):
            r=records[q['layer']][int(ii)];t=r['track']
            if t['net']==q['net']:continue
            clear=max(G.gap(h,q['net'],t['net']),float(q.get('clearance_mm',.15)))+.025
            radius=t['w']/2+clear;cut=GP.bounded_buffer(r['centerline'],radius)
            if cut.intersects(outline):
                cuts.append(cut);rows.append({'track_uuid':t['uuid'],'raw_net':t['net'],'a':t['a'],'b':t['b'],'width_mm':t['w'],'analytic_centerline_radius_mm':radius,'required_Cu_guard_mm':clear,'outward256edge_cutter_WKB_SHA256':digest(cut)})
        if not cuts:out.append(copy.deepcopy(q));continue
        cutter=unary_union(cuts);after=set_precision(set_precision(before,1e-6).difference(cutter),1e-6);oa=set_precision(set_precision(outline,1e-6).difference(cutter),1e-6)
        if before.equals(after) and outline.equals(oa):out.append(copy.deepcopy(q));continue
        out.append({**copy.deepcopy(q),'shape':after,'zone_outline_shape':oa})
        geometry[q['uuid']]={'physical-before':before,'physical-after':after,'outline-before':outline,'outline-after':oa,'track-cutter-union':cutter}
        ledger.append({'zone_uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'physical_before_WKB_SHA256':digest(before),'physical_after_WKB_SHA256':digest(after),'outline_before_WKB_SHA256':digest(outline),'outline_after_WKB_SHA256':digest(oa),'physical_removed_area_mm2':before.difference(after).area,'physical_quantization_added_area_mm2':after.difference(before).area,'outline_removed_area_mm2':outline.difference(oa).area,'outline_quantization_added_area_mm2':oa.difference(outline).area,'cutters_union_WKB_SHA256':digest(cutter),'cutters':rows,'all_original_outline_discrete_and_prior_contact_obligations_retained':True,'fresh_source_contact_native_current_gate_required':True})
    return out,ledger,geometry
