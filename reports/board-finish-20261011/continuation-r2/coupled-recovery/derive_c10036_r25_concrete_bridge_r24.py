"""Stage a concrete R25 repair; conflicting prospective R41 mesh stays OPEN."""
from pathlib import Path
HERE=Path(__file__).resolve().parent
s=(HERE/'construct_c10036_scoped_reference_bridge_r20.py').read_text().replace('c10036-scoped-reference-bridge-recipe-r20.json','c10036-r25-reference-bridge-recipe-r24.json').replace('c10036-reference-bridge-r20.wkb','c10036-reference-bridge-r24.wkb').replace('c10036-reference-bridge-r20.pkl','c10036-reference-bridge-r24.pkl')
s=s.replace("if q.get('layer')!='In4.Cu' or L.norm(q['net'])==GROUND:continue", "if q.get('layer')!='In4.Cu' or L.norm(q['net'])==GROUND or q['uuid']=='630264b1-3d8f-5604-aedd-209dc0a5eaa3':continue")
s=s.replace('/In4-source-ground-bridge/r20/','/In4-source-ground-bridge/r24/')
s=s.replace("'R41_mutual_inputs_sha256':pins", "'R41_mutual_inputs_sha256':pins,'R41_mutual_reference_verdict':'OPEN_FAIL_UNTIL_SEPARATE_SOURCE_FEED_MESH_CORRECTION','R41_conflicting_prospective_In4_mesh_UUID':'630264b1-3d8f-5604-aedd-209dc0a5eaa3','R41_mesh_not_integrated_or_qualified_by_R25_constructor':True,'other_R41_new_barrels_stubs_and_meshes_remain_hard':True")
t=HERE/'construct_c10036_r25_concrete_bridge_r24.py';assert not t.exists();t.write_text(s);print(t)
