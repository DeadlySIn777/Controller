"""R553 schema correction only: explicit empty native/host hole-container.

Preserves the first failed strict array assertion. Both reconstructed closed
AREA polygons must have identical WKB before actual no-zone predicates run.
No source, geometry, native rule, contact operator or tolerance changes.
"""
from pathlib import Path
import hashlib,json
H=Path(__file__).resolve().parent
prior=H/'audit_TMR_R218_actual_native_drilled_source_r553.py'
code=prior.read_text(encoding='utf-8')
code=code.replace("OUT=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r553'","OUT=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r555'")
old="assert area['outline']==ha['outline']and area['layers']==ha['layers'];area_shape=unary_union(L.poly(area['outline']))"
new="""assert area['layers']==ha['layers'] and area['uuid']==ha['uuid'];area_shape=unary_union(L.poly(area['outline']));host_area_shape=unary_union(L.poly(ha['outline']));assert area_shape.wkb==host_area_shape.wkb
 put(OUT/'actual-native-area-exact-closed-shape-schema-binding.json',{'native_record':area,'host_record':ha,'same_UUID_layers_and_exact_closed_WKB':True,'actual_native_closed_AREA_WKB_SHA256':hashlib.sha256(area_shape.wkb).hexdigest(),'difference':'Host each polygon carries an explicit empty holes-array; native plane_dump omits it. Outer integer vertices/layers/UUID and exact reconstructed closed shape are identical.','first_R553_FAILED_array_assertion_preserved':True})"""
assert old in code;code=code.replace(old,new)
code=code.replace("'inputs_SHA256':{str(x.resolve()):sha(x)for x in inputfiles}","'inputs_SHA256':{str(x.resolve()):sha(x)for x in inputfiles},'prior_R553_FAILED_schema_assertion_SHA256':sha(Path(__file__)), 'derived_R555_schema_adapter_SHA256':sha(H/'audit_TMR_R218_actual_native_drilled_source_r555.py')")
exec(compile(code,str(prior),'exec'))
