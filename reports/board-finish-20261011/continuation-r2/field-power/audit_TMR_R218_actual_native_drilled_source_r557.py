"""R218 independent graph and raw PCB integer TMR-area binding.

R553/R555 failed schema assumptions remain unchanged. This successor converts
only the native export's omitted empty hole-array and pins the exact raw AST
triangle, UUID, layer set and closed-set geometry before no-zone predicates.
"""
from pathlib import Path
from decimal import Decimal
H=Path(__file__).resolve().parent
prior=H/'audit_TMR_R218_actual_native_drilled_source_r553.py'
code=prior.read_text(encoding='utf-8')
code=code.replace("OUT=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r553'","OUT=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r557'")
old="assert area['outline']==ha['outline']and area['layers']==ha['layers'];area_shape=unary_union(L.poly(area['outline']))"
new="""assert area['layers']==ha['layers'] and area['uuid']==ha['uuid']
 # Read the actual serialized rule-area AST, not merely a nominal rectangle
 # or API bounding box. No points are omitted, averaged or rounded.
 pcb=(N/'copy/board.kicad_pcb').read_bytes();needle=('(uuid "'+area['uuid']+'")').encode();at=pcb.index(needle);begin=pcb.rfind(b'\\n\\t(zone',0,at)+1;end=re.search(rb'\\r?\\n\\t\\)\\r?\\n',pcb[at:]);assert begin>0 and end;chunk=pcb[begin:at+end.end()];assert chunk.count(needle)==1 and b'(name "TMR4WI_KEEPOUT_U14619")'in chunk
 txt=chunk.decode('utf-8');polys=re.findall(r'\\(polygon\\s+\\(pts\\s*(.*?)\\s*\\)\\s*\\)',txt,re.S);assert len(polys)==1
 decimal_xy=re.findall(r'\\(xy\\s+([-+0-9.]+)\\s+([-+0-9.]+)\\)',polys[0]);assert len(decimal_xy)==3
 def iu(v):
  n=Decimal(str(v))*Decimal(1000000);assert n==n.to_integral_value();return int(n)
 rawring=[[iu(x),iu(y)]for x,y in decimal_xy];nativering=[[iu(x),iu(y)]for x,y in area['outline'][0][0]];hostring=[[iu(x),iu(y)]for x,y in ha['outline'][0][0]]
 assert rawring==nativering==hostring==[[348198000,130350000],[323998000,130350000],[323998000,118650000]]
 rawlayers=re.findall(r'"([^"\\n]+)"',re.search(r'\\(layers\\s+([^)]*)\\)',txt).group(1));assert set(rawlayers)==set(area['layers'])==set(ha['layers'])
 area_shape=unary_union(L.poly(O.polys(area['outline'])));host_area_shape=unary_union(L.poly(ha['outline']));raw_area_shape=Polygon([(x/1e6,y/1e6)for x,y in rawring]);assert area_shape.wkb==host_area_shape.wkb==raw_area_shape.wkb
 (OUT/'exact-raw-native-TMR-area-zone.chunk').write_bytes(chunk)
 put(OUT/'actual-native-area-exact-closed-shape-schema-and-raw-AST-binding.json',{'native_record':area,'host_record':ha,'raw_native_zone_chunk_SHA256':hashlib.sha256(chunk).hexdigest(),'exact_ordered_raw_native_integer_ring':rawring,'API_export_and_model_ordered_integer_ring_equal':True,'raw_native_layers':rawlayers,'raw_AST_API_and_model_same_UUID_layer_set_and_exact_closed_WKB':True,'actual_native_closed_AREA_WKB_SHA256':hashlib.sha256(area_shape.wkb).hexdigest(),'difference':'Host polygon carries an explicit empty holes-array; native plane_dump omits it. Exact three outer vertices, UUID, six-layer set and reconstructed closed shape are identical.','actual_added_corner_or_region':False,'first_R553_and_R555_FAILED_schema_assertions_preserved':True})"""
assert old in code;code=code.replace(old,new)
# Freeze graph results before later independent rule/AST checks, so a failed
# predicate is retained without requiring another unnecessary graph rebuild.
code=code.replace("print('R553 actual_native',net", "(OUT/('fresh-native-all-drilled-'+('IO3'if net=='/IO_3V3'else'FA')+'-groups.pkl')).write_bytes(pickle.dumps({net:xs},protocol=5));print('R557 actual_native',net")
code=code.replace("'inputs_SHA256':{str(x.resolve()):sha(x)for x in inputfiles}","'inputs_SHA256':{str(x.resolve()):sha(x)for x in inputfiles},'preserved_R553_failed_checker_SHA256':sha(H/'audit_TMR_R218_actual_native_drilled_source_r553.py'),'preserved_R555_failed_adapter_SHA256':sha(H/'audit_TMR_R218_actual_native_drilled_source_r555.py'),'raw_native_AREA_integer_AST_binding_file':str((OUT/'actual-native-area-exact-closed-shape-schema-and-raw-AST-binding.json').resolve())")
exec(compile(code,str(prior),'exec'))
