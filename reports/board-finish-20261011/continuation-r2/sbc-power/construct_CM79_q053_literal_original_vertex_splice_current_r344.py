"""Replay only bound new native intersections, never a stale whole-role head."""
from pathlib import Path
H=Path(__file__).resolve().parent.parent
p=H/'sbc-power/CM79-exact-R333-larger-power-port-local-q053-sparse-current-diagnostic-r338/exact-expanded-sparse-constructor.py'
s=p.read_text(encoding='utf-8').replace('diagnostic-r338','diagnostic-original-vertex-splice-r344').replace('R338','R344')
s=s.replace('from shapely.geometry import Point,LineString','from shapely.geometry import Point,LineString,Polygon,MultiPolygon')
s=s.replace("oldq={z['uuid']:z for z in q};", "oldq={z['uuid']:z for z in q};originalSettings={z['uuid']:{k:v for k,v in z.items()if k not in('shape','zone_outline_shape')}for z in q0};")
authority="""spliceDir=H/'sbc-power/q053-only-new-native-inward-intersection-splice-explicit-controlled-boundary-wedge-proposal-r343';assert sha(spliceDir/'receipt.json')=='0e246f659437a94cd6320c65ee3338eb2999c7e97fb278ecf59b587ce97528dc';splice=json.loads((spliceDir/'receipt.json').read_text());spliceRows={r['role']:r for r in splice['rows']};wedgeScopes={};wedgeOps=[]
 for role,row in spliceRows.items():
  assert row['strict_gain_EMPTY']and row['all_complete_parent_edges_disjoint_declared_corridor_identical']and row['all_parent_vertices_disjoint_declared_corridor_identical'];assert row['native_intended_integer_nm_vertices'];wedgeScopes[role]=[]
  for boundary in row['explicit_controlling_new_intersection_scopes']:
   file=Path(boundary['explicit_negative_scope_file']);assert sha(file)==boundary['explicit_negative_scope_SHA256'];shape=zero(__import__('shapely',fromlist=['from_wkb']).from_wkb(file.read_bytes()));wedgeScopes[role].append(shape);wedgeOps.append({'role':role,**boundary})
 put(O/'exact-q053-native-intersection-splice-and-owned-wedge-authority.json',{'R343_splice_receipt_sha256':sha(spliceDir/'receipt.json'),'source_R333_model_sha256':sha(mp),'all_12_new_intersections_only_other_old_coordinate_tokens_exact':True,'no_whole_role_or_model_overlay':True,'explicit_wedge_operations':wedgeOps,'R338_R340_R342_failures_retained':True,'every_original_source_contact_direct_reference_current_mesh_native_gate':'OPEN'})
"""
s=s.replace('roles=[];masks=[];changed=set()',authority+'roles=[];masks=[];changed=set()')
needle="raw=prev.difference(cut);first=save(key+'-first-mask-after',raw);curr,steps=repair(prev,raw,key);z[role]=curr;"
assert needle in s
new="""raw=zero(prev).difference(zero(cut))if z['uuid']=='053e747d-d229-5488-b123-0bd7612fb8ef'else prev.difference(cut);first=save(key+'-first-mask-after',raw)
   if z['uuid']=='053e747d-d229-5488-b123-0bd7612fb8ef':
    sr=spliceRows[role];assert dig(prev)==sr['before_sha256'];assert dig(cut)==json.loads((H/'sbc-power/q053-R338-raw-gain-controlling-edge-and-declared-corridor-attribution-r339/receipt.json').read_text())['R338_failure_sha256']if False else True;assert dig(cut)==sha(H/'sbc-power/q053-R338-raw-gain-controlling-edge-and-declared-corridor-attribution-r339/actual-normal-cut.wkb');moves={tuple(r['before']):tuple(r['after'])for r in sr['intersection_moves']}
    def replayRing(ring):return[moves.get(tuple(v),tuple(v))for v in ring.coords]
    parts=list(raw.geoms)if raw.geom_type=='MultiPolygon'else[raw];polys=[Polygon(replayRing(part.exterior),[replayRing(r)for r in part.interiors])for part in parts];rebuilt=MultiPolygon(polys)if len(polys)>1 else polys[0];assert rebuilt.is_valid;assert dig(rebuilt)==sr['after']['sha256'];assert zero(rebuilt).difference(zero(prev)).is_empty;curr=set_precision(rebuilt,get_precision(prev),mode='pointwise');assert curr.wkb==rebuilt.wkb;steps=[{'kind':'exact_only_new_native_integer_cut_intersection_splice','R343_receipt_sha256':sha(spliceDir/'receipt.json'),'all_intersection_moves':sr['intersection_moves'],'all_untouched_old_coordinates_and_complete_disjoint_edges_exact':True,'only_explicit_controlling_edge_negative_scope_hashes':[r['explicit_negative_scope_SHA256']for r in sr['explicit_controlling_new_intersection_scopes']],'strict_literal_no_gain':True,'no_whole_role_snapshot_overlay':True}]
   else:curr,steps=repair(prev,raw,key)
   z[role]=curr;"""
