"""Bind each extra actual generated-record loss to its exact OLD edge.

No area waiver: preserve every raw witness, require exact containment within
named outward edge envelopes, then fresh source/contact/reference gates.
"""
from pathlib import Path
import ast
H=Path(__file__).resolve().parent
p=H/'construct_four_unions_named_owned_record_edge_negatives_r623.py'
tree=ast.parse(p.read_text(encoding='utf-8'));tree.body.pop();ns={'__file__':str(p)};exec(compile(tree,str(p),'exec'),ns);s=ns['s']
s=s.replace('R543-four-unions-named-new-owned-current-edge-negatives-r623','R543-four-unions-complete-named-generated-record-edge-scopes-r625')
old="   assert gain.is_empty and outside.is_empty,('current fill gain/nonlocal negative',i,member['uuid'],ds(gain),ds(outside))"
new="""   extraedge=[]
   if not outside.is_empty:
    wf=OUT/f'cluster-{i}-{member["uuid"]}-RAW-extra-actual-record-loss-outside-primary-scopes.wkb';wf.write_bytes(outside.wkb);alledges=[(ri,LineString([a,d]))for ri,record in enumerate(L.poly(rs))for ring in[record.exterior]+list(record.interiors)for a,d in zip(list(ring.coords),list(ring.coords)[1:])if a!=d]
    from physical_reference_losses_r3_zero_r208 import parts
    chunks=list(outside.geoms)if hasattr(outside,'geoms')else[outside]
    selected={}
    for witness in chunks:
     for ri,e in sorted(alledges,key=lambda r:r[1].distance(witness))[:8]:
      if e.distance(witness)<=.000002:selected[ri,tuple(e.coords)]=e
    for ei,((ri,coords),edge)in enumerate(selected.items()):
     em=zero(Z.bounded_buffer(edge,.0002));ef=OUT/f'cluster-{i}-{member["uuid"]}-extra-record-{ri}-named-OLD-generated-edge-{ei}.wkb';ef.write_bytes(em.wkb);scope=unary_union([scope,em]);extraedge.append({'exact_OLD_generated_record_index':ri,'exact_OLD_edge_coordinates_mm':list(coords),'exact_OLD_record_WKB_SHA256':hs(L.poly([rs[ri]])[0]),'explicit200nm_boundary_withdrawal_scope_file':str(ef.resolve()),'scope_SHA256':sha(ef),'scope_nomination_only_no_additional_geometry_operation':True,'parent_zone_is_verified_NEW_owned_not_original_native':True})
    residual=removed.difference(scope);rf=OUT/f'cluster-{i}-{member["uuid"]}-actual-loss-outside-COMPLETE-exact-named-owned-edge-scopes.wkb';rf.write_bytes(residual.wkb);assert residual.is_empty,('actual record loss not bound to named NEW-owned edges',i,member['uuid'],ds(residual));outside=residual
   assert gain.is_empty and outside.is_empty,('current fill gain/unbound actual negative',i,member['uuid'],ds(gain),ds(outside))"""
assert old in s;s=s.replace(old,new)
s=s.replace("'immutable_per_record_proof':proof,'literal_gain_EMPTY'", "'immutable_per_record_proof':proof,'separately_nominated_extra_exact_OLD_record_edge_withdrawals':extraedge,'literal_gain_EMPTY'")
s=s.replace("print('R623'","print('R625'")
exec(compile(s,str(Path(__file__)),'exec'))
