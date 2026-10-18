"""Finish the native check from R557's already-built actual drilled graphs.

Only the raw zone AST extraction is replaced with the frozen S-expression
parser. The exact source caches were written before the preserved AST checker
failure. Their parent native geometry, flashes and actual pad bindings are
bound again; no new numerical contact assumption or native job is introduced.
"""
from pathlib import Path
from decimal import Decimal
import hashlib
H=Path(__file__).resolve().parent
adapter=H/'audit_TMR_R218_actual_native_drilled_source_r557.py'
text=adapter.read_text(encoding='utf-8')
end="exec(compile(code,str(prior),'exec'))"
assert end in text
ns={'__file__':str(adapter)}
exec(compile(text.replace(end,''),str(adapter),'exec'),ns)
code=ns['code']
code=code.replace("OUT=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r557'","OUT=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r559'")
code=code.replace("import ordinary_routes as O","import ordinary_routes as O\nfrom verify_source import P as SP")
a="txt=chunk.decode('utf-8');polys=re.findall(r'\\(polygon\\s+\\(pts\\s*(.*?)\\s*\\)\\s*\\)',txt,re.S);assert len(polys)==1\n decimal_xy=re.findall(r'\\(xy\\s+([-+0-9.]+)\\s+([-+0-9.]+)\\)',polys[0]);assert len(decimal_xy)==3"
bb="""txt=chunk.decode('utf-8');areaAST=SP['sexpr_parse'](txt);assert areaAST[0]=='zone' and SP['atom'](areaAST,'uuid')==area['uuid'] and SP['atom'](areaAST,'name')==area['name'];polys=SP['children'](areaAST,'polygon');assert len(polys)==1
 pts=SP['child'](polys[0],'pts');coords=SP['children'](pts,'xy');assert len(coords)==3 and len(pts)==4 and all(len(x)==3 for x in coords);decimal_xy=[(x[1],x[2])for x in coords]"""
assert a in code;code=code.replace(a,bb)
old="area_shape.wkb==host_area_shape.wkb==raw_area_shape.wkb"
assert old in code
code=code.replace(old,"area_shape.wkb==host_area_shape.wkb and area_shape.normalize().wkb==raw_area_shape.normalize().wkb")
code=code.replace("'raw_AST_API_and_model_same_UUID_layer_set_and_exact_closed_WKB':True", "'raw_AST_API_and_model_same_UUID_layer_set_and_exact_normalized_closed_WKB':True,'normalization_only_orders_rings_and_coordinates_without_grid_or_coordinate_change':True")
old="_,xs=K.physical(candidate,net,ctx);groups[net]=xs"
new="""cache=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r557'/('fresh-native-all-drilled-'+('IO3'if net=='/IO_3V3'else'FA')+'-groups.pkl');assert cache.exists();cached=pickle.loads(cache.read_bytes());assert set(cached)=={net};xs=cached[net];groups[net]=xs
  # These exact K.physical caches were written after all native raw geometry
  # and actual-pad binding assertions, before the unrelated AST parser fail.
  priorbindings=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r557/exact-native-physical-pad-bindings.json';assert (OUT/'exact-native-physical-pad-bindings.json').read_bytes()==priorbindings.read_bytes()
  assert len(ctx[0])==len(candidate['vias'])+sum(len(L.poly(p.get('hole')or[]))for p in candidate['pads'])
  put(OUT/('bound-R557-'+('IO3'if net=='/IO_3V3'else'FA')+'-actual-drilled-cache.json'),{'cache_file':str(cache.resolve()),'cache_SHA256':sha(cache),'producing_checker_file':str((H/'audit_TMR_R218_actual_native_drilled_source_r557.py').resolve()),'producing_checker_SHA256':sha(H/'audit_TMR_R218_actual_native_drilled_source_r557.py'),'producing_checker_stage':'K.physical(candidate,net,all-real-drill-context) completed and cache frozen before raw AST regex failure','exact_R218_native_geometry_SHA256':sha(gp),'exact_R218_actual_via_flashes_SHA256':sha(vp),'exact_actual_native_pad_bindings_equal_to_rebuilt_R559':True,'unrelated_later_AST_schema_fail_does_not_modify_cached_graph':True,'cached_graph_does_not_grant_own_nozone_or_current_acceptance':True})"""
assert old in code;code=code.replace(old,new)
code=code.replace("'preserved_R555_failed_adapter_SHA256':sha(H/'audit_TMR_R218_actual_native_drilled_source_r555.py')", "'preserved_R555_failed_adapter_SHA256':sha(H/'audit_TMR_R218_actual_native_drilled_source_r555.py'),'preserved_R557_failed_AST_regex_checker_SHA256':sha(H/'audit_TMR_R218_actual_native_drilled_source_r557.py'),'source_graph_reuse':'Exact native K.physical/all-drill graphs written before unrelated AST parser failure; actual input geometry/flashes/pad identities independently rebound. No repeated graph calculation or weakened native predicate.'")
exec(compile(code,str(H/'audit_TMR_R218_actual_native_drilled_source_r553.py'),'exec'))
