"""R559 continuation: empty fill has no direct-contact obligation.

The raw failed NaN comparison is preserved. Every nonempty old fill contact
still has to meet actual native physical copper; an absent new fill is FAIL.
No finite distance, source key, native rule or geometry is waived.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
p=H/'complete_TMR_R218_actual_native_from_bound_R557_graphs_r559.py'
text=p.read_text(encoding='utf-8');end="exec(compile(code,str(H/'audit_TMR_R218_actual_native_drilled_source_r553.py'),'exec'))";assert end in text
ns={'__file__':str(p)};exec(compile(text.replace(end,''),str(p),'exec'),ns);code=ns['code']
code=code.replace("OUT=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r559'","OUT=H/'TMR-R218-native-selected-actual-all-drill-FA-IO3-source-contact-r561'")
code=code.replace("source=[];contact=[];direct=[];annular=[]","source=[];contact=[];direct=[];annular=[];empty_old_fill_layers=[]")
old="alloldfill=unary_union([x['shape']for xx in host[net]for x in xx if x['kind']=='fill'and x['layer']==ly])\n   for key,x in metal.items():"
new="""alloldfill=unary_union([x['shape']for xx in host[net]for x in xx if x['kind']=='fill'and x['layer']==ly])
   if alloldfill.is_empty:
    empty_old_fill_layers.append({'net':net,'layer':ly,'actual_BEFORE_fill_empty':True,'no_physical_BEFORE_fill_to_metal_touch_existed':True,'raw_nan_distance_does_not_invent_a_contact_obligation':True});continue
   actual_metal=collections.defaultdict(list)
   for yy in xs:
    for y in yy:
     if y['layer']==ly and y['kind']!='fill':actual_metal[(y['kind'],y['uuid'],ly)].append(y['shape'])
   for key,x in metal.items():"""
assert old in code;code=code.replace(old,new)
old="newmetal=[y for yy in xs for y in yy if(y['kind'],y['uuid'],y['layer'])==key];body=unary_union([y['shape']for y in newmetal]);gap=body.distance(finalfill.get(ly,Polygon()))if not body.is_empty else None"
new="newmetal=actual_metal.get(key,[]);body=unary_union(newmetal);newfill=finalfill.get(ly,Polygon());gap=body.distance(newfill)if not body.is_empty and not newfill.is_empty else None"
assert old in code;code=code.replace(old,new)
code=code.replace("'actual_gap_mm':gap,'same_2nm_host_contact_operator_not_native_DRC_tolerance':True", "'actual_gap_mm':gap,'actual_native_metal_empty':body.is_empty,'actual_native_same_net_layer_fill_empty':newfill.is_empty,'same_2nm_host_contact_operator_not_native_DRC_tolerance':True")
code=code.replace("'host_before_direct_native_fill_contact_count':len(direct)","'host_before_direct_native_fill_contact_count':len(direct),'exact_empty_BEFORE_fill_layers_no_touch_obligation':empty_old_fill_layers,'preserved_R559_FAILED_nan_serialization_checker_SHA256':sha(H/'complete_TMR_R218_actual_native_from_bound_R557_graphs_r559.py')")
exec(compile(code,str(H/'audit_TMR_R218_actual_native_drilled_source_r553.py'),'exec'))
