"""Preserve R12 and diagnose exact terminal/reference obstruction."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'construct_c10036_power_return_r12.py').read_text()
s=s.replace('c10036-power-paired-return-recipe-r12.json','c10036-power-paired-return-recipe-r13.json')
s=s.replace("legal=win.difference(unary_union(obstacles)).intersection(planes['In4.Cu']);options=", "physicallegal=win.difference(unary_union(obstacles));strictlegal=physicallegal.intersection(planes['In4.Cu']);legal=physicallegal;options=")
s=s.replace("'power_route_options':len(options)","'power_route_options':len(options),'endpoint_diagnostics':[{'at_mm':xy,'physical_point_contained':physicallegal.covers(Point(xy)),'physical_inward156_contained':physicallegal.buffer(-.156).covers(Point(xy)),'rooted_reference_point_distance_mm':Point(xy).distance(planes['In4.Cu']),'strict_inward156_contained':strictlegal.buffer(-.156).covers(Point(xy)),'nearby_vias':[w for w in g['vias'] if Point(xy).distance(Point(w['x'],w['y']))<1.2]} for xy in(old['a'],old['b'])]")
s=s.replace("if nomination and not returnbad:","if nomination and not returnbad and nomination['source_rooted_full_body_gap_mm2']<1e-9:")
s=s.replace("('verdict','B_power_route','return_clearance_errors','power_route_options','return_finite_annular_source_interior_mm2')","('verdict','B_power_route','return_clearance_errors','power_route_options','return_finite_annular_source_interior_mm2','endpoint_diagnostics')")
target=HERE/'construct_c10036_power_return_r13.py';assert not target.exists();target.write_text(s);print(target)
