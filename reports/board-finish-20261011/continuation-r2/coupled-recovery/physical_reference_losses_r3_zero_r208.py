"""Exact reference delta audit using every locally intersecting delta piece.

For a complete disjoint polygon decomposition D of oldRef minus newRef,
B intersect D equals B intersect union(all pieces meeting a conservative
bound on B). Every omitted piece is disjoint from B. No reference geometry,
loss threshold, full-body shape or source-root/contact gate is changed.
The original full-plane formula is algebraically B intersect D; r1 remains
preserved with its expensive per-candidate numerical formula comparisons.
"""
import audit_aux_exact_raw as A
import contact_layout as L
from shapely.geometry import box
from shapely.ops import unary_union
from shapely.strtree import STRtree
C=A.C
def parts(shape):
 if shape.is_empty:return []
 if shape.geom_type=='Polygon':return [shape]
 return [p for q in getattr(shape,'geoms',[]) for p in parts(q)]
def audit(g,oldrefs,newrefs,ground,removed=()):
 removed=set(removed);deltas={l:oldrefs[l].difference(newrefs[l]) for l in newrefs};ps={l:parts(sh) for l,sh in deltas.items()};trees={l:STRtree(xs) for l,xs in ps.items()};rows=[];checked=0;candidates=0;piecechecks=0
 for t in g['tracks']:
  l=t['layer'];net=L.norm(t['net'])
  if t['uuid'] in removed or l not in newrefs or net==ground or g['domains_normalized'].get(net)!=g['domains_normalized'][ground]:continue
  checked+=1
  if not ps[l]:continue
  if t.get('m') is not None:body=L.body(t);bounds=body.envelope
  else:
   bounds=box(min(t['a'][0],t['b'][0])-t['w']/2,min(t['a'][1],t['b'][1])-t['w']/2,max(t['a'][0],t['b'][0])+t['w']/2,max(t['a'][1],t['b'][1])+t['w']/2);body=None
  indices=trees[l].query(bounds.buffer(1e-9),predicate='intersects')
  if not len(indices):continue
  candidates+=1;piecechecks+=len(indices)
  if body is None:body=A.shape({'kind':'segment',**t})
  selected=[ps[l][int(i)] for i in indices];loss=body.intersection(unary_union(selected))
  if not loss.is_empty:rows.append({'uuid':t['uuid'],'net':t['net'],'layer':l,'prior_source_reference_lost_mm2':loss.area,'full_body_exact_local_delta_piece_count':len(indices),'exact_local_delta_WKB_sha256':C.sha(unary_union(selected).wkb)})
 return rows,{'exact_delta_WKB_sha256':{l:C.sha(sh.wkb) for l,sh in deltas.items()},'exact_delta_area_mm2':{l:sh.area for l,sh in deltas.items()},'complete_delta_polygon_piece_count':{l:len(xs) for l,xs in ps.items()},'all_retained_eligible_tracks_checked':checked,'exact_body_delta_candidates':candidates,'exact_delta_pieces_checked':piecechecks,'exact_selected_piece_intersection':True,'excluded_pieces_provably_disjoint_from_conservative_full_body_bounds':True,'conservative_broad_phase_only_bounds_margin_mm':1e-9,'threshold_mm2':0,'every_nonempty_intersection_reported':True,'algebraic_identity_no_reference_buffer_expansion':True,'preserved_r1_runtime_original_formula_oracle_not_repeated':True}
