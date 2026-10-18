"""Exact incremental reference-loss audit with a physical delta broad phase.

For every retained signal body B, (B intersect oldRef) minus newRef equals
B intersect (oldRef minus newRef). Broad-phase bounds only avoid empty
intersections; every reported loss uses the full serialized copper body.
"""
import audit_aux_exact_raw as A
import contact_layout as L
from shapely.geometry import box
from shapely.strtree import STRtree
C=A.C
def parts(shape):
 if shape.is_empty:return []
 if shape.geom_type=='Polygon':return [shape]
 return [p for q in getattr(shape,'geoms',[]) for p in parts(q)]
def audit(g,oldrefs,newrefs,ground,removed=()):
 removed=set(removed);deltas={l:oldrefs[l].difference(newrefs[l]) for l in newrefs};ps={l:parts(sh) for l,sh in deltas.items()};trees={l:STRtree(xs) for l,xs in ps.items()};rows=[];checked=0;candidates=0
 for t in g['tracks']:
  l=t['layer'];net=L.norm(t['net'])
  if t['uuid'] in removed or l not in newrefs or net==ground or g['domains_normalized'].get(net)!=g['domains_normalized'][ground]:continue
  checked+=1
  if not ps[l]:continue
  xmin=min(t['a'][0],t['b'][0])-t['w']/2;xmax=max(t['a'][0],t['b'][0])+t['w']/2;ymin=min(t['a'][1],t['b'][1])-t['w']/2;ymax=max(t['a'][1],t['b'][1])+t['w']/2
  if 'm'in t and t['m'] is not None:
   body=L.body(t);bounds=body.envelope
  else:
   bounds=box(xmin,ymin,xmax,ymax);body=None
  indices=trees[l].query(bounds.buffer(1e-9),predicate='intersects')
  if not len(indices):continue
  candidates+=1
  if body is None:body=A.shape({'kind':'segment',**t})
  loss=body.intersection(deltas[l]);original=body.intersection(oldrefs[l]).difference(newrefs[l]);assert loss.symmetric_difference(original).area<=1e-12,(t['uuid'],loss.area,original.area)
  if loss.area>1e-9:rows.append({'uuid':t['uuid'],'net':t['net'],'layer':l,'prior_source_reference_lost_mm2':loss.area})
 return rows,{'exact_delta_WKB_sha256':{l:C.sha(sh.wkb) for l,sh in deltas.items()},'exact_delta_area_mm2':{l:sh.area for l,sh in deltas.items()},'all_retained_eligible_tracks_checked':checked,'exact_body_delta_candidates':candidates,'every_candidate_direct_original_formula_compared':True,'candidate_formula_symmetric_difference_limit_mm2':1e-12,'conservative_broad_phase_only_bounds_margin_mm':1e-9,'threshold_mm2':1e-9,'algebraic_identity_no_reference_buffer_expansion':True}
