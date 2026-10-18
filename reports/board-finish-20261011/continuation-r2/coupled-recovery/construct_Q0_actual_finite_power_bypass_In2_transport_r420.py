"""Finite real power feed, retained B annulus carry and F/In2/F Q0 transport."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'construct_Q0_power_actual_left_source_bypass_FLT_dive_r418.py'
code=base.read_text().replace('Q0-power-left-source-bypass-FLT-dive-r418','Q0-finite-power-bypass-In2-transport-r420')
old="powerTarget=unary_union([r['shape']for r in powerRoot if r['layer']=='F.Cu'and r['kind']!='fill']);assert not powerTarget.is_empty"
new="powerTarget=unary_union([r['shape']for r in powerRoot if r['layer']=='F.Cu'and r['kind']!='fill']).difference(Point(228.45,158.35).buffer(.25,quad_segs=128));assert not powerTarget.is_empty"
assert old in code;code=code.replace(old,new)
# This replacement applies to the underlying R404 code after its composition.
code += """
"""
old="exec(compile(code,str(base),'exec'))"
new="""code=code.replace("qtransport=route_attachments('Q0-In3-common-transport',NET,'In3.Cu',qref['B.Cu']", "qtransport=route_attachments('Q0-In2-common-transport',NET,'In2.Cu',qref['F.Cu']")
code=code.replace("'Q0_In3':qtransport", "'Q0_In2':qtransport")
terminal_code=\"\"\"senseBterminal=[[228.96,160.2],[228.96,160.412]]
uid,ch=identity.serial_segment(SENSE,'B.Cu',*senseBterminal,.2);chunks[uid]=ch;tracks.append({'uuid':uid,'net':identity.raw(SENSE),'layer':'B.Cu','a':senseBterminal[0],'b':senseBterminal[1],'w':.2})
assert K.A.shape({'kind':'segment',**tracks[-1]}).difference(K.A.shape({'kind':'segment',**oldtrack['7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d']})).is_empty
put(out/'retained-SENSE-exact-old-B-terminal-natural-mask-obligation.json',{'original_UUID':'7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d','retained_native_subset_axis_mm':senseBterminal,'width_mm':.2,'old_barrel_UUID':oldSense['uuid'],'natural_required_old_F_B_plus_new_In3_annuli':True,'original_unused_layer_flags_unchanged':True,'actual_global_source_reference_contact_native_flash_gate':'OPEN'})
\"\"\"
code=code.replace("qref={l:refs[p]", terminal_code+"qref={l:refs[p]",1)
exec(compile(code,str(base),'exec'))"""
assert old in code;code=code.replace(old,new,1);exec(compile(code,str(base),'exec'))
