"""Exact unmodified outer-fill polygon cache; preserve R216 diagnostic."""
from pathlib import Path
P=Path(__file__).resolve().parent
s=(P/'construct_remaining_IO3_direct_capsule_joins_r216.py').read_text()
s=s.replace('remaining-original-IO3-direct-capsule-source-nominees-r216','remaining-original-IO3-indexed-direct-source-nominees-r217')
prep=""" native_outer_fills={layer:[] for layer in ('F.Cu','B.Cu')}
 for index,q in enumerate(c['zones']):
  if q['uuid'] not in nativeids or q['net']==RAW or C.norm(q['net'])=='/LOGIC_GND':continue
  req=max(GP.G.gap(h,RAW,q['net']),float(q['clearance_mm']))+.025+.000020
  for layer in native_outer_fills:
   cache=C.poly(q['fills'].get(layer,[]))
   # Re-reading exactly the same unchanged rings must preserve each WKB.
   assert [sh.wkb for sh in cache]==[sh.wkb for sh in C.poly(q['fills'].get(layer,[]))]
   native_outer_fills[layer]+=[{'zone_index':index,'component_index':j,'uuid':q['uuid'],'req':req,'shape':sh} for j,sh in enumerate(cache)]
 native_outer_trees={l:STRtree([r['shape'] for r in rs]) for l,rs in native_outer_fills.items()}
 query_guard=max([r['req'] for rs in native_outer_fills.values() for r in rs]+[.7])+.000020
 (O/'exact-native-outer-fill-cache.pkl').write_bytes(pickle.dumps(native_outer_fills,protocol=5))
 put(O/'exact-native-outer-fill-cache-binding.json',{'model_sha256':sha(mp),'cache_sha256':sha(O/'exact-native-outer-fill-cache.pkl'),'per_layer_polygon_counts':{l:len(rs) for l,rs in native_outer_fills.items()},'every_cached_C_poly_WKB_matches_second_read':True,'predicate_query_radius_mm':query_guard,'no_buffer_operator_or_geometry_change':True})
 print('R217_EXACT_NATIVE_OUTER_FILL_CACHE_READY', {l:len(rs) for l,rs in native_outer_fills.items()},flush=True)
"""
assert ' def screen(points,width,layer):' in s
s=s.replace(' def screen(points,width,layer):',prep+' def screen(points,width,layer):')
start=s.index("  for q in c['zones']:",s.index(' def screen('));end=s.index('  for i in ht.query',start)
s=s[:start]+"""  near=sorted([int(i) for i in native_outer_trees[layer].query(body.buffer(query_guard),predicate='intersects')],key=lambda i:(native_outer_fills[layer][i]['zone_index'],native_outer_fills[layer][i]['component_index']))
  rejected=set()
  for i in near:
   r=native_outer_fills[layer][i]
   if r['uuid'] in rejected:continue
   distance=body.distance(r['shape'])
   if distance<r['req']:bad.append(('original_supply_or_foreign_fill',r['uuid'],distance,r['req']));rejected.add(r['uuid'])
"""+s[end:]
# Freeze the physical reference after its one expensive initial reconstruction.
mark=" rec,trees=F.build({**h,'zones':[]});"
assert mark in s
s=s.replace(mark," (O/'exact-source-ground-reference.pkl').write_bytes(pickle.dumps(refs,protocol=5));print('R217_DRILLED_SOURCE_REFERENCE_READY',flush=True)\n"+mark)
mark=" put(O/'checkpoint.json',{'accepted_source_nominations':accepted"
assert mark in s
s=s.replace(mark," if p['ref']=='C10025':\n  expected=json.loads((H/'sbc-power/remaining-original-IO3-direct-capsule-source-nominees-r216/checkpoint.json').read_text())['pending_direct_primitives'][0]\n  assert not options and fails[-1]['tested_capsule_paths']==expected['tested_capsule_paths'] and fails[-1]['first_failures']==expected['first_failures'], 'exact cached screen differs from preserved C10025 negative'\n  put(O/'exact-C10025-cached-vs-original-screen-equivalence.json',{'negative_path_count':expected['tested_capsule_paths'],'all_first15_path_coordinates_widths_and_first4_failures_exact':True,'old_checkpoint_sha256':sha(H/'sbc-power/remaining-original-IO3-direct-capsule-source-nominees-r216/checkpoint.json')})\n"+mark)
s=s.replace("'script_sha256':sha(__file__)","'script_sha256':sha(__file__),'effective_source_sha256':sha(O/'effective-source-used.py')")
old=" assert not O.exists();O.mkdir();mp="
assert old in s;s=s.replace(old," assert not O.exists();O.mkdir();(O/'effective-source-used.py').write_text(EFFECTIVE_SOURCE);mp=")
EFFECTIVE_SOURCE=s
exec(compile(s,str(P/'construct_remaining_IO3_direct_capsule_joins_r216.py'),'exec'))
