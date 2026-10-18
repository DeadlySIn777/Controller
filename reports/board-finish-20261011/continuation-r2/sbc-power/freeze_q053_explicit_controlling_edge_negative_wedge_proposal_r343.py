"""Explicit owned controlling-edge proposal only; no source/current head."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/q053-only-new-native-inward-intersection-splice-proposal-r342/exact-expanded-owned-intersection-splice-proposal.py'
s=p.read_text(encoding='utf-8').replace('proposal-r342','explicit-controlled-boundary-wedge-proposal-r343').replace('R342','R343')
s=s.replace("assert outside.is_empty,('owned negative wedge outside declared local corridor',role,sm(outside));", "# Outside wedges stay explicit; this is a proposal only, never a locality waiver.\n  ")
s=s.replace("row={'role':role", "wedgeRows=[]\n  for rr in rings(raw):\n   for k,vv in enumerate(rr[:-1]):\n    vv=tuple(vv)\n    if vv not in moves:continue\n    aa=tuple(rr[k-1]if k else rr[-2]);zz=tuple(rr[k+1]);mm=moves[vv];triangles=[Polygon([aa,vv,mm]),Polygon([vv,zz,mm])];scope=lit(N.bounded_buffer(__import__('shapely.ops',fromlist=['unary_union']).unary_union(triangles),.0001));fn=O/(role+'-controlled-new-intersection-'+str(len(wedgeRows))+'-explicit-negative-scope.wkb');save(fn,scope);wedgeRows.append({'raw_new_cut_intersection':vv,'native_inward_replacement':mm,'unchanged_preceding_vertex':aa,'unchanged_following_vertex':zz,'exact_two_local_wedge_stats':[sm(t)for t in triangles],'explicit_negative_scope':sm(scope),'explicit_negative_scope_file':str(fn.resolve()),'explicit_negative_scope_SHA256':hashlib.sha256(fn.read_bytes()).hexdigest(),'scope_outside_prior_declared_corridor':sm(scope.difference(local)),'no_original_coordinate_token_changed':True})\n  row={'explicit_controlling_new_intersection_scopes':wedgeRows,'role':role")
s=s.replace('Q053_ONLY_NEW_NATIVE_INTERSECTION_SPLICE_STRICT_NEGATIVE_LOCAL_PROPOSAL_ONLY_NO_MODEL','Q053_ONLY_NEW_NATIVE_INTERSECTION_SPLICE_EXPLICIT_BOUNDARY_WEDGE_SCOPE_EXTENSION_PROPOSAL_ONLY_NO_MODEL')
EXACT_EXPANDED_SOURCE=s
exec(compile(s,str(__file__),'exec'))
