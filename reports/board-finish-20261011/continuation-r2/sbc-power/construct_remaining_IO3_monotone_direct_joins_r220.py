"""Reuse exact R219 caches and prove append contacts before one final graph."""
import hashlib
from pathlib import Path
P=Path(__file__).resolve().parent
src=P/'remaining-original-IO3-indexed-direct-source-nominees-r219/effective-source-used.py'
assert hashlib.sha256(src.read_bytes()).hexdigest()=='8d307ee8740e9ec283da840e88ecfcae35ddefee2f83b908678cd22d09f8c79e'
s=src.read_text().replace('remaining-original-IO3-indexed-direct-source-nominees-r219','remaining-original-IO3-monotone-direct-source-nominees-r220')
start=s.index(" _,gg=Q.physical(c,'/LOGIC_GND')");end=s.index(' rec,trees=F.build',start)
s=s[:start]+""" refcache=H/'sbc-power/remaining-original-IO3-indexed-direct-source-nominees-r219/exact-source-ground-reference.pkl'
 refs=pickle.loads(refcache.read_bytes());(O/'exact-source-ground-reference.pkl').write_bytes(refcache.read_bytes());print('R220_REUSED_EXACT_DRILLED_SOURCE_REFERENCE',flush=True)
"""+s[end:]
start=s.index(' native_outer_fills=');end=s.index(' def screen(',start)
s=s[:start]+""" cf=H/'sbc-power/remaining-original-IO3-indexed-direct-source-nominees-r219/exact-native-outer-fill-cache.pkl'
 cb=cf.with_name('exact-native-outer-fill-cache-binding.json');proof=json.loads(cb.read_text());assert proof['model_sha256']==sha(mp) and proof['cache_sha256']==sha(cf) and proof['every_cached_C_poly_WKB_matches_second_read']
 native_outer_fills=pickle.loads(cf.read_bytes());assert {l:len(rs) for l,rs in native_outer_fills.items()}=={'F.Cu':137,'B.Cu':92}
 native_outer_trees={l:STRtree([r['shape'] for r in rs]) for l,rs in native_outer_fills.items()};query_guard=proof['predicate_query_radius_mm'];put(O/'exact-reused-cache-bindings.json',{'R214_model_sha256':sha(mp),'native_polygon_cache_file':str(cf.resolve()),'native_polygon_cache_sha256':sha(cf),'cache_binding_sha256':sha(cb),'drilled_source_ground_reference_file':str(refcache.resolve()),'drilled_source_ground_reference_sha256':sha(refcache),'no_geometry_buffer_or_predicate_change':True})
 initial_source_keys=set(prior);by_pad={r['uuid']:xs for xs in groups for r in xs if r['kind']=='pad'}
 print('R220_EXACT_CACHES_READY',flush=True)
"""+s[end:]
start=s.index('      trial=copy.deepcopy(c);nt=');end=s.index('      refgap=body.difference',start)
block=s[start:end]
nt=block[block.index('nt='):block.index(';trial[\'tracks\']')]
s=s[:start]+'      '+nt+"\n"+"""      nominal=LineString(points).buffer(width/2,quad_segs=128)
      target=unary_union(C.poly(p['layers'][layer]));actual_port=source_shapes[i]
      if nominal.intersection(target).area<.002 or nominal.intersection(actual_port).area<.002:continue
      # No IO3 item is removed or cut: a positive same-layer same-raw-net
      # contact monotonically attaches the unchanged original pad component.
      actual_src=src+by_pad[p['uuid']]+[{'kind':'track','uuid':t['uuid'],'net':RAW,'layer':layer,'shape':C.body(t),'source':t} for t in nt]
      actual=keys(actual_src)
"""+s[end:]
# The endpoint loop must retain the actual port shape, not a stale `i` from sorting.
s=s.replace("endpoints.append((list(a.coords[0]),list(bb.coords[0]),source_rows[i]['uuid'],source_rows[i]['kind']))", "endpoints.append((list(a.coords[0]),list(bb.coords[0]),source_rows[i]['uuid'],source_rows[i]['kind'],sh))")
s=s.replace('for a,end,port,kind in endpoints:', 'for a,end,port,kind,actual_port in endpoints:')
s=s.replace("target=unary_union(C.poly(p['layers'][layer]));actual_port=source_shapes[i]", "target=unary_union(C.poly(p['layers'][layer]))")
mark=" put(O/'receipt.json',{'verdict':"
assert mark in s
final=""" trial=copy.deepcopy(c);trial['tracks']+=new;finalgroups=F.graph(trial,RAW);finalsource=root(finalgroups,'R18001','2');finalkeys=keys(finalsource)
 assert not initial_source_keys-finalkeys and all(('pad',r['pad_UUID']) in finalkeys for r in accepted), 'final exact source graph rejects constructive append proof'
 (O/'actual-final-IO3-groups.pkl').write_bytes(pickle.dumps(finalgroups,protocol=5));put(O/'actual-final-source-proof.json',{'exact_R214_model_sha256':sha(mp),'final_graph_groups':len(finalgroups),'source_R18001_2_named_pad_UUIDs':len({q['uuid'] for q in finalsource if q['kind']=='pad'and q['pin']}),'prior_source_keys_lost':[list(k) for k in sorted(initial_source_keys-finalkeys)],'all_new_target_pad_UUIDs_source_joined':True,'new_tracks_only_no_IO3_old_item_removed':True,'new_holes':0,'actual_group_cache_sha256':sha(O/'actual-final-IO3-groups.pkl'),'full_foreign_contact_drill_subtracted_native_and_current_gates':'OPEN'})
"""
s=s.replace(mark,final+mark)
EFFECTIVE_SOURCE=s
exec(compile(s,str(P/'construct_remaining_IO3_direct_capsule_joins_r216.py'),'exec'))
