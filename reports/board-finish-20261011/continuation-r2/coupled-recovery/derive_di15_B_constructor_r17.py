from pathlib import Path
HERE=Path(__file__).resolve().parent
src=HERE/'construct_di15_reference_escape_r15.py';dst=HERE/'construct_di15_reference_escape_r17.py';assert not dst.exists();t=src.read_text()
t=t.replace('import di15_current_base_r13 as BIND','import di15_reuse_base_r17 as BIND')
t=t.replace("out=HERE/'di15-reference-escape-nomination-r15.json'", "out=HERE/'di15-reference-B-escape-nomination-r17.json'")
t=t.replace("'In3.Cu'", "'B.Cu'")
needle="'source_pad_bounds_mm':sourcepad.bounds,"
insert="'all_current_DI15_tracks':[x for x in h['tracks'] if L.norm(x['net'])==NET],'all_current_DI15_vias':[x for x in h['vias'] if L.norm(x['net'])==NET],'selected_transport':'B.Cu','source_pad_bounds_mm':sourcepad.bounds,"
assert needle in t;t=t.replace(needle,insert)
needle="print('DI15_CONTINUOUS_EXACT_REFERENCE_PAIRS'"
insert="site_diagnosis={'source_attachments':sp,'target_attachments':dp,'source_F_components_with_via_area':[{'attachment':q['at_mm'],'legal_site_area_mm2':via[NET].intersection(unary_union([p for p in K.pieces(free[NET,'F.Cu']) if p.covers(Point(q['at_mm']))])).area} for q in sp],'target_F_components_with_via_area':[{'attachment':q['at_mm'],'legal_site_area_mm2':via[NET].intersection(unary_union([p for p in K.pieces(free[NET,'F.Cu']) if p.covers(Point(q['at_mm']))])).area} for q in dp],'B_source_reachable_component_count':len(ins),'B_total_reference_free_mm2':free[NET,'B.Cu'].area}\n print('DI15_CONTINUOUS_EXACT_REFERENCE_PAIRS'"
assert needle in t;t=t.replace(needle,insert)
t=t.replace("'pairs':pairs,", "'continuous_exact_component_diagnosis':site_diagnosis,'pairs':pairs,")
assert t!=src.read_text();dst.write_text(t);print(dst)
