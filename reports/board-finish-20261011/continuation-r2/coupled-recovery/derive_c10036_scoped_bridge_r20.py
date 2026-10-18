"""Keep .5-mm GND bulk with a legal finite terminal taper; no gap waiver."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'construct_c10036_joint_reference_bridge_r18.py').read_text().replace('c10036-joint-reference-bridge-recipe-r18.json','c10036-scoped-reference-bridge-recipe-r20.json').replace('c10036-reference-bridge-r18.wkb','c10036-reference-bridge-r20.wkb').replace('c10036-reference-bridge-r18.pkl','c10036-reference-bridge-r20.pkl')
s=s.replace("glegal.buffer(-.256)","glegal.buffer(-.156)")
s=s.replace("bridge=set_precision(LineString(pts).buffer(.25,quad_segs=128),1e-6);assert glegal.covers(bridge);", "bridge=set_precision(LineString(pts).buffer(.25,quad_segs=128).intersection(glegal.buffer(-.000003)),1e-6);assert bridge.geom_type=='Polygon' and glegal.covers(bridge);assert bridge.covers(body);assert bridge.covers(LineString(pts).buffer(.155,quad_segs=128));")
s=s.replace("'core_width_mm':.5", "'bulk_width_mm':.5,'finite_continuous_core_width_mm':.31,'terminal_clip_only_to_exact_foreign_clearance_legal_area':True,'core_width_mm':.31")
s=s.replace("'added_source_ground_reference_bridge_width_mm':.5", "'added_source_ground_reference_bridge_bulk_width_mm':.5,'added_source_ground_reference_bridge_continuous_core_width_mm':.31")
s=s.replace('/In4-source-ground-bridge/r18/','/In4-source-ground-bridge/r20/')
t=HERE/'construct_c10036_scoped_reference_bridge_r20.py';assert not t.exists();t.write_text(s);print(t)
