from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'b5_source_rooted_feeds_r3.py').read_text(encoding='utf-8')
def change(a,b):
 global s
 assert s.count(a)==1,(a,s.count(a));s=s.replace(a,b)
change("OUT=HERE/'b5-source-rooted-feeds-r3'","OUT=HERE/'b5-source-rooted-feeds-r4'")
change('controller-b5-source-feeds-r3/','controller-b5-source-feeds-r4/')
change('if distance>150:continue','if distance>240:continue')
change("if gi==ri and route and route.get('source_escape_initialization'):source[layer]=unary_union([source[layer],disk.difference(hole)])", "for source_layer in INNER:source[source_layer]=unary_union([source[source_layer],disk.difference(hole)])")
old="sameholes=unary_union([q['shape'] for q in drills if q['plated'] and q['net']==raw]+[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64) for v in vias]+[hole]);body=set_precision(unary_union([q for q in polys(line.buffer(.6,quad_segs=32).intersection(legal)) if q.intersection(core).area>1e-9]).difference(sameholes),1e-6)"
new="sameholes=unary_union([q['shape'] for q in drills if q['plated'] and q['net']==raw]+[Point(v['x'],v['y']).buffer(v['drill']/2,quad_segs=64) for v in vias]+[hole]);nativeoutline=set_precision(unary_union([q for q in polys(line.buffer(.6,quad_segs=32).intersection(legal)) if q.intersection(core).area>1e-9]),1e-6);body=set_precision(nativeoutline.difference(sameholes),1e-6)"
change(old,new)
change("'points_mm':points,'sheet_only_R35um60C_ohm'", "'points_mm':points,'native_outline_WKB_hex':nativeoutline.wkb_hex,'sheet_only_R35um60C_ohm'")
change("z={'uuid':zid,'net':raw,'layer':layer,'shape':body,'clearance_mm':.15}", "from shapely import from_wkb\n                                    z={'uuid':zid,'net':raw,'layer':layer,'shape':body,'zone_outline_shape':from_wkb(bytes.fromhex(route['native_outline_WKB_hex'])),'physical_Cu_drill_subtracted':True,'clearance_mm':.15}")
change("'same_raw_plated_source_annuli_preserved':True", "'same_raw_plated_source_annuli_preserved':True,'source_goals_include_all_four_screened_prospective_inner_annuli_of_each_rooted_plated_barrel':True,'additional_native_flash_on_every_used_barrel_plane_contact_required':True,'intended_native_outline_and_effective_drill_subtracted_Cu_separate':True")
out=HERE/'b5_source_rooted_feeds_r4.py';assert not out.exists();out.write_text(s,encoding='utf-8')
