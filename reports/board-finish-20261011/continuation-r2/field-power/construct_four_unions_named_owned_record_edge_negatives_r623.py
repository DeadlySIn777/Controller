"""Declare extra negatives only on exact affected NEW-owned record edges.

R621's private-primary-scope failure remains frozen. Each proposed extra
negative is tied to its old generated record edge; no original native record
or unrelated role is touched. Fresh contact/reference qualification required.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'construct_R543_only_four_inward_same_settings_unions_r619.py').read_text(encoding='utf-8')
s=s.replace('R543-only-four-current-inward-same-nine-settings-unions-r619','R543-four-unions-named-new-owned-current-edge-negatives-r623')
s=s.replace('from shapely.geometry import Polygon','from shapely.geometry import Polygon,LineString')
old="assert z.get('prospective_not_native')and set(z['fills'])=={layer}"
new="assert member['uuid']not in {x['uuid']for x in h['zones']}and z['net']==member['net']and set(z['fills'])=={layer},('exact_declared_owned_member_identity',member['uuid']);assert all(z[k]==v for k,v in profile.items()if k in z)"
assert old in s;s=s.replace(old,new)
old="     mask=from_wkb(Path(r['reserve_file']).read_bytes());assert mask.difference(unary_union([zero(Z.bounded_buffer(loss,.0002))])).is_empty,('nonlocal current record reserve',i,member['uuid'],r)\n     scope=unary_union([scope,mask])"
new="""     mask=from_wkb(Path(r['reserve_file']).read_bytes());gainw=from_wkb(Path(r['raw_gain_file']).read_bytes());record=L.poly([rs[step['record']]])[0];edges=[LineString([a,d])for ring in[record.exterior]+list(record.interiors)for a,d in zip(list(ring.coords),list(ring.coords)[1:])if a!=d];nearest=sorted(edges,key=lambda e:e.distance(gainw))[:8];authority=[];edge_rows=[]
     for ei,e in enumerate(nearest):
      if e.distance(gainw)>.000002:continue
      em=zero(Z.bounded_buffer(e,.0002));authority.append(em);ef=OUT/f'cluster-{i}-{member["uuid"]}-record-{step["record"]}-reserve-{r["iteration"]}-named-old-edge-{ei}.wkb';ef.write_bytes(em.wkb);edge_rows.append({'exact_OLD_generated_record_edge_mm':list(e.coords),'exact_OLD_parent_record_WKB_SHA256':hs(record),'explicit200nm_edge_authority_file':str(ef.resolve()),'explicit200nm_edge_authority_SHA256':sha(ef),'scope_is_named_existing_generated_member_edge_not_original_native_Cu':True})
     es=unary_union(authority);edge_outside=mask.difference(es);wf=OUT/f'cluster-{i}-{member["uuid"]}-record-{step["record"]}-reserve-{r["iteration"]}-outside-exact-named-owned-edge-authority.wkb';wf.write_bytes(edge_outside.wkb);assert edge_outside.is_empty,('record negative not bound to exact old GENERATED edge',i,member['uuid'],ds(edge_outside))
     r['separately_nominated_OLD_generated_record_edges']=edge_rows;r['literal_negative_outside_exact_named_edge_authority_EMPTY']=True;r['private_primary_role_wedge_scope_R621_FAIL_preserved']=True
     scope=unary_union([scope,es])"""
assert old in s;s=s.replace(old,new)
s=s.replace("'current_records_concatenated_only_after_local_negative_replay_no_global_union':True", "'current_records_concatenated_only_after_local_negative_replay_no_global_union':True,'extra_current_negatives_are_separately_bound_NEW_owned_record_edge_nominations':True")
s=s.replace("print('R619'","print('R623'")
exec(compile(s,str(Path(__file__)),'exec'))
