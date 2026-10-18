"""Source-proved wall feeds with independently screened separated Q0/FLT ports."""
from pathlib import Path
H=Path(__file__).resolve().parent;base=H/'construct_Q0_power_wall_SENSE_dive_coupled_r404.py'
code=base.read_text().replace('Q0-power-wall-SENSE-dive-coupled-r404','Q0-separated-ports-actual-source-coupled-r424')
old="exec(compile(prefix,str(base),'exec'))"
new="prefix=prefix.replace('[229.12,157.72]','[229.23,157.82]').replace('groupsfile=', \"newvias.append({'uuid':'FLT-source','net':FLT,'x':229.18,'y':158.636,'d':.5,'drill':.2,'flashed':list(K.LAYERS)})\\ngroupsfile=\",1)\nexec(compile(prefix,str(base),'exec'))"
assert old in code;code=code.replace(old,new,1)
code=code.replace("('SENSE-source','b88b7a49-a1ea-458a-9195-d0a46a3a7f66'),", "('SENSE-source','b88b7a49-a1ea-458a-9195-d0a46a3a7f66'),('FLT-source','retained-SENSE-return'),")
start=code.index("power_ok=route_attachments(");end=code.index("ground_ok=route_attachments(",start)
replacement="""powerWithout7bb={**current,'tracks':[t for t in current['tracks']if t['uuid']!='7bb3c794-cbe6-40a7-abfb-5a3ab7df28ff']}
_,powerGroups=K.physical(powerWithout7bb,POWER,K.hole_context(powerWithout7bb));powerRoot=K.root(powerGroups,'U11017','1');powerTarget=unary_union([r['shape']for r in powerRoot if r['layer']=='F.Cu'and r['kind']!='fill']).difference(Point(228.45,158.35).buffer(.25,quad_segs=128));assert not powerTarget.is_empty
power_ok=route_attachments('POWER-only-7bb-original-feed-node-to-real-source-rooted-retained-F-Cu',POWER,'F.Cu',refs['In1.Cu'],Point(228.45,158.35),powerTarget.buffer(-.02,quad_segs=128),tracks)
fltNew=next(v for v in newvias if v['uuid']=='FLT-source');fltIn4Own,fltIn4Ledger=support_FLT(K,current,{**h,'vias':h['vias']+newvias},trueRoot,iv,oldFLTvia,GND,FLT,'In4.Cu');fltIn4Ledger['used_signal_layer']='In3.Cu';put(out/'retained-FLT-In3-exact-native-own-support.json',fltIn4Ledger)
fltFown=newOwn(fltNew,'In1.Cu');fltIown=newOwn(fltNew,'In4.Cu');fltF=route_attachments('FLT-F-original-feed-to-new-ordinary-dive',FLT,'F.Cu',refs['In1.Cu'].union(fltFown),Point(229.35,158.45),Point(fltNew['x'],fltNew['y']),tracks,qualified_new_own=fltFown)
fltInner=route_attachments('FLT-In3-to-retained-original-all6-barrel',FLT,'In3.Cu',refs['In4.Cu'].union(fltIown).union(fltIn4Own),Point(fltNew['x'],fltNew['y']),Point(oldFLTvia['x'],oldFLTvia['y']),tracks,qualified_new_own=fltIown.union(fltIn4Own));flt_ok=fltF and fltInner
"""
code=code[:start]+replacement+code[end:]
terminal="""senseBterminal=[[228.96,160.2],[228.96,160.412]]
uid,ch=identity.serial_segment(SENSE,'B.Cu',*senseBterminal,.2);chunks[uid]=ch;tracks.append({'uuid':uid,'net':identity.raw(SENSE),'layer':'B.Cu','a':senseBterminal[0],'b':senseBterminal[1],'w':.2})
assert K.A.shape({'kind':'segment',**tracks[-1]}).difference(K.A.shape({'kind':'segment',**oldtrack['7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d']})).is_empty
put(out/'retained-SENSE-exact-old-B-terminal-natural-mask-obligation.json',{'original_UUID':'7b8f7e31-baac-4ff2-8b1f-3d210fb85e0d','retained_native_subset_axis_mm':senseBterminal,'width_mm':.2,'old_barrel_UUID':oldSense['uuid'],'natural_required_old_F_B_plus_new_In3_annuli':True,'original_unused_layer_flags_unchanged':True,'actual_global_source_reference_contact_native_flash_gate':'OPEN'})
"""
code=code.replace("qref={l:refs[p]",terminal+"qref={l:refs[p]",1)
# No zero-axis serialized segment is a route nomination.
code=code.replace("if not gap.is_empty:continue\n  for a,bb in zip(path,path[1:]):", "if not gap.is_empty or LineString(path).length<.001:continue\n  for a,bb in zip(path,path[1:]):")
exec(compile(code,str(base),'exec'))
