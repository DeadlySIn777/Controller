"""Fresh direct source proof after the explicit converter-local union cuts."""
from pathlib import Path
H=Path(__file__).resolve().parent
s=(H/'audit_IO3_R14045_TMR_new_only_source_geometry_r503.py').read_text(encoding='utf-8')
s=s.replace("M=H/'IO3-R14045-new-only-existing-barrel-TMR-materialization-r501/model.pkl'", "M=H/'IO3-TMR-bypass-only-two-role-union-individual-role-fill-scopes-r511/model.pkl'")
s=s.replace("P=H/'R155-FA-plus-IO3-TMR-individual-local-scope-witnesses-r491/model.pkl'", "P=H/'IO3-R14045-new-only-existing-barrel-TMR-materialization-r501/model.pkl'")
s=s.replace("O=H/'IO3-R14045-new-only-TMR-bypass-independent-source-geometry-r503'", "O=H/'IO3-TMR-minimal-union-independent-source-geometry-r513'")
s=s.replace("UID='a7168f4b-192a-52fe-a025-456a10753a51'", "UID='4f297f78-8d11-5be4-910e-9245f73fa249'\nADD='a7168f4b-192a-52fe-a025-456a10753a51'")
s=s.replace("assert sha(M)=='4085476528750a14f77b9d9c78a75c10914522a82932b38991f35241b7c77bd3';assert sha(P)=='c41d00e4c79e6374fbdc5a8167de451fbd4c84f8350cb41935cea3e0ae4a6abf'", "assert sha(M)=='2d10de56f7e4fb5654431d4c1ba20361235127c7dc3d958da394300bf116cc19';assert sha(P)=='4085476528750a14f77b9d9c78a75c10914522a82932b38991f35241b7c77bd3'")
s=s.replace(" assert g==pg and h==ph and q[:-1]==pq\n assert after['zones'][:-1]==before['zones']and{k:v for k,v in after.items()if k!='zones'}=={k:v for k,v in before.items()if k!='zones'}\n newq=q[-1];assert newq['uuid']==UID and L.norm(newq['net'])==NET", """ assert g==pg and h==ph
 assert{k:v for k,v in after.items()if k!='zones'}=={k:v for k,v in before.items()if k!='zones'}
 assert {z['uuid']for z in q}=={z['uuid']for z in pq}-{ADD}
 for z in q:
  oldz=next(x for x in pq if x['uuid']==z['uuid'])
  if z['uuid']!=UID:assert z==oldz
  else:
   for field in ('net','layer','priority','clearance_mm','min_thickness_mm','pad_connect_mode','island_removal_mode','thermal_gap_mm','thermal_bridge_width_mm'):assert z[field]==oldz[field]
 for z in after['zones']:
  oldz=next(x for x in before['zones']if x['uuid']==z['uuid'])
  if z['uuid']!=UID:assert z==oldz
  else:assert{k:v for k,v in z.items()if k!='fills'}=={k:v for k,v in oldz.items()if k!='fills'}
 # Analytic new-body checks conservatively use the full R501 addition:
 # the final union adds only its explicitly bound subset and local negatives.
 newq=next(x for x in pq if x['uuid']==ADD)
 operation=pickle.loads((M.parent/'only-two-member-role-and-local-fill-union-operation.pkl').read_bytes())
 finalq=next(x for x in q if x['uuid']==UID)
 assert operation['new_q']==finalq and operation['prior_new_add_q']==newq
 for role in ('shape','zone_outline_shape'):
  oldshape=lit(operation['prior_q'][role]);addition=lit(newq[role]);actual=lit(finalq[role]);assert actual.difference(oldshape).difference(addition).is_empty
  assert oldshape.difference(actual).difference(operation['explicit_negative_mask']).is_empty
 assert ADD not in {z['uuid']for z in after['zones']}
""")
s=s.replace("print('R503 source'", "print('R513 source'").replace("print('R503 geometry'", "print('R513 geometry'").replace("print('R503 receipt'", "print('R513 receipt'")
s=s.replace("'SCOPED_TMR_SOURCE_CONTACT_TRUE_GEOMETRY_NOZONE_HOST_PASS_NATIVE_UNION_CURRENT_OPEN'", "'SCOPED_TMR_MINIMAL_UNION_SOURCE_CONTACT_TRUE_GEOMETRY_NOZONE_HOST_PASS_CURRENT_NATIVE_OPEN'")
s=s.replace("'full_native_same_raw_equal_settings_overlap_normalization_current_loop_mesh_DRC':'OPEN'", "'minimal_same_all_nine_settings_union_bound':True,'full_current_loop_mesh_native_fill_DRC':'OPEN'")
exec(compile(s,str(H/'audit_IO3_TMR_minimal_union_direct_source_geometry_r513.py'),'exec'))
