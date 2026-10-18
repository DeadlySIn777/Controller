"""Finite ordinary .5/.2 DC FIELD5 landing follow-up; all guards retained.

This is a geometric nomination only for the unchanged .341131/.36 A case.
No barrel/current/temperature/native or loop claim follows from the size.
"""
from pathlib import Path
H=Path(__file__).resolve().parent
owner=H/'construct_FIELD5_joint_faces_strong_new_ordinary_r447.py'
ns={'__file__':str(owner),'__name__':'_load_strong_guarded_constructor_without_running'}
exec(compile(owner.read_text(encoding='utf-8').rsplit('\nexec(compile(s,',1)[0],str(owner),'exec'),ns)
s=ns['s'].replace('FIELD5-joint-In3-In2-strong-new-ordinary-IO3-oldrefs-hard-nomination-r447','FIELD5-joint-In3-In2-half-mm-ordinary-IO3-oldrefs-hard-nomination-r459')
for a,b in(
 ('radius=.3+G.gap','radius=.25+G.gap'),
 ('hard.append(N.bounded_buffer(qq[\'shape\'],.3+max','hard.append(N.bounded_buffer(qq[\'shape\'],.25+max'),
 ('hard.append(N.bounded_buffer(supported,.3+max','hard.append(N.bounded_buffer(supported,.25+max'),
 ('sh,.15+.275+.0001','sh,.1+.275+.0001'),
 ('max(.8251,.15+v[\'drill\']/2+.2751)','max(.8251,.1+v[\'drill\']/2+.2751)'),
 ('sh,.3251','sh,.2751'),
 ("'new_via_diameter_mm':.6,'drill_mm':.3","'new_via_diameter_mm':.5,'drill_mm':.2"),
 ("'d':.6,'drill':.3","'d':.5,'drill':.2"),
 ("'controller/FIELD5/R447/ordinary/'","'controller/FIELD5/R459/ordinary/'"),
 ("'controller/FIELD5/R447/'","'controller/FIELD5/R459/'"),
 ('for core in (.50,.35):','for core in (.35,):'),
 ):
 assert a in s,a;s=s.replace(a,b)
s=s.replace("'R437_no_existing_middle_preserved':True","'R437_no_existing_middle_preserved':True,'R447_no_point6_barrel_preserved':True,'half_mm_DC_ordinary_nominations_only_current_unchanged':True")
exec(compile(s,str(H/'construct_FIELD5_two_layer_existing_barrel_IO3_hard_r437.py'),'exec'))
