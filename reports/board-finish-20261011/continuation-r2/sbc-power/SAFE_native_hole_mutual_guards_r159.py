"""Explicit owned-only pad-hole and simultaneous foreign-zone margin cuts.

The required gaps stay fixed. An extra 20 nm is a construction reserve,
followed by literal independent clearance and all contact/reference gates.
"""
import copy,hashlib
from shapely import STRtree,set_precision
from shapely.ops import unary_union
import guarded_declared_settings_projection_r58 as GP
G=GP.G
def digest(s):return hashlib.sha256(s.wkb).hexdigest()
def change(q,cut,kind,rows):
 before=q['shape'];outline=q.get('zone_outline_shape',before)
 after=set_precision(set_precision(before,1e-6).difference(cut),1e-6);oa=set_precision(set_precision(outline,1e-6).difference(cut),1e-6)
 result={**copy.deepcopy(q),'shape':after,'zone_outline_shape':oa}
 if before.equals(after) and outline.equals(oa):return result,None
 ledger={'owned_uuid':q['uuid'],'raw_net':q['net'],'layer':q['layer'],'kind':kind,'physical_before_WKB_SHA256':digest(before),'physical_after_WKB_SHA256':digest(after),'outline_before_WKB_SHA256':digest(outline),'outline_after_WKB_SHA256':digest(oa),'physical_removed_mm2':before.difference(after).area,'physical_quantization_added_mm2':after.difference(before).area,'outline_removed_mm2':outline.difference(oa).area,'outline_quantization_added_mm2':oa.difference(outline).area,'cutters_union_WKB_SHA256':digest(cut),'cutters':rows,'no_original_native_definition_or_discrete_change':True,'fresh_all_contact_source_reference_native_current_gates_required':True}
 return result,ledger
def native_pad_hole_guards(h,zones):
 holes=[{'pad':pad,'shape':s} for pad in h['pads'] for s in G.p.base.polygons(pad.get('hole') or [])];tree=STRtree([r['shape'] for r in holes]);out=[];led=[]
 for q in zones:
  outline=q.get('zone_outline_shape',q['shape']);cuts=[];rows=[]
  for ii in tree.query(outline.buffer(.5),predicate='intersects'):
   r=holes[int(ii)];pad=r['pad']
   if pad['net']==q['net']:continue
   cut=GP.bounded_buffer(r['shape'],.275+.000020)
   if not cut.intersects(outline):continue
   cuts.append(cut);rows.append({'pad_UUID':pad['uuid'],'raw_net':pad['net'],'native_bound_hole_polygon_WKB_SHA256':digest(r['shape']),'required_hole_edge_gap_mm':.275,'construction_extra_mm':.000020,'outward_guard_WKB_SHA256':digest(cut),'native_curves_and_fresh_refill_remain_required':True})
  if not cuts:out.append(copy.deepcopy(q));continue
  nq,row=change(q,unary_union(cuts),'native_foreign_pad_hole',rows);out.append(nq)
  if row:led.append(row)
 return out,led
def simultaneous_mutual_guards(h,zones):
 # Both members are tested against the same immutable pre-cut geometry.
 # This prevents order-dependent copper ownership or clearance assignment.
 snapshot=copy.deepcopy(zones);out=[];led=[]
 for q in snapshot:
  outline=q.get('zone_outline_shape',q['shape']);cuts=[];rows=[]
  for peer in snapshot:
   if peer['uuid']==q['uuid'] or peer['net']==q['net'] or peer['layer']!=q['layer']:continue
   required=max(G.gap(h,q['net'],peer['net']),float(q.get('clearance_mm',.15)),float(peer.get('clearance_mm',.15)))+.025
   if q['shape'].distance(peer['shape'])>=required:continue
   # A true ordinary-rule collision must have an explicit constructor first.
   ordinary=required-.025
   assert q['shape'].distance(peer['shape'])>=ordinary,('actual_foreign_copper_overlap_requires_owned_reroute',q['uuid'],peer['uuid'])
   cut=GP.bounded_buffer(peer['shape'],required+.000020);cuts.append(cut);rows.append({'peer_UUID':peer['uuid'],'peer_raw_net':peer['net'],'immutable_peer_physical_WKB_SHA256':digest(peer['shape']),'immutable_pre_cut_gap_mm':q['shape'].distance(peer['shape']),'required_gap_mm':required,'construction_extra_mm':.000020,'outward_guard_WKB_SHA256':digest(cut)})
  if not cuts:out.append(copy.deepcopy(q));continue
  nq,row=change(q,unary_union(cuts),'simultaneous_NEW_mutual_planning_margin',rows);out.append(nq)
  if row:led.append(row)
 return out,led