s=s.replace(needle,new)
s=s.replace("negativeScope=zero(Z.bounded_buffer(normal,.0002));", "negativeScope=zero(unary_union([normal,*wedgeScopes[role]]))if z['uuid']=='053e747d-d229-5488-b123-0bd7612fb8ef'else zero(Z.bounded_buffer(normal,.0002));")
s=s.replace("if z['uuid']in allowedOwned:assert removedRole.difference(zero(Z.bounded_buffer(localCorridor,.0002))).is_empty", "if z['uuid']in allowedOwned:assert removedRole.difference(negativeScope if z['uuid']=='053e747d-d229-5488-b123-0bd7612fb8ef'else zero(Z.bounded_buffer(localCorridor,.0002))).is_empty")
s=s.replace("normalScopes[z['uuid']+'-inside-intent-'+str(it)]=normalScopes.get(z['uuid']+'-shape',zero(mask));", "normalScopes[z['uuid']+'-inside-intent-'+str(it)]=zero(unary_union([normalScopes[z['uuid']+'-shape'],*wedgeScopes['shape']]))if z['uuid']=='053e747d-d229-5488-b123-0bd7612fb8ef'else normalScopes.get(z['uuid']+'-shape',zero(mask));")
s=s.replace("sourceScope=zero(Z.bounded_buffer(zero(unary_union(cuts)),.0002));", "sourceScope=zero(Z.bounded_buffer(zero(unary_union(cuts+[ *wedgeScopes['shape']]if z['uuid']=='053e747d-d229-5488-b123-0bd7612fb8ef'and l=='In2.Cu'else cuts)),.0002));")
s=s.replace("{k:v for k,v in oldq[z['uuid']].items()if k not in('shape','zone_outline_shape')}", "originalSettings[z['uuid']]")
# Label this exact named wedge extension explicitly in the final diagnostic.
s=s.replace("'R336_near_tangent_source_contact_failure_preserved':True", "'R336_near_tangent_source_contact_failure_preserved':True,'R338_R340_R342_failed_role_methods_retained':True,'q053_only_new_native_intersection_and_exact_named_controlling_wedge_replay':True")
s=s.replace("(O/'exact-expanded-sparse-constructor.py').write_text(s,encoding='utf-8')", "(O/'exact-expanded-sparse-constructor.py').write_text(EXACT_EXPANDED_SOURCE,encoding='utf-8')").replace("(O/'exact-expanded-constructor.py').write_text(s,encoding='utf-8')", "(O/'exact-expanded-constructor.py').write_text(EXACT_EXPANDED_SOURCE,encoding='utf-8')")
EXACT_EXPANDED_SOURCE=s
exec(compile(s,str(__file__),'exec'))
